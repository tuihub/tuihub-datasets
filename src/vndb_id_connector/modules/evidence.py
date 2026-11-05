"""Decide which VNDB <-> Bangumi pairs are published.

Evidence for a pair:
  S1    the Bangumi subject links to the VN on vndb.org
  S2    both sides link the same Steam app
  S3    both sides link the same ErogameScape / DLsite / Getchu / novelgame / freem page
  name  a name match from modules.matching ("exact" or "loose")
VNDB links only count when they come from the VN itself or from a release of this VN
only (see VndbData.links). A link kind present on both sides without a common value
contradicts the pair. Getchu and DLsite use one page per edition, so a mismatch there
only contradicts the pair when fewer than two other evidences agree.

A pair is accepted when nothing contradicts it and either
  - at least two evidences agree; without a name match the Bangumi subject must also
    not look like a fan disc / append that the VN's titles do not mention, or
  - an exact name match on a VN-level title, first release years at most one year
    apart, no disagreeing developer/publisher, and not a generic English title on a
    subject whose genre does not look like a visual novel.
Everything else is sent to the review queue together with the reason.
"""

import re

BRIDGE_SITES = ("egs", "dlsite", "getchu", "novelgame", "freem")
MULTI_EDITION_SITES = ("getchu", "dlsite")
VN_GENRE = re.compile(
    r"AVG|ADV|ノベル|视觉小说|視覺小說|文字|恋爱|恋愛|アドベンチャー|adventure|"
    r"visual\s*novel|\bVN\b|NVL|galgame|ギャルゲ|美少女",
    re.I,
)
FANDISC = re.compile(
    r"fan\s*disc|ファンディスク|\bFD\b|外伝|外传|番外|append|アペンド|追加|DLC|"
    r"after\s*story|アフター|特典|おまけ",
    re.I,
)
ACCEPTED_BY_NAME_TIER = {"exact": "id+exact", "loose": "id+loose", None: "id-only"}


def _compare(a, b):
    if a and b:
        return bool(a & b)
    return None


def companies_match(a, b):
    if not a or not b:
        return None
    return any(
        x == y or (min(len(x), len(y)) >= 4 and (x in y or y in x))
        for x in a
        for y in b
    )


class PairJudge:
    def __init__(self, vndb, bangumi, name_matches):
        """name_matches: {(vid, bid): (tier, [(normalized name, name)])}"""
        self.vndb = vndb
        self.bangumi = bangumi
        self.name_matches = name_matches

    def candidates(self):
        pairs = set(self.name_matches)
        for bid, links in self.bangumi.links.items():
            for vid in links.get("vndb", ()):
                if vid in self.vndb.vids:
                    pairs.add((vid, bid))
        by_link = {}
        for vid, links in self.vndb.links.items():
            for kind, values in links.items():
                for value in values:
                    by_link.setdefault((kind, value), set()).add(vid)
        for bid, links in self.bangumi.links.items():
            for kind, values in links.items():
                for value in values:
                    for vid in by_link.get((kind, value), ()):
                        pairs.add((vid, bid))
        return pairs

    def evidence(self, vid, bid):
        b_links = self.bangumi.links.get(bid, {})
        v_links = self.vndb.links.get(vid, {})
        tier, keys = self.name_matches.get((vid, bid), (None, []))
        declared = b_links.get("vndb", set()) & self.vndb.vids
        b_year, v_year = self.bangumi.year.get(bid), self.vndb.year.get(vid)
        genre = self.bangumi.genre.get(bid, "")
        vn_titles = self.vndb.title_names.get(vid, set())
        fandisc = FANDISC.search(" ".join(self.bangumi.names.get(bid, [])))
        return {
            "S1": (vid in declared) if declared else None,
            "S2": _compare(b_links.get("steam"), v_links.get("steam")),
            "sites": {
                site: result
                for site in BRIDGE_SITES
                if (result := _compare(b_links.get(site), v_links.get(site)))
                is not None
            },
            "name": tier,
            "via_title": any(name in vn_titles for _key, name in keys),
            "year": abs(b_year - v_year) <= 1 if b_year and v_year else None,
            "company": companies_match(
                self.vndb.companies.get(vid), self.bangumi.companies.get(bid)
            ),
            "generic_english": bool(keys)
            and all(key.isascii() for key, _name in keys)
            and not (genre and VN_GENRE.search(genre)),
            "fandisc": bool(fandisc)
            and not re.search(
                re.escape(fandisc.group(0)),
                " ".join(self.vndb.names_for_output(vid)),
                re.I,
            ),
        }

    @staticmethod
    def decide(ev):
        """Return (accepted, reason)."""
        sites = ev["sites"]
        positive = sum(
            [
                ev["S1"] is True,
                ev["S2"] is True,
                any(sites.values()),
                ev["name"] is not None,
            ]
        )
        hard_conflict = (
            ev["S1"] is False
            or ev["S2"] is False
            or any(v is False for k, v in sites.items() if k not in MULTI_EDITION_SITES)
        )
        soft_conflict = any(
            v is False for k, v in sites.items() if k in MULTI_EDITION_SITES
        )
        if hard_conflict or (soft_conflict and positive < 2):
            return False, "conflicting-evidence" if positive >= 2 else "contradicted"
        if positive >= 2:
            if ev["name"] is None and ev["fandisc"]:
                return False, "possible-fandisc"
            return True, ACCEPTED_BY_NAME_TIER[ev["name"]]
        if ev["name"] == "exact":
            if not ev["via_title"]:
                return False, "release-title-only"
            if ev["year"] is None:
                return False, "year-unknown"
            if ev["year"] is False:
                return False, "year-mismatch"
            if ev["company"] is False:
                return False, "company-mismatch"
            if ev["generic_english"]:
                return False, "generic-english"
            return True, "exact+year"
        if ev["name"] == "loose":
            return False, "loose-name-only"
        return False, "single-id"

    def judge(self):
        """Return {(vid, bid): (accepted, reason, evidence)} for every candidate."""
        decisions = {}
        for vid, bid in self.candidates():
            ev = self.evidence(vid, bid)
            accepted, reason = self.decide(ev)
            decisions[(vid, bid)] = (accepted, reason, ev)
        # a subject accepted for several VNs on name + year alone is suspicious
        accepted_vids = {}
        for (vid, bid), (accepted, _reason, _ev) in decisions.items():
            if accepted:
                accepted_vids.setdefault(bid, set()).add(vid)
        for (vid, bid), (accepted, reason, ev) in decisions.items():
            if accepted and reason == "exact+year" and len(accepted_vids[bid]) > 1:
                decisions[(vid, bid)] = (False, "bangumi-shared", ev)
        return decisions
