import argparse
import json
from collections import Counter

import psycopg2

from modules.bangumi import BangumiData
from modules.evidence import PairJudge
from modules.matching import NameMatcher
from modules.output import build_entries
from modules.utils import normalize_loose, normalize_string
from modules.vndb import VndbData

DESCRIPTION = (
    "THERE IS NO WARRANTY FOR THE DATA, TO THE EXTENT PERMITTED BY APPLICABLE LAW."
)
REVIEW_EVIDENCE_FIELDS = ("S1", "S2", "sites", "name", "year", "company")


def parse_args():
    parser = argparse.ArgumentParser(description="Generate the VNDB ID connector data.")
    parser.add_argument(
        "output",
        nargs="?",
        default="../../data/vndb_id_connector/2_automated.json",
        help="where to write the generated dataset",
    )
    parser.add_argument(
        "--review-queue",
        default="../../data/vndb_id_connector/review_queue.jsonl",
        help="where to write candidate pairs that were not accepted",
    )
    return parser.parse_args()


def connect(database, port):
    return psycopg2.connect(
        database=database,
        user=database,
        password=database,
        host="localhost",
        port=port,
    )


def write_review_queue(path, decisions, vndb, bangumi):
    rows = sorted(
        (reason, vid, bid, ev)
        for (vid, bid), (accepted, reason, ev) in decisions.items()
        if not accepted
    )
    with open(path, "w", encoding="utf8") as f:
        for reason, vid, bid, ev in rows:
            record = {
                "reason": reason,
                "vndb": vid,
                "bangumi": str(bid),
                "vndb_names": vndb.names_for_output(vid)[:3],
                "bangumi_names": bangumi.names.get(bid, [])[:3],
                "evidence": {k: ev[k] for k in REVIEW_EVIDENCE_FIELDS},
            }
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


def main():
    args = parse_args()
    vndb = VndbData(connect("vndb", "10001").cursor()).load()
    bangumi = BangumiData(connect("bangumi", "10000").cursor()).load()
    matcher = NameMatcher(
        vndb.names,
        bangumi.names,
        [("exact", normalize_string), ("loose", normalize_loose)],
    )

    name_matches = {}
    for vid, names in vndb.names.items():
        tier, found = matcher.match(names)
        for bid, keys in found.items():
            name_matches[(vid, bid)] = (tier, keys)
    decisions = PairJudge(vndb, bangumi, name_matches).judge()

    bangumi_matches = {}
    for (vid, bid), (accepted, _reason, _ev) in decisions.items():
        if accepted:
            bangumi_matches.setdefault(vid, []).append(bid)
    for bids in bangumi_matches.values():
        bids.sort()

    entries = build_entries(vndb, bangumi, bangumi_matches, vndb.steam)
    with open(args.output, "w", encoding="utf8") as f:
        json.dump(
            {"info": {"description": DESCRIPTION}, "entries": entries},
            f,
            ensure_ascii=False,
            indent=2,
        )
    write_review_queue(args.review_queue, decisions, vndb, bangumi)

    accepted = Counter(r for a, r, _ev in decisions.values() if a)
    rejected = Counter(r for a, r, _ev in decisions.values() if not a)
    print(f"entries: {len(entries)}")
    print(f"accepted vndb-bangumi pairs: {sum(accepted.values())} {dict(accepted)}")
    print(f"pairs sent to review: {sum(rejected.values())} {dict(rejected)}")
    print(f"vndb-steam pairs: {sum(len(v) for v in vndb.steam.values())}")


if __name__ == "__main__":
    main()
