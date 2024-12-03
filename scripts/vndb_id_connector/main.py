# WARN: Currently ALL SHIT MOUNTAIN, proceed WITH CAUTION
import json
import sys

import psycopg2

from modules.bangumi import Bangumi
from modules.steam import Steam
from modules.utils import normalize_string
from modules.vndb import Vndb

if __name__ == "__main__":
    # connect db
    vndb_conn = psycopg2.connect(database='vndb', user='vndb', password='vndb', host='localhost',
                                 port='10001')
    vndb_cur = vndb_conn.cursor()
    bangumi_conn = psycopg2.connect(database='bangumi', user='bangumi', password='bangumi', host='localhost',
                                    port='10000')
    bangumi_cur = bangumi_conn.cursor()

    # var
    bangumi_id_name_dict = {}
    bangumi_name_id_dict = {}
    bangumi_dup_id_same_name = {}
    bangumi_dup_id_list = []
    vndb_vid_steamid_dict = {}
    vndb_name_vid_dict = {}
    vndb_vid_names_dict = {}
    vndb_dup_vid_same_name = {}
    vndb_dup_vid_list = []
    vndb_rid_vid_dict = {}
    vndb_rid_multi_vid_list = []
    vndb_release_name_vid_dict = {}
    vndb_dup_release_name_list = []

    # get dict
    bangumi = Bangumi(bangumi_cur, bangumi_id_name_dict, bangumi_name_id_dict, bangumi_dup_id_list,
                      bangumi_dup_id_same_name)
    bangumi.main()
    steam = Steam(vndb_cur, vndb_vid_steamid_dict)
    steam.main()
    vndb = Vndb(vndb_cur, vndb_name_vid_dict, vndb_vid_names_dict, vndb_dup_vid_same_name, vndb_dup_vid_list,
                vndb_rid_vid_dict, vndb_rid_multi_vid_list, vndb_release_name_vid_dict, vndb_dup_release_name_list)
    vndb.main()


    def get_names(vid, bangumi_id=None):
        names = []
        for name in vndb_vid_names_dict[vid]:
            if not names.__contains__(name):
                names.append(name)
        if bangumi_id:
            for name in bangumi_id_name_dict[bangumi_id]:
                if not names.__contains__(name):
                    names.append(name)
        return names


    # vndb match bangumi
    json_result = {
        "info": {
            "description": "THERE IS NO WARRANTY FOR THE DATA, TO THE EXTENT PERMITTED BY APPLICABLE LAW.",
        }
    }
    matches = []
    for vid, names in vndb_vid_names_dict.items():
        # steam
        steam_matches = []
        if vndb_vid_steamid_dict.__contains__(vid):
            steam_matches = vndb_vid_steamid_dict[vid]
        # bangumi
        bangumi_matches = []
        for name in names:
            name = normalize_string(name)
            if bangumi_name_id_dict.__contains__(name):
                if not bangumi_matches.__contains__(bangumi_name_id_dict[name]):
                    bangumi_matches.append(bangumi_name_id_dict[name])
        if bangumi_matches.__len__() == 0 and steam_matches.__len__() == 0:
            continue
        if steam_matches.__len__() > 0:
            for steam_match in steam_matches:
                if bangumi_matches.__len__() > 0:
                    for bangumi_match in bangumi_matches:
                        matches.append({
                            "steam": str(steam_match),
                            "bangumi": str(bangumi_match),
                            "vndb": str(vid),
                            "names": get_names(vid, bangumi_match)
                        })
                else:
                    matches.append({
                        "steam": str(steam_match),
                        "bangumi": "",
                        "vndb": str(vid),
                        "names": get_names(vid)
                    })
        else:
            if bangumi_matches.__len__() > 0:
                for bangumi_match in bangumi_matches:
                    matches.append({
                        "steam": "",
                        "bangumi": str(bangumi_match),
                        "vndb": str(vid),
                        "names": get_names(vid, bangumi_match)
                    })
    json_result['entries'] = matches
    saved_file_path = '../../game_id_connector/2-vndb_automated.json' if len(sys.argv) == 1 else sys.argv[1]
    with open(saved_file_path, 'w', encoding='utf8') as f3:
        f3.writelines(json.dumps(json_result, ensure_ascii=False, indent=2))
