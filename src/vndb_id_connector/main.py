import argparse
import json

import psycopg2

from modules.bangumi import BangumiData
from modules.matching import NameMatcher
from modules.output import build_entries
from modules.utils import normalize_string
from modules.vndb import VndbData

DESCRIPTION = (
    "THERE IS NO WARRANTY FOR THE DATA, TO THE EXTENT PERMITTED BY APPLICABLE LAW."
)


def parse_args():
    parser = argparse.ArgumentParser(description="Generate the VNDB ID connector data.")
    parser.add_argument(
        "output",
        nargs="?",
        default="../../data/vndb_id_connector/2_automated.json",
        help="where to write the generated dataset",
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


def main():
    args = parse_args()
    vndb = VndbData(connect("vndb", "10001").cursor()).load()
    bangumi = BangumiData(connect("bangumi", "10000").cursor()).load()
    matcher = NameMatcher(vndb.names, bangumi.names, [("exact", normalize_string)])

    bangumi_matches = {}
    for vid, names in vndb.names.items():
        _tier, found = matcher.match(names)
        if found:
            bangumi_matches[vid] = sorted(found)

    entries = build_entries(vndb, bangumi, bangumi_matches, vndb.steam)
    with open(args.output, "w", encoding="utf8") as f:
        json.dump(
            {"info": {"description": DESCRIPTION}, "entries": entries},
            f,
            ensure_ascii=False,
            indent=2,
        )
    print(
        f"entries: {len(entries)}, "
        f"vndb-bangumi pairs: {sum(len(v) for v in bangumi_matches.values())}, "
        f"vndb-steam pairs: {sum(len(v) for v in vndb.steam.values())}"
    )


if __name__ == "__main__":
    main()
