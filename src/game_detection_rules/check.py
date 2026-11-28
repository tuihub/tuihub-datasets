"""Validate raw rule sources, the compiled schema, and portable conformance cases."""

import json
from pathlib import Path

from jsonschema import Draft202012Validator

if __package__:
    from .rules import DATA_DIR, build_rules, iter_json_files
    from .scanner import CASES_PATH, run_cases
else:
    from rules import DATA_DIR, build_rules, iter_json_files
    from scanner import CASES_PATH, run_cases

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = REPO_ROOT / "docs/schemas/game_detection_rules_schema.json"

MANIFEST_KINDS = {"gog-galaxy-info", "steam-acf"}
TITLE_KINDS = {"line", "json", "ini", "html-title"}
HINT_KINDS = {"uint-line"}
EXPECTED_ROOT_ENTRIES = {"base.json", "stores", "engines", "extensions"}


def unique(items, key):
    values = [item[key] for item in items]
    if len(values) != len(set(values)):
        raise ValueError(f"Duplicate {key} in {values}")


def validate_file(validator, path):
    rel = path.relative_to(REPO_ROOT)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        validator.validate(data)
    except Exception as exc:
        raise ValueError(f"{rel}: {exc}") from exc


def validate_source_tree(schema):
    entries = {p.name for p in DATA_DIR.iterdir() if not p.name.startswith(".")}
    if entries != EXPECTED_ROOT_ENTRIES:
        raise ValueError(
            f"Unexpected entries in {DATA_DIR.relative_to(REPO_ROOT)}: "
            f"{sorted(entries ^ EXPECTED_ROOT_ENTRIES)}"
        )

    props = schema["properties"]
    defs = schema["$defs"]
    base_validator = Draft202012Validator(
        {
            "type": "object",
            "properties": {
                "traversal": props["traversal"],
                "defaults": props["defaults"],
            },
            "required": ["traversal", "defaults"],
            "additionalProperties": False,
        }
    )
    store_validator = Draft202012Validator(
        {
            "type": "object",
            "properties": {
                "traversal": props["traversal"],
                "defaults": props["defaults"],
                "storeManifests": props["storeManifests"],
                "hints": props["hints"],
            },
            "minProperties": 1,
            "additionalProperties": False,
            "$defs": defs,
        }
    )
    engine_validator = Draft202012Validator({"$ref": "#/$defs/engine", "$defs": defs})
    extension_validator = Draft202012Validator(
        {
            "type": "object",
            "properties": {
                "traversal": props["traversal"],
                "defaults": props["defaults"],
                "hints": props["hints"],
            },
            "minProperties": 1,
            "additionalProperties": False,
            "$defs": defs,
        }
    )

    validate_file(base_validator, DATA_DIR / "base.json")
    for subdir, validator in (
        ("stores", store_validator),
        ("engines", engine_validator),
        ("extensions", extension_validator),
    ):
        directory = DATA_DIR / subdir
        stray = [
            p.name
            for p in directory.iterdir()
            if not p.name.startswith(".") and (not p.is_file() or p.suffix != ".json")
        ]
        if stray:
            raise ValueError(
                f"Unexpected non-JSON entries in {directory.relative_to(REPO_ROOT)}: "
                f"{sorted(stray)}"
            )
        for path in iter_json_files(directory):
            validate_file(validator, path)


def validate_rules(validator, rules, strict_kinds=False):
    validator.validate(rules)
    for key in ("engines", "storeManifests", "hints"):
        unique(rules[key], "id")
    for engine in rules["engines"]:
        unique(engine["layouts"], "id")
    if not strict_kinds:
        return
    for manifest in rules["storeManifests"]:
        if manifest["kind"] not in MANIFEST_KINDS:
            raise ValueError(f"Unsupported manifest kind: {manifest['kind']!r}")
    for engine in rules["engines"]:
        for layout in engine["layouts"]:
            for title in layout.get("titles", ()):
                if title["kind"] not in TITLE_KINDS:
                    raise ValueError(f"Unsupported title kind: {title['kind']!r}")
    for hint in rules["hints"]:
        if hint["kind"] not in HINT_KINDS:
            raise ValueError(f"Unsupported hint kind: {hint['kind']!r}")


def main():
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)

    validate_source_tree(schema)
    compiled = json.loads(
        json.dumps(build_rules(DATA_DIR), ensure_ascii=False, separators=(",", ":"))
    )
    validate_rules(validator, compiled, strict_kinds=True)

    cases = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    unique(cases, "name")
    for case in cases:
        if "rules" in case:
            validate_rules(validator, case["rules"])
    run_cases(compiled, cases)
    print(f"Schema valid; {len(cases)} conformance cases passed")


if __name__ == "__main__":
    main()
