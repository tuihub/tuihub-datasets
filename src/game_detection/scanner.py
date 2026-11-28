"""Reference interpreter for game_detection_rules. Uses only Python's standard library."""

import argparse
import html
import io
import json
import os
import re
import stat
import sys
from functools import lru_cache
from pathlib import Path, PurePosixPath

DATA = Path(__file__).resolve().parents[2] / "data/game_detection_rules"


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
                key=lambda x: x[0].encode("utf-16-be"),
            )
        return self.cached[directory]

    def paths(self, pattern, bindings=None):
        bindings = bindings or {}
        current = [("", True)]
        for part in pattern.rstrip("/").split("/"):
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
                    if part != expanded
                    else glob(part).fullmatch(name)
                )
            ]
        return [path for path, is_dir in current if is_dir == pattern.endswith("/")]

    def read(self, path, offset=0, length=-1):
        return self.fs.read_bytes(join(self.root, path), offset, length)


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
            current = ""
            parts = task["path"].replace("\\", "/").split("/")
            for i, part in enumerate(parts):
                match = next(
                    (
                        n
                        for n, d in view.listing(current)
                        if n.lower() == part.lower() and d == (i < len(parts) - 1)
                    ),
                    None,
                )
                if match is None:
                    break
                current = join(current, match)
            else:
                entries.append(current)
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


def detect(view, name, rules):
    store = next(
        (
            record
            for m in rules["storeManifests"]
            if m["kind"] == "gog-galaxy-info" and (record := gog(view, m))
        ),
        None,
    )
    engine = next(
        (
            g
            for e in rules["engines"]
            for layout in e["layouts"]
            if (g := engine_result(view, name, e, layout, rules["defaults"]))
        ),
        None,
    )
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
        if rule["kind"] != "uint-line" or rule["provider"] in hints:
            continue
        for path in (path for pattern in rule["paths"] for path in view.paths(pattern)):
            line = view.read(path).decode("utf-8-sig", errors="replace").splitlines()
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
    while pending:
        path = pending.pop()
        view = View(fs, path)
        try:
            children = view.listing("")
            result = detect(view, path.rsplit("/", 1)[-1] or name, rules)
            if result:
                games.append(dict(root=path or ".", **result))
            else:
                pending.extend(
                    join(path, n)
                    for n, d in reversed(children)
                    if d
                    and not any(
                        glob(p).fullmatch(n)
                        for p in rules["traversal"]["skipDirectories"]
                    )
                )
        except OSError:
            if not path:
                raise
            unreadable.append(path)
    return {"games": games, "unreadable": unreadable}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("directory", type=Path, nargs="?")
    p.add_argument("--rules", type=Path, default=DATA / "game_detection_rules.json")
    p.add_argument(
        "--check", action="store_true", help="run portable conformance cases"
    )
    args = p.parse_args()
    rules = json.loads(args.rules.read_text(encoding="utf-8"))
    if args.check:
        cases = json.loads(
            (DATA / "game_detection_cases.json").read_text(encoding="utf-8")
        )
        for case in cases:
            result = scan(
                Fixture(case["files"]), case["name"], case.get("rules", rules)
            )
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
