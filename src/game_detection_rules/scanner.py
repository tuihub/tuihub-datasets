"""Reference interpreter for game_detection_rules using Python's standard library."""

import argparse
import html
import io
import json
import os
import posixpath
import re
import stat
import sys
from functools import lru_cache
from pathlib import Path, PurePosixPath

if __package__:
    from .rules import DATA_DIR, load_rules
else:
    from rules import DATA_DIR, load_rules

CASES_PATH = Path(__file__).resolve().parent / "cases.json"
_ACF_ESCAPES = {"n": "\n", "r": "\r", "t": "\t", "\\": "\\", '"': '"'}


class Disk:
    def __init__(self, root):
        self.root = root

    def list_dir(self, relative):
        with os.scandir(self.root / relative) as entries:
            return [
                (e.name, e.is_dir(follow_symlinks=False))
                for e in entries
                if not e.is_symlink()
                and not (
                    os.name == "nt"
                    and e.stat(follow_symlinks=False).st_file_attributes
                    & stat.FILE_ATTRIBUTE_REPARSE_POINT
                )
                and (
                    e.is_dir(follow_symlinks=False) or e.is_file(follow_symlinks=False)
                )
            ]

    def read_bytes(self, path, offset, length):
        with (self.root / path).open("rb") as stream:
            stream.seek(offset)
            return stream.read(length)


class Fixture:
    def __init__(self, files):
        self.files = {}
        self.directories = {"": {}}
        for path, value in files.items():
            parent = ""
            parts = path.split("/")
            for part in parts[:-1]:
                self.directories[parent][part] = True
                parent = join(parent, part)
                self.directories.setdefault(parent, {})
            self.directories[parent][parts[-1]] = False
            self.files[path] = (
                bytes.fromhex(value[4:]) if value.startswith("hex:") else value.encode()
            )

    def list_dir(self, relative):
        return self.directories[relative].items()

    def read_bytes(self, path, offset, length):
        return self.files[path][offset : None if length < 0 else offset + length]


def join(parent, child):
    return parent + "/" + child if parent and child else parent or child


@lru_cache(maxsize=512)
def glob(pattern):
    return re.compile(
        re.escape(pattern).replace(r"\*", ".*").replace(r"\?", "."),
        re.IGNORECASE | re.ASCII | re.DOTALL,
    )


class View:
    def __init__(self, fs, root):
        self.fs, self.root, self.cached = fs, root, {}

    def listing(self, directory):
        if directory not in self.cached:
            self.cached[directory] = sorted(
                self.fs.list_dir(join(self.root, directory)),
                key=lambda x: x[0].encode("utf-16-be", "surrogatepass"),
            )
        return self.cached[directory]

    def paths(self, pattern, bindings=None):
        bindings = bindings or {}
        current = [("", True)]
        for part in pattern.rstrip("/").split("/"):
            bound = any("{" + token + "}" in part for token in bindings)
            expanded = part
            for token, value in bindings.items():
                expanded = expanded.replace("{" + token + "}", value)
            current = [
                (join(parent, name), is_dir)
                for parent, directory in current
                if directory
                for name, is_dir in self.listing(parent)
                if (
                    name.lower() == expanded.lower()
                    if bound
                    else glob(part).fullmatch(name)
                )
            ]
        return [path for path, is_dir in current if is_dir == pattern.endswith("/")]

    def read(self, path, offset=0, length=-1):
        return self.fs.read_bytes(join(self.root, path), offset, length)


def resolve_subpath(view, rel_path, want_dir):
    parts = rel_path.replace("\\", "/").split("/")
    if any(not p or p in (".", "..") for p in parts):
        return None
    current = ""
    for i, part in enumerate(parts):
        need_dir = want_dir if i == len(parts) - 1 else True
        match = next(
            (
                n
                for n, d in view.listing(current)
                if n.lower() == part.lower() and d == need_dir
            ),
            None,
        )
        if match is None:
            return None
        current = join(current, match)
    return current


def first_probe(view, probe, bindings):
    if isinstance(probe, str):
        return next(iter(view.paths(probe, bindings)), None)
    if "any" in probe:
        return next(
            (
                hit
                for child in probe["any"]
                if (hit := first_probe(view, child, bindings))
            ),
            None,
        )
    magic = bytes.fromhex(probe.get("magic", ""))
    return next(
        (
            path
            for path in view.paths(probe["path"], bindings)
            if not magic or view.read(path, probe.get("offset", 0), len(magic)) == magic
        ),
        None,
    )


