"""Manual corrections for the VNDB ID connector dataset.

1_manually.json:
{
  "whitelist": [{"vndb": "v1", "bangumi": "2", "steam": "", "names": ["..."], "note": "..."}],
  "blacklist": [{"vndb": "v1", "bangumi": "3", "note": "..."}]
}

- A whitelist entry states that all of its (at least two) IDs belong to the same work.
  It always ends up in the published dataset unless the blacklist forbids it.
- A blacklist entry with one ID removes that ID from every entry. With two or three IDs
  it forbids every pairwise association between them. The blacklist wins over the
  whitelist.
"""

import json
import re

ID_FIELDS = ("vndb", "bangumi", "steam")
ID_PATTERNS = {
    "vndb": re.compile(r"^v[1-9][0-9]*$"),
    "bangumi": re.compile(r"^[1-9][0-9]*$"),
    "steam": re.compile(r"^[1-9][0-9]*$"),
}
WHITELIST_FIELDS = set(ID_FIELDS) | {"names", "note"}
BLACKLIST_FIELDS = set(ID_FIELDS) | {"note"}


def entry_ids(entry):
    return {(field, entry[field]) for field in ID_FIELDS if entry.get(field)}


def _check_ids(item, where, errors):
    for field in ID_FIELDS:
        value = item.get(field, "")
        if not isinstance(value, str) or (
            value and not ID_PATTERNS[field].match(value)
        ):
            errors.append(f"{where}: invalid {field} id {value!r}")


class ManualLists:
    def __init__(self, whitelist, blacklist):
        self.whitelist = whitelist
        self.blacklist = blacklist
        self._banned_ids = set()
        self._banned_pairs = set()
        for rule in blacklist:
            ids = sorted(entry_ids(rule))
            if len(ids) == 1:
                self._banned_ids.add(ids[0])
            for i in range(len(ids)):
                for j in range(i + 1, len(ids)):
                    self._banned_pairs.add((ids[i], ids[j]))

    @classmethod
    def load(cls, path):
        with open(path, encoding="utf8") as f:
            data = json.load(f)
        errors = []
        if not isinstance(data, dict) or set(data) - {"whitelist", "blacklist"}:
            raise ValueError(
                f"{path}: expected an object with 'whitelist' and 'blacklist' only"
            )
        whitelist, blacklist = data.get("whitelist", []), data.get("blacklist", [])
        for i, item in enumerate(whitelist):
            where = f"whitelist[{i}]"
            if not isinstance(item, dict):
                errors.append(f"{where}: not an object")
                continue
            if set(item) - WHITELIST_FIELDS:
                errors.append(
                    f"{where}: unknown fields {sorted(set(item) - WHITELIST_FIELDS)}"
                )
            _check_ids(item, where, errors)
            if len(entry_ids(item)) < 2:
                errors.append(f"{where}: needs at least two ids")
            names = item.get("names")
            if (
                not isinstance(names, list)
                or not names
                or not all(isinstance(n, str) and n for n in names)
            ):
                errors.append(
                    f"{where}: 'names' must be a non-empty list of non-empty strings"
                )
        for i, item in enumerate(blacklist):
            where = f"blacklist[{i}]"
            if not isinstance(item, dict):
                errors.append(f"{where}: not an object")
                continue
            if set(item) - BLACKLIST_FIELDS:
                errors.append(
                    f"{where}: unknown fields {sorted(set(item) - BLACKLIST_FIELDS)}"
                )
            _check_ids(item, where, errors)
            if len(entry_ids(item)) < 1:
                errors.append(f"{where}: needs at least one id")
        if errors:
            raise ValueError(f"{path}: " + "; ".join(errors))
        whitelist = [
            {
                **{field: item.get(field, "") for field in ID_FIELDS},
                "names": list(item["names"]),
            }
            for item in whitelist
        ]
        blacklist = [
            {field: item.get(field, "") for field in ID_FIELDS} for item in blacklist
        ]
        return cls(whitelist, blacklist)

    def pair_forbidden(self, field_a, id_a, field_b, id_b):
        a, b = (field_a, str(id_a)), (field_b, str(id_b))
        if a in self._banned_ids or b in self._banned_ids:
            return True
        return (min(a, b), max(a, b)) in self._banned_pairs

    def entry_forbidden(self, entry):
        ids = sorted(entry_ids(entry))
        if any(i in self._banned_ids for i in ids):
            return True
        return any(
            (ids[i], ids[j]) in self._banned_pairs
            for i in range(len(ids))
            for j in range(i + 1, len(ids))
        )

    def apply(self, entries):
        """Merge the whitelist into entries, then drop everything the blacklist forbids."""
        entries = [dict(e, names=list(e["names"])) for e in entries]
        for item in self.whitelist:
            wanted = entry_ids(item)
            existing = next((e for e in entries if wanted <= entry_ids(e)), None)
            if existing is not None:
                existing["names"] += item["names"]
                continue
            merged = dict(item, names=list(item["names"]))
            kept = []
            for e in entries:
                if entry_ids(e) < wanted:
                    merged["names"] += e["names"]
                else:
                    kept.append(e)
            entries = kept + [merged]
        merged_by_ids = {}
        for e in entries:
            if self.entry_forbidden(e):
                continue
            key = (e["steam"], e["bangumi"], e["vndb"])
            merged_by_ids.setdefault(key, set()).update(e["names"])
        # same key order as the generated data
        result = [
            {"steam": steam, "bangumi": bid, "vndb": vid, "names": sorted(names)}
            for (steam, bid, vid), names in merged_by_ids.items()
        ]
        return sort_entries(result)


def _id_number(value):
    return int(value.lstrip("v")) if value else float("inf")


def sort_entries(entries):
    return sorted(
        entries,
        key=lambda e: tuple(_id_number(e[field]) for field in ID_FIELDS),
    )
