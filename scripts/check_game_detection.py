"""Check the authoring schema and the stable IDs used in scanner output."""

import json
from pathlib import Path
from jsonschema import Draft202012Validator

data = Path(__file__).resolve().parents[1] / "data/game_detection_rules"
schema = json.loads(
    (data / "game_detection_rules.schema.json").read_text(encoding="utf-8")
)
Draft202012Validator.check_schema(schema)
validator = Draft202012Validator(schema)


def unique(items, key):
    values = [item[key] for item in items]
    if len(values) != len(set(values)):
        raise ValueError(f"Duplicate {key} in {values}")


def validate(rules):
    validator.validate(rules)
    for key in ("engines", "storeManifests", "hints"):
        unique(rules[key], "id")
    for engine in rules["engines"]:
        unique(engine["layouts"], "id")


validate(json.loads((data / "game_detection_rules.json").read_text(encoding="utf-8")))
cases = json.loads((data / "game_detection_cases.json").read_text(encoding="utf-8"))
unique(cases, "name")
for case in cases:
    if "rules" in case:
        validate(case["rules"])
