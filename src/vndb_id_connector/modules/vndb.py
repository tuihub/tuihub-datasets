from .utils import normalize_company

LANGUAGES = ("ja", "zh-Hans", "zh-Hant", "en", "uk")
PC_PLATFORMS = ("win", "dos", "lin", "mac")
# VNDB extlink site -> link kind shared with modules.bangumi
LINK_SITES = {
    "steam": "steam",
    "egs": "egs",
    "dlsite": "dlsite",
    "dlsiteen": "dlsite",
    "getchu": "getchu",
    "novelgam": "novelgame",
    "freem": "freem",
}


def _add_unique(target, key, value):
    values = target.setdefault(key, [])
    if value not in values:
        values.append(value)


class VndbData:
    """Visual novels loaded from the VNDB dump.

    names:          titles used for matching: VN titles plus titles of PC releases that
                    belong to this VN only, both restricted to LANGUAGES
    title_names:    the VN-level part of names
    fallback_names: VN titles in any language, for VNs without names
    links:          {kind: ids} from the VN itself and from releases of this VN only
    bundle_links:   {kind: ids} from releases shared with other VNs
    steam:          every Steam app id linked from the VN or its releases
    year:           year of the first release
    companies:      normalized developer and publisher names
    """

    def __init__(self, cur):
        self.cur = cur
        self.vids = set()
        self.release_vids = {}
        self.names = {}
        self.title_names = {}
        self.fallback_names = {}
        self.links = {}
        self.bundle_links = {}
        self.steam = {}
        self.year = {}
        self.companies = {}

    def _query(self, sql, params=None):
        self.cur.execute(sql, params)
        return self.cur.fetchall()

    def is_bundle(self, rid):
        return len(self.release_vids.get(rid, ())) > 1

    def load(self):
        self.vids = {vid for (vid,) in self._query("SELECT id FROM vn")}
        for rid, vid in self._query("SELECT id, vid FROM releases_vn"):
            self.release_vids.setdefault(rid, set()).add(vid)

        for vid, title, latin in self._query(
            "SELECT id, title, latin FROM vn_titles WHERE lang IN %s", (LANGUAGES,)
        ):
            for name in (title, latin):
                if name:
                    self.title_names.setdefault(vid, set()).add(name)
                    _add_unique(self.names, vid, name)

        for vid, title, latin, rid in self._query(
            """SELECT DISTINCT rv.vid, rt.title, rt.latin, rv.id
               FROM releases_vn rv
               JOIN releases_titles rt ON rt.id = rv.id
               WHERE rt.lang IN %s AND EXISTS (
                   SELECT 1 FROM releases_platforms rp
                   WHERE rp.id = rv.id AND rp.platform IN %s)""",
            (LANGUAGES, PC_PLATFORMS),
        ):
            if self.is_bundle(rid):
                continue
            for name in (title, latin):
                if name:
                    _add_unique(self.names, vid, name)

        for vid, title, latin in self._query("SELECT id, title, latin FROM vn_titles"):
            for name in (title, latin):
                if name:
                    _add_unique(self.fallback_names, vid, name)

        sites = tuple(LINK_SITES)
        for vid, site, value, rid in self._query(
            """SELECT vl.id, e.site::text, e.value, NULL
               FROM vn_extlinks vl JOIN extlinks e ON e.id = vl.link
               WHERE e.site::text IN %s AND e.value IS NOT NULL
               UNION ALL
               SELECT rv.vid, e.site::text, e.value, rl.id
               FROM releases_extlinks rl
               JOIN extlinks e ON e.id = rl.link
               JOIN releases_vn rv ON rv.id = rl.id
               WHERE e.site::text IN %s AND e.value IS NOT NULL""",
            (sites, sites),
        ):
            kind = LINK_SITES[site]
            value = value.strip()
            if kind == "dlsite":
                value = value.upper()
            target = self.bundle_links if rid and self.is_bundle(rid) else self.links
            target.setdefault(vid, {}).setdefault(kind, set()).add(value)
            if kind == "steam":
                _add_unique(self.steam, vid, value)

        for vid, released in self._query(
            """SELECT rv.vid, min(r.released)
               FROM releases r JOIN releases_vn rv ON rv.id = r.id
               WHERE r.released > 19000000 AND r.released < 99990000
               GROUP BY rv.vid"""
        ):
            self.year[vid] = released // 10000

        for vid, name, latin, alias in self._query(
            """SELECT DISTINCT rv.vid, p.name, p.latin, p.alias
               FROM releases_vn rv
               JOIN releases_producers rp ON rp.id = rv.id
               JOIN producers p ON p.id = rp.pid
               WHERE rp.developer OR rp.publisher"""
        ):
            for company in [name, latin] + (alias or "").split("\n"):
                normalized = normalize_company(company or "")
                if len(normalized) >= 2:
                    self.companies.setdefault(vid, set()).add(normalized)
        return self

    def names_for_output(self, vid):
        return self.names.get(vid) or self.fallback_names.get(vid, [])