def pointer(data, path):
    if path and not path.startswith("/"):
        return None
    for part in path.split("/")[1:]:
        key = part.replace("~1", "/").replace("~0", "~")
        if (
            isinstance(data, list)
            and re.fullmatch("0|[1-9][0-9]*", key)
            and len(key) <= len(str(len(data)))
            and int(key) < len(data)
        ):
            data = data[int(key)]
        elif isinstance(data, dict) and key in data:
            data = data[key]
        else:
            return None
    return data if isinstance(data, str) else None


def title_value(view, path, rule):
    kind = rule["kind"]
    if kind not in ("json", "line", "ini", "html-title"):
        return None
    text = view.read(path, length=65536 if kind == "html-title" else -1).decode(
        "utf-8-sig", errors="replace"
    )
    if kind == "json":
        try:
            return pointer(json.loads(text), rule["pointer"])
        except ValueError:
            return None
    if kind == "html-title":
        match = re.search(r"<title\s*>([^<]*)</title\s*>", text, re.I)
        return html.unescape(match[1]) if match else None
    lines = io.StringIO(text, newline=None)
    if kind == "line":
        return next(
            (line for i, line in enumerate(lines, 1) if i == rule["line"]), None
        )
    section = ""
    for line in lines:
        line = line.strip()
        if line.startswith("[") and line.endswith("]"):
            section = line[1:-1]
        elif section.lower() == rule["section"].lower():
            key, sep, value = line.partition("=")
            if sep and key.strip().lower() == rule["key"].lower():
                return value
    return None


def engine_result(view, root_name, engine, layout, defaults):
    signals = [first_probe(view, probe, {}) for probe in layout.get("anchors", [])]
    if None in signals:
        return None
    ignored = defaults["ignoreEntries"] + engine.get("ignoreEntries", [])
    for entry in layout["entries"]:
        pattern = entry if isinstance(entry, str) else entry["path"]
        found, stems, evidence = [], [], list(signals)
        for path in view.paths(pattern.replace("{project}", "*")):
            name = PurePosixPath(path).name
            stem = name.rsplit(".", 1)[0] if "." in name else name
            if (
                isinstance(entry, dict)
                and entry.get("extension") == "none"
                and "." in name
            ):
                continue
            if any(glob(p).fullmatch(name) for p in ignored):
                continue
            bindings = {"stem": stem}
            if "{project}" in pattern.split("/"):
                bindings["project"] = path.split("/")[
                    pattern.split("/").index("{project}")
                ]
            companions = [
                first_probe(view, p, bindings) for p in layout.get("companions", [])
            ]
            if None not in companions:
                found.append(path)
                stems.append(stem)
                evidence.extend(companions)
        if not found:
            continue
        stem = stems[0] if len({s.lower() for s in stems}) == 1 else ""
        result = dict(
            engine=engine["name"],
            rule=engine["id"] + "/" + layout["id"],
            entries=found,
            signals=list(dict.fromkeys(evidence)),
        )
        for title in layout.get("titles", []):
            if title["kind"] not in ("json", "line", "ini", "html-title") or (
                "{stem}" in title["path"] and not stem
            ):
                continue
            for path in view.paths(title["path"], {"stem": stem}):
                value = (title_value(view, path, title) or "").strip()
                if value:
                    return dict(result, title=value, titleFile=path)
        for suffix in engine.get("stripStemSuffixes", []):
            if stem.lower().endswith(suffix.lower()):
                stem = stem[: -len(suffix)]
                break
        generic = defaults["genericStems"] + engine.get("genericStems", [])
        return dict(
            result,
            title=stem
            if stem and stem.lower() not in [x.lower() for x in generic]
            else root_name,
        )
    return None


def gog(view, manifest):
    games = []
    for path in view.paths(manifest["path"]):
        try:
            data = json.loads(view.read(path))
        except (ValueError, UnicodeError):
            continue
        if not isinstance(data, dict):
            continue
        game_id, name = data.get("gameId"), data.get("name")
        if (
            not isinstance(game_id, str)
            or not re.fullmatch("[0-9]+", game_id)
            or game_id != data.get("rootGameId")
        ):
            continue
        if (
            path.lower() != f"goggame-{game_id}.info"
            or not isinstance(name, str)
            or not name.strip()
        ):
            continue
        entries = []
        for task in (
            data.get("playTasks", []) if isinstance(data.get("playTasks"), list) else []
        ):
            if (
                not isinstance(task, dict)
                or task.get("isPrimary") is not True
                or (
                    not isinstance(task.get("type"), str)
                    or task["type"].lower() != "filetask"
                )
                or not isinstance(task.get("path"), str)
            ):
                continue
            resolved = resolve_subpath(view, task["path"], False)
            if resolved is not None:
                entries.append(resolved)
        if entries:
            games.append(
                dict(
                    store=manifest["store"],
                    external=game_id,
                    title=name,
                    titleFile=path,
                    entries=entries,
                    signals=[path],
                    engine=None,
                )
            )
    return games[0] if len(games) == 1 else None


