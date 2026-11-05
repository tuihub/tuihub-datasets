LANGUAGES = ("ja", "zh-Hans", "zh-Hant", "en", "uk")
PC_PLATFORMS = ("win", "dos", "lin", "mac")


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
    steam:          Steam app ids linked from the VN's releases
    """

    def __init__(self, cur):
        self.cur = cur
        self.release_vids = {}
        self.names = {}
        self.title_names = {}
        self.fallback_names = {}
        self.steam = {}

    def _query(self, sql, params=None):
        self.cur.execute(sql, params)
        return self.cur.fetchall()

    def is_bundle(self, rid):
        return len(self.release_vids.get(rid, ())) > 1

    def load(self):
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

        for vid, value in self._query(
            """SELECT DISTINCT rv.vid, e.value
               FROM releases_extlinks rl
               JOIN extlinks e ON e.id = rl.link
               JOIN releases_vn rv ON rv.id = rl.id
               WHERE e.site = 'steam' AND e.value IS NOT NULL"""
        ):
            _add_unique(self.steam, vid, value)
        return self

    def names_for_output(self, vid):
        return self.names.get(vid) or self.fallback_names.get(vid, [])
