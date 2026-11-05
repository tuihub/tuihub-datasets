from .utils import normalize_string, parse_infobox


class BangumiData:
    """Game subjects loaded from the Bangumi archive.

    names: name, name_cn and 别名 of subjects available on PC (or without platform info)
    """

    INCLUDED_PLATFORMS = ["pc", "win", "dos", "linux", "mac"]
    EXCLUDED_PLATFORMS = ["windowsphone"]

    def __init__(self, cur):
        self.cur = cur
        self.names = {}

    @classmethod
    def platform_supported(cls, platforms):
        for platform in platforms:
            platform = normalize_string(platform)
            if any(ep in platform for ep in cls.EXCLUDED_PLATFORMS):
                continue
            if any(ip in platform for ip in cls.INCLUDED_PLATFORMS):
                return True
        return False

    def load(self):
        self.cur.execute(
            'SELECT id, name, name_cn, infobox FROM "public".subject WHERE type = 4'
        )
        for bid, name, name_cn, infobox in self.cur.fetchall():
            platforms = parse_infobox(infobox, "平台")
            if platforms and not self.platform_supported(platforms):
                continue
            names = []
            if name:
                names.append(name)
            if name_cn and name and name_cn != name:
                names.append(name_cn)
            for alias in parse_infobox(infobox, "别名"):
                if alias not in names:
                    names.append(alias)
            self.names[bid] = names
        return self