def _acf_tokens(text):
    i, n = 0, len(text)
    while i < n:
        ch = text[i]
        if ch.isspace():
            i += 1
        elif ch == "/" and i + 1 < n and text[i + 1] == "/":
            end = text.find("\n", i + 2)
            i = n if end < 0 else end + 1
        elif ch in "{}":
            yield ch
            i += 1
        elif ch == '"':
            i += 1
            buf = []
            while i < n and text[i] != '"':
                if text[i] == "\\":
                    i += 1
                    if i >= n:
                        raise ValueError("unterminated escape")
                    buf.append(_ACF_ESCAPES.get(text[i], text[i]))
                else:
                    buf.append(text[i])
                i += 1
            if i >= n:
                raise ValueError("unterminated quote")
            yield "".join(buf)
            i += 1
        else:
            start = i
            while i < n and not text[i].isspace() and text[i] not in '{}"':
                i += 1
            yield text[start:i]


def parse_acf(raw):
    try:
        tokens = iter(_acf_tokens(raw.decode("utf-8-sig")))
        root_key = next(tokens, None)
        if (
            not isinstance(root_key, str)
            or root_key.lower() != "appstate"
            or next(tokens, None) != "{"
        ):
            return None
        fields = {}
        while True:
            key = next(tokens, None)
            if key is None or key == "{":
                return None
            if key == "}":
                return fields
            val = next(tokens, None)
            if val is None or val == "}":
                return None
            if val == "{":
                depth = 1
                while depth > 0:
                    tok = next(tokens, None)
                    if tok is None:
                        return None
                    depth += (tok == "{") - (tok == "}")
            else:
                fields[key.lower()] = val
    except (UnicodeError, ValueError):
        return None


def steam_acf_catalog(view, base_path, manifest):
    matched = view.paths(manifest["path"])
    if not matched:
        return {}, set(), set()
    skip_patterns = manifest.get("skipDirectories", ())
    skip_dirs = {
        join(base_path, name)
        for name, is_dir in view.listing("")
        if is_dir and any(glob(p).fullmatch(name) for p in skip_patterns)
    }
    records, ambiguous, ignored_targets = {}, set(), set()
    ignore_ids = set(manifest.get("ignore", ()))
    for acf_path in matched:
        fields = parse_acf(view.read(acf_path))
        if not fields:
            continue
        app_id = fields.get("appid", "")
        name = fields.get("name", "").strip()
        installdir = fields.get("installdir", "")
        if (
            not re.fullmatch("[1-9][0-9]*", app_id)
            or len(app_id) > 10
            or int(app_id) > 4294967295
            or PurePosixPath(acf_path).name.lower() != f"appmanifest_{app_id}.acf"
            or not installdir
            or "/" in installdir
            or "\\" in installdir
            or installdir in (".", "..")
        ):
            continue
        sub_dir = resolve_subpath(view, manifest["appsDir"] + "/" + installdir, True)
        if sub_dir is None:
            continue
        target = join(base_path, sub_dir)
        if app_id in ignore_ids:
            ignored_targets.add(target)
            continue
        if not name:
            continue
        if target in records:
            ambiguous.add(target)
        else:
            records[target] = {
                "manifest": manifest,
                "external": app_id,
                "title": name,
                "acf_path": join(base_path, acf_path),
            }
    for target in ambiguous:
        records.pop(target, None)
    return records, skip_dirs, ignored_targets - set(records) - ambiguous


def fallback_entries(view, entries_spec, ignored, skip_dirs):
    for entry in entries_spec:
        pattern = entry if isinstance(entry, str) else entry["path"]
        found = []
        for candidate in view.paths(pattern):
            parts = candidate.split("/")
            name = parts[-1]
            if (
                isinstance(entry, dict)
                and entry.get("extension") == "none"
                and "." in name
            ):
                continue
            if any(glob(s).fullmatch(seg) for seg in parts[:-1] for s in skip_dirs):
                continue
            if any(glob(p).fullmatch(name) for p in ignored):
                continue
            found.append(candidate)
        if found:
            return found
    return []


