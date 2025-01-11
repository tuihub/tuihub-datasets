import json
import sys

from module.SteamService import SteamService
from module.bangumi import get_bangumi_id_names
from module.vndb import get_vndb_steam_relation


def process_data(steam_id_names: dict[int, list[str]], vid_steam_ids: dict[str, list[int]],
                 steam_id_vid: dict[int, str], bid_names: dict[int, list[str]]) -> list:
    result = []

    vndb_steam_matches = []
    vid_vndb_steam_matches_id_idxes = {}
    proceeded_steam_ids = set()
    # process vndb groupings
    for vid, steam_ids in vid_steam_ids.items():
        group_steam_ids = []
        group_names = set()
        for steam_id in steam_ids:
            if steam_id in steam_id_names:
                group_steam_ids.append(steam_id)
                group_names.update(steam_id_names[steam_id])

        proceeded_steam_ids.update(group_steam_ids)
        vndb_steam_matches.append(
            {
                "steam": group_steam_ids,
                "bangumi": [],
                "vndb": [vid],
                "names": group_names
            }
        )
        vid_vndb_steam_matches_id_idxes[vid] = len(vndb_steam_matches) - 1

    # set steam name to id mapping
    steam_name_id = {}
    dup_steam_names = set()
    for steam_id, names in steam_id_names.items():
        for name in names:
            if name in steam_name_id:
                dup_steam_names.add(name)
            steam_name_id[name] = steam_id
    # remove duplicate steam names
    for name in dup_steam_names:
        steam_name_id.pop(name)

    proceeded_bangumi_ids = set()
    bangumi_steam_matches = []
    # process bangumi to steam name matching
    for bid, bnames in bid_names.items():
        matched_steam_ids = set()
        for bname in bnames:
            if bname in steam_name_id:
                matched_steam_ids.add(steam_name_id[bname])
        if len(matched_steam_ids) == 0:
            continue
        # process matched steam ids
        if len(matched_steam_ids) > 1:
            failed_match = False
            matched_vids = set()
            for matched_steam_id in matched_steam_ids:
                if matched_steam_id not in steam_id_vid:
                    failed_match = True
                    break
                vid = steam_id_vid[matched_steam_id]
                matched_vids.add(vid)
                if len(matched_vids) > 1:
                    failed_match = True
                    break
            if failed_match:
                continue
            else:
                vid = list(matched_vids)[0]
                if bid not in vndb_steam_matches[vid_vndb_steam_matches_id_idxes[vid]]["bangumi"]:
                    vndb_steam_matches[vid_vndb_steam_matches_id_idxes[vid]]["bangumi"].append(bid)
                    vndb_steam_matches[vid_vndb_steam_matches_id_idxes[vid]]["names"].update(bnames)
                proceeded_bangumi_ids.add(bid)
        elif len(matched_steam_ids) == 1:
            matched_steam_id = list(matched_steam_ids)[0]
            # matched steam id is in vndb groupings
            if matched_steam_id in steam_id_vid:
                vid = steam_id_vid[matched_steam_id]
                if bid not in vndb_steam_matches[vid_vndb_steam_matches_id_idxes[vid]]["bangumi"]:
                    vndb_steam_matches[vid_vndb_steam_matches_id_idxes[vid]]["bangumi"].append(bid)
                    vndb_steam_matches[vid_vndb_steam_matches_id_idxes[vid]]["names"].update(bnames)
            # else add to steam_bangumi_matches
            else:
                names = set()
                names.update(bnames)
                names.update(steam_id_names[matched_steam_id])
                bangumi_steam_matches.append(
                    {
                        "steam": [matched_steam_id],
                        "bangumi": [bid],
                        "vndb": [],
                        "names": names
                    }
                )
                proceeded_steam_ids.add(matched_steam_id)
            proceeded_bangumi_ids.add(bid)

    # add vndb_steam_matches
    for match in vndb_steam_matches:
        result.append({
            "steam": sorted(match["steam"]),
            "bangumi": sorted(match["bangumi"]),
            "vndb": sorted(match["vndb"], key=lambda x: int(x[1:])),
            "names": sorted(list(match["names"]))
        })
    # add bangumi_steam_matches
    for match in bangumi_steam_matches:
        result.append({
            "steam": sorted(match["steam"]),
            "bangumi": sorted(match["bangumi"]),
            "vndb": [],
            "names": sorted(list(match["names"]))
        })
    # add unmatched steam ids
    for steam_id, names in steam_id_names.items():
        if steam_id not in proceeded_steam_ids:
            result.append({
                "steam": [steam_id],
                "bangumi": [],
                "vndb": [],
                "names": sorted(names)
            })
    # add unmatched bangumi ids
    for bid, bnames in bid_names.items():
        if bid not in proceeded_bangumi_ids:
            result.append({
                "steam": [],
                "bangumi": [bid],
                "vndb": [],
                "names": sorted(bnames)
            })

    # sort result
    result = sorted(
        result,
        key=lambda x: (
            int(x["vndb"][0][1:]) if len(x["vndb"]) > 0 else float("inf"),
            int(x["bangumi"][0]) if len(x["bangumi"]) > 0 else float("inf"),
            int(x["steam"][0]) if len(x["steam"]) > 0 else float("inf"),
        ),
    )

    return result


if __name__ == "__main__":
    steam_id_names: dict[int, list[str]]
    steam_service = SteamService()
    steam_id_names = steam_service.get_app_list()

    vid_steam_ids: dict[str, list[int]]
    steam_id_vid: dict[int, str]
    vid_steam_ids, steam_id_vid = get_vndb_steam_relation()

    bid_names: dict[int, list[str]]
    bid_names = get_bangumi_id_names()

    result = process_data(steam_id_names, vid_steam_ids, steam_id_vid, bid_names)

    json_result = {
        "info": {
            "description": "THERE IS NO WARRANTY FOR THE DATA, TO THE EXTENT PERMITTED BY APPLICABLE LAW.",
        },
        "entries": result
    }
    saved_file_path = (
        "../../data/game_id_list/1_automated.json"
        if len(sys.argv) == 1
        else sys.argv[1]
    )
    with open(saved_file_path, "w", encoding="utf8") as f3:
        f3.writelines(json.dumps(json_result, ensure_ascii=False, indent=2))
