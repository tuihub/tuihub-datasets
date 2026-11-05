from .utils import sort_entries


def _names(vndb, bangumi, vid, bid=None):
    names = set(vndb.names_for_output(vid))
    if bid is not None:
        names.update(bangumi.names.get(bid, []))
    return names


def build_entries(vndb, bangumi, bangumi_matches, steam_matches, manual=None):
    """bangumi_matches / steam_matches: {vid: [ids]}.

    A VN with several Bangumi subjects and Steam apps (e.g. one per episode) is not
    expanded into every combination: a subject and an app share an entry only if the
    subject links that app (or the manual whitelist does), or if they are the VN's only
    subject and only app. Everything else gets an entry of its own. Associations
    forbidden by the manual blacklist are never put into one entry.
    """

    def forbidden(bid, app):
        return manual is not None and manual.pair_forbidden(
            "bangumi", bid, "steam", app
        )

    def linked_by_source(bid, app):
        if app in bangumi.links.get(bid, {}).get("steam", ()):
            return True
        return manual is not None and manual.pair_whitelisted(
            "bangumi", bid, "steam", app
        )

    entries = []
    for vid in set(bangumi_matches) | set(steam_matches):
        bangumi_ids = sorted(bangumi_matches.get(vid, ()))
        steam_ids = sorted(steam_matches.get(vid, ()), key=int)
        linked = [
            (bid, app)
            for bid in bangumi_ids
            for app in steam_ids
            if linked_by_source(bid, app) and not forbidden(bid, app)
        ]
        if (
            not linked
            and len(bangumi_ids) == 1
            and len(steam_ids) == 1
            and not forbidden(bangumi_ids[0], steam_ids[0])
        ):
            linked = [(bangumi_ids[0], steam_ids[0])]
        for bid, app in linked:
            entries.append(_entry(vndb, bangumi, manual, vid, bid, app))
        for bid in bangumi_ids:
            if all(bid != b for b, _app in linked):
                entries.append(_entry(vndb, bangumi, manual, vid, bid, ""))
        for app in steam_ids:
            if all(app != a for _b, a in linked):
                entries.append(_entry(vndb, bangumi, manual, vid, None, app))
    return sort_entries(entries)


def _entry(vndb, bangumi, manual, vid, bid, app):
    entry = {
        "steam": app,
        "bangumi": "" if bid is None else str(bid),
        "vndb": vid,
    }
    names = _names(vndb, bangumi, vid, bid)
    if manual is not None:
        names.update(manual.whitelist_names(entry))
    entry["names"] = sorted(names)
    return entry
