import re

from .utils import normalize_company, normalize_string, parse_infobox

# link kind -> pattern for the id inside a Bangumi infobox URL
LINK_PATTERNS = {
    "vndb": re.compile(r"vndb\.org/(v\d+)", re.I),
    "steam": re.compile(r"store\.steampowered\.com/app/(\d+)", re.I),
    "egs": re.compile(r"erogamescape[^\s|\]}]*?[?&]game=(\d+)", re.I),
    "dlsite": re.compile(r"dlsite\.com/[^\s|\]}]*?product_id/([A-Z]{2}\d+)", re.I),
    "getchu": re.compile(r"getchu\.com/soft\.phtml\?id=(\d+)", re.I),
    "novelgame": re.compile(r"novelgame\.jp/games/show/(\d+)", re.I),
    "freem": re.compile(r"freem\.ne\.jp/win/game/(\d+)", re.I),
}
YEAR_PATTERN = re.compile(r"\|\s*发行日期\s*=\s*[^|]*?((?:19|20)\d{2})")
DATE_YEAR = re.compile(r"((?:19|20)\d{2})-")
COMPANY_KEYS = (
    "开发",
    "游戏开发商",
    "开发商",
    "制作",
    "社团",
    "品牌",
    "ブランド",
    "サークル",
    "游戏制作",
    "制作公司",
    "发行",
    "发行商",
    "游戏发行商",
    "发售",
    "メーカー",
)
COMPANY_SEPARATORS = re.compile(r"[、,，/／&＆;；|×・]| x | and ")


class BangumiData:
    """Game subjects loaded from the Bangumi archive.

    names:     name, name_cn and 别名 of subjects available on PC (or without platform)
    links:     {kind: ids} parsed from the infobox (vndb, steam, egs, dlsite, ...)
    year:      release year: the earlier of subject.date and the first year in 发行日期
               (subject.date is empty for some subjects, and the infobox pattern stops
               at the "|" of multi-platform lists such as {[Win|2005-01-01]})
    genre:     游戏类型
    companies: normalized developer and publisher names
    """

    INCLUDED_PLATFORMS = ["pc", "win", "dos", "linux", "mac"]
    EXCLUDED_PLATFORMS = ["windowsphone"]

    def __init__(self, cur):
        self.cur = cur
        self.names = {}
        self.links = {}
        self.year = {}
        self.genre = {}
        self.companies = {}

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
            'SELECT id, name, name_cn, infobox, date FROM "public".subject WHERE type = 4'
        )
        for bid, name, name_cn, infobox, date in self.cur.fetchall():
            infobox = infobox or ""
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

            links = {}
            for kind, pattern in LINK_PATTERNS.items():
                values = set(pattern.findall(infobox))
                if kind == "dlsite":
                    values = {v.upper() for v in values}
                elif kind == "vndb":
                    values = {v.lower() for v in values}
                if values:
                    links[kind] = values
            self.links[bid] = links

            years = [
                int(match.group(1))
                for match in (DATE_YEAR.match(date or ""), YEAR_PATTERN.search(infobox))
                if match
            ]
            if years:
                self.year[bid] = min(years)
            self.genre[bid] = " ".join(parse_infobox(infobox, "游戏类型")).strip()
            companies = set()
            for key in COMPANY_KEYS:
                for value in parse_infobox(infobox, key):
                    for piece in COMPANY_SEPARATORS.split(value):
                        normalized = normalize_company(piece)
                        if len(normalized) >= 2:
                            companies.add(normalized)
            if companies:
                self.companies[bid] = companies
        return self
