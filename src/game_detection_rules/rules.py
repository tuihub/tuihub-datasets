"""Assemble game_detection_rules from its raw source directory."""

import argparse
import json
import sys
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[2] / "data/game_detection_rules"


def iter_json_files(directory):
    if not directory.is_dir():
        return []
    return sorted(
        (
            p
            for p in directory.iterdir()
            if p.is_file() and not p.name.startswith(".") and p.suffix == ".json"
        ),
        key=lambda p: p.name,
    )


def _read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _dedupe(items):
    return list(dict.fromkeys(items))


def build_rules(source_dir=DATA_DIR):
    source = Path(source_dir)
    base = _read_json(source / "base.json")
    skip_directories = list(base["traversal"]["skipDirectories"])
    ignore_entries = list(base["defaults"]["ignoreEntries"])
    generic_stems = list(base["defaults"]["genericStems"])
    store_manifests = []
    engines = []
    hints = []

    for path in iter_json_files(source / "stores"):
        store = _read_json(path)
        skip_directories.extend(store.get("traversal", {}).get("skipDirectories", ()))
        ignore_entries.extend(store.get("defaults", {}).get("ignoreEntries", ()))
        generic_stems.extend(store.get("defaults", {}).get("genericStems", ()))
        store_manifests.extend(store.get("storeManifests", ()))
        hints.extend(store.get("hints", ()))

    for path in iter_json_files(source / "engines"):
        engines.append(_read_json(path))

    for path in iter_json_files(source / "extensions"):
        ext = _read_json(path)
        skip_directories.extend(ext.get("traversal", {}).get("skipDirectories", ()))
        ignore_entries.extend(ext.get("defaults", {}).get("ignoreEntries", ()))
        generic_stems.extend(ext.get("defaults", {}).get("genericStems", ()))
        hints.extend(ext.get("hints", ()))

    return {
        "traversal": {"skipDirectories": _dedupe(skip_directories)},
        "defaults": {
            "ignoreEntries": _dedupe(ignore_entries),
            "genericStems": _dedupe(generic_stems),
        },
        "storeManifests": store_manifests,
        "engines": engines,
        "hints": hints,
    }


def load_rules(path=DATA_DIR):
    target = Path(path)
    return build_rules(target) if target.is_dir() else _read_json(target)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path, nargs="?")
    parser.add_argument("--source", type=Path, default=DATA_DIR)
    parser.add_argument("--compact", action="store_true")
    args = parser.parse_args()
    rules = build_rules(args.source)
    text = (
        json.dumps(rules, ensure_ascii=False, separators=(",", ":"))
        if args.compact
        else json.dumps(rules, ensure_ascii=False, indent=2) + "\n"
    )
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    else:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stdout.write(text)


if __name__ == "__main__":
    main()
