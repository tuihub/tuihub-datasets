from .utils import sort_entries


def _names(vndb, bangumi, vid, bid=None):
    names = set(vndb.names_for_output(vid))
    if bid is not None:
        names.update(bangumi.names.get(bid, []))
    return sorted(names)


def build_entries(vndb, bangumi, bangumi_matches, steam_matches):
    """bangumi_matches / steam_matches: {vid: [ids]}."""
    entries = []
    for vid in set(bangumi_matches) | set(steam_matches):
        bangumi_ids = bangumi_matches.get(vid) or [None]
        for steam_id in steam_matches.get(vid) or [""]:
            for bid in bangumi_ids:
                entries.append(
                    {
                        "steam": str(steam_id),
                        "bangumi": "" if bid is None else str(bid),
                        "vndb": vid,
                        "names": _names(vndb, bangumi, vid, bid),
                    }
                )
    return sort_entries(entries)
