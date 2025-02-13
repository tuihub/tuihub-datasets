import json


def get_vndb_vid_dict(data):
    vndb_vid_dict = {}
    for entry in data["entries"]:
        if not vndb_vid_dict.__contains__(entry["vndb"]):
            vndb_vid_dict[entry["vndb"]] = []
        vndb_vid_dict[entry["vndb"]].append(entry)
    return vndb_vid_dict


if __name__ == "__main__":
    # vndb_id_connector
    f = open("../../data/vndb_id_connector/1_manually.json", encoding="utf8")
    manual_data = json.load(f)
    f = open("../../data/vndb_id_connector/2_automated.json", encoding="utf8")
    vndb_data = json.load(f)
    manual_vndb_vid_dict = get_vndb_vid_dict(manual_data)
    merged_manual_vndb_vid_list = []
    merged_data = {"info": vndb_data["info"], "entries": []}
    for entry in vndb_data["entries"]:
        vid = entry["vndb"]
        if manual_vndb_vid_dict.__contains__(vid):
            if merged_manual_vndb_vid_list.__contains__(vid):
                continue
            else:
                for entry in manual_vndb_vid_dict[vid]:
                    merged_data["entries"].append(entry)
                merged_manual_vndb_vid_list.append(vid)
        else:
            merged_data["entries"].append(entry)
    with open("../../docs/vndb_id_connector.json", "w", encoding="utf8") as f3:
        f3.writelines(
            json.dumps(
                merged_data, ensure_ascii=False, indent=None, separators=(",", ":")
            )
        )
    # game_id_list
    f = open("../../data/game_id_list/1_automated.json", encoding="utf8")
    game_id_list_data = json.load(f)
    with open("../../docs/game_id_list.json", "w", encoding="utf8") as f3:
        f3.writelines(
            json.dumps(
                game_id_list_data, ensure_ascii=False, indent=None, separators=(",", ":")
            )
        )