def steam_acf_result(view, path, info, engine, rules):
    manifest = info["manifest"]
    entries = (
        engine["entries"]
        if engine
        else fallback_entries(
            view,
            manifest["entries"],
            rules["defaults"]["ignoreEntries"] + manifest.get("ignoreEntries", []),
            rules["traversal"]["skipDirectories"],
        )
    )
    if not entries:
        return None
    rel_acf = posixpath.relpath(info["acf_path"], path or ".")
    return dict(
        store=manifest["store"],
        external=info["external"],
        title=info["title"],
        titleFile=rel_acf,
        entries=entries,
        signals=[rel_acf],
        engine=None,
    )


def detect(view, path, name, rules, catalog):
    engine = next(
        (
            g
            for e in rules["engines"]
            for layout in e["layouts"]
            if (g := engine_result(view, name, e, layout, rules["defaults"]))
        ),
        None,
    )
    by_manifest = catalog.get(path, {})
    store = None
    for m in rules["storeManifests"]:
        if m["kind"] == "gog-galaxy-info":
            store = gog(view, m)
        elif m["kind"] == "steam-acf" and m["id"] in by_manifest:
            store = steam_acf_result(view, path, by_manifest[m["id"]], engine, rules)
        if store:
            break
    if not (store or engine):
        return None
    result = store or engine
    if store and engine:
        result.update(
            rule=engine["rule"],
            engine=engine["engine"],
            signals=list(dict.fromkeys(store["signals"] + engine["signals"])),
        )
    hints = {}
    for rule in rules["hints"]:
        if (
            rule["kind"] != "uint-line"
            or rule["provider"] in hints
            or rule["provider"] == result.get("store")
        ):
            continue
        for hit in (hit for pattern in rule["paths"] for hit in view.paths(pattern)):
            line = view.read(hit).decode("utf-8-sig", errors="replace").splitlines()
            if line and re.fullmatch("[0-9]+", line[0]):
                value = line[0].lstrip("0")
                if (
                    value
                    and len(value) <= 10
                    and int(value) <= 4294967295
                    and value not in rule.get("ignore", [])
                ):
                    hints[rule["provider"]] = value
                    break
    if hints:
        result["hints"] = hints
    return result


def scan(fs, name, rules):
    pending, games, unreadable = [""], [], []
    catalog, skip_paths = {}, set()
    skip_dirs = rules["traversal"]["skipDirectories"]
    while pending:
        path = pending.pop()
        view = View(fs, path)
        try:
            children = view.listing("")
            result = detect(view, path, path.rsplit("/", 1)[-1] or name, rules, catalog)
            if result:
                games.append(dict(root=path or ".", **result))
            else:
                for m in rules["storeManifests"]:
                    if m["kind"] == "steam-acf":
                        records, m_skips, m_ignored = steam_acf_catalog(view, path, m)
                        skip_paths |= m_skips | m_ignored
                        for target, rec in records.items():
                            catalog.setdefault(target, {})[m["id"]] = rec
                for n, d in reversed(children):
                    child = join(path, n)
                    if (
                        d
                        and not any(glob(p).fullmatch(n) for p in skip_dirs)
                        and (child not in skip_paths or child in catalog)
                    ):
                        pending.append(child)
        except OSError:
            if not path:
                raise
            unreadable.append(path)
    return {"games": games, "unreadable": unreadable}


def run_cases(rules, cases):
    for case in cases:
        result = scan(Fixture(case["files"]), case["name"], case.get("rules", rules))
        expected = case["games"]
        if (
            result["unreadable"]
            or len(expected) != len(result["games"])
            or any(
                {k: v for k, v in g.items() if k != "signals" or k in e} != e
                for e, g in zip(expected, result["games"])
            )
        ):
            raise ValueError(f"{case['name']}: expected {expected}, got {result}")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("directory", type=Path, nargs="?")
    p.add_argument(
        "--rules",
        type=Path,
        default=DATA_DIR,
        help="source directory or compiled JSON file",
    )
    p.add_argument(
        "--check", action="store_true", help="run portable conformance cases"
    )
    args = p.parse_args()
    rules = load_rules(args.rules)
    if args.check:
        cases = json.loads(CASES_PATH.read_text(encoding="utf-8"))
        run_cases(rules, cases)
        print(f"{len(cases)} conformance cases passed")
    elif args.directory:
        root = args.directory.resolve(strict=True)
        sys.stdout.reconfigure(encoding="utf-8")
        print(
            json.dumps(scan(Disk(root), root.name, rules), indent=2, ensure_ascii=False)
        )
    else:
        p.error("provide a directory or --check")


if __name__ == "__main__":
    main()
