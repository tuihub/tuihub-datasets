import argparse
import json
import sys
from pathlib import Path


ID_FIELDS = ("vndb", "bangumi", "steam")


def as_id_list(value) -> list[str]:
    if value is None or value == "":
        return []
    if isinstance(value, list):
        return [str(item) for item in value if item is not None and item != ""]
    return [str(value)]


def load_entries(path: Path) -> list[dict]:
    with path.open("r", encoding="utf8") as f:
        data = json.load(f)
    return data["entries"]


def parse_ratio(value: str) -> float:
    if value.endswith("%"):
        ratio = float(value[:-1]) / 100
    else:
        ratio = float(value)

    if ratio < 0 or ratio > 1:
        raise argparse.ArgumentTypeError("ratio must be between 0 and 1, or a percentage")
    return ratio


def entry_ids(entry: dict, skip_steam: bool) -> tuple[str, ...]:
    ids = []
    for field in ID_FIELDS:
        if skip_steam and field == "steam":
            continue
        ids.extend(f"{field}:{value}" for value in as_id_list(entry.get(field)))
    return tuple(sorted(ids))


def collect_entry_identities(
    entries: list[dict], skip_steam: bool
) -> set[tuple[str, ...]]:
    identities = set()
    for entry in entries:
        ids = entry_ids(entry, skip_steam)
        if ids:
            identities.add(ids)
    return identities


def collect_ids(entries: list[dict], skip_steam: bool) -> set[str]:
    ids = set()
    for entry in entries:
        ids.update(entry_ids(entry, skip_steam))
    return ids


def collect_names_by_id(entries: list[dict], skip_steam: bool) -> dict[str, set[str]]:
    names_by_id = {}
    for entry in entries:
        names = {name for name in entry.get("names", []) if name}
        if not names:
            continue
        for id_value in entry_ids(entry, skip_steam):
            names_by_id.setdefault(id_value, set()).update(names)
    return names_by_id


def validate_new_entries(
    old_entries: list[dict], new_entries: list[dict], skip_steam: bool
) -> int:
    old_identities = collect_entry_identities(old_entries, skip_steam)
    new_identities = collect_entry_identities(new_entries, skip_steam)
    added_entries = new_identities - old_identities

    old_ids = collect_ids(old_entries, skip_steam)
    new_ids = collect_ids(new_entries, skip_steam)
    added_ids = new_ids - old_ids

    print(f"old entries: {len(old_entries)}")
    print(f"new entries: {len(new_entries)}")
    print(f"added comparable entries: {len(added_entries)}")
    print(f"added comparable ids: {len(added_ids)}")
    return len(added_entries)


def validate_alias_retention(
    old_entries: list[dict],
    new_entries: list[dict],
    skip_steam: bool,
    min_retention: float,
) -> float:
    old_names_by_id = collect_names_by_id(old_entries, skip_steam)
    new_names_by_id = collect_names_by_id(new_entries, skip_steam)

    checked_aliases = 0
    missing_aliases = []
    for id_value, old_names in old_names_by_id.items():
        new_names = new_names_by_id.get(id_value, set())
        checked_aliases += len(old_names)
        for missing_name in sorted(old_names - new_names):
            missing_aliases.append((id_value, missing_name))

    if checked_aliases == 0:
        raise ValueError("no comparable aliases were found")

    retention = (checked_aliases - len(missing_aliases)) / checked_aliases
    print(f"checked aliases: {checked_aliases}")
    print(f"missing aliases: {len(missing_aliases)}")
    print(f"alias retention: {retention:.4%}")

    if retention < min_retention:
        print("first missing aliases:")
        for id_value, missing_name in missing_aliases[:20]:
            print(f"  {id_value}: {missing_name}")
        raise ValueError(
            f"alias retention {retention:.4%} is below required {min_retention:.4%}"
        )

    return retention


def validate_steam_names(entries: list[dict]) -> None:
    missing_name_steam_ids = []
    for entry in entries:
        steam_ids = as_id_list(entry.get("steam"))
        if steam_ids and len(entry.get("names", [])) == 0:
            missing_name_steam_ids.extend(steam_ids)

    if missing_name_steam_ids:
        raise ValueError(
            "steam ids without names: " + ", ".join(missing_name_steam_ids[:20])
        )
    print("steam name check: passed")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate that a generated dataset update added entries without large alias loss."
    )
    parser.add_argument("old_json", type=Path)
    parser.add_argument("new_json", type=Path)
    parser.add_argument(
        "--min-alias-retention",
        type=parse_ratio,
        default=0.99,
        help="Minimum retained alias ratio for comparable non-skipped ids. Accepts ratios like 0.995 or percentages like 99.5%%. Defaults to 99%%.",
    )
    parser.add_argument(
        "--allow-no-new-entry",
        action="store_true",
        help="Do not fail when the generated file has no new comparable entries.",
    )
    parser.add_argument(
        "--skip-steam-name-check",
        action="store_true",
        help="Skip steam-only identity and steam name checks.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    old_entries = load_entries(args.old_json)
    new_entries = load_entries(args.new_json)

    added_entries = validate_new_entries(
        old_entries, new_entries, args.skip_steam_name_check
    )
    validate_alias_retention(
        old_entries,
        new_entries,
        args.skip_steam_name_check,
        args.min_alias_retention,
    )

    if args.skip_steam_name_check:
        print("steam name check: skipped")
    else:
        validate_steam_names(new_entries)

    if added_entries == 0 and not args.allow_no_new_entry:
        raise ValueError("no new comparable entries were added")

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as ex:
        print(f"validation failed: {ex}", file=sys.stderr)
        sys.exit(1)
