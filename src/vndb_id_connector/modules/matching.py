"""Name based matching between VNDB and Bangumi.

A normalized name only counts when exactly one VN and exactly one Bangumi subject carry
it, so a title shared by several works never links any of them while the other names
of those works still can. Normalizers are tried in order and the first one that yields
a match for a VN is used.
"""


def build_index(names_by_id, normalize):
    index = {}
    for key, names in names_by_id.items():
        for name in names:
            normalized = normalize(name)
            if normalized:
                index.setdefault(normalized, set()).add(key)
    return index


class NameMatcher:
    def __init__(self, vndb_names, bangumi_names, normalizers):
        self.tiers = [
            (
                label,
                normalize,
                build_index(vndb_names, normalize),
                build_index(bangumi_names, normalize),
            )
            for label, normalize in normalizers
        ]

    def match(self, names):
        """Return (tier label, {bangumi id: [(normalized name, name)]})."""
        for label, normalize, vndb_index, bangumi_index in self.tiers:
            found = {}
            for name in names:
                key = normalize(name)
                if (
                    len(vndb_index.get(key, ())) == 1
                    and len(bangumi_index.get(key, ())) == 1
                ):
                    (bid,) = bangumi_index[key]
                    found.setdefault(bid, []).append((key, name))
            if found:
                return label, found
        return None, {}
