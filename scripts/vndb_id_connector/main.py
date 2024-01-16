# WARN: Currently ALL SHIT MOUNTAIN, proceed WITH CAUTION
import copy
import json
import psycopg2

from modules.utils import normalize_string
from modules.bangumi import Bangumi
from modules.steam import Steam
from modules.vndb import Vndb

if __name__ == "__main__":
    # connect db
    vndb_conn = psycopg2.connect(database='vndb', user='postgres', password='postgres', host='192.168.5.17',
                                 port='5432')
    vndb_cur = vndb_conn.cursor()
    bangumi_conn = psycopg2.connect(database='bangumi', user='postgres', password='postgres', host='192.168.5.17',
                                    port='5432')
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

    # vndb match bangumi
    json_result = {
        "info": {
            "description": "THERE IS NO WARRANTY FOR THE DATA, TO THE EXTENT PERMITTED BY APPLICABLE LAW.",
        }
    }
    matches = []
    for vid, names in vndb_vid_names_dict.items():
        match = {}
        match_count = 0
        # steam
        if vndb_vid_steamid_dict.__contains__(vid):
            match_count = match_count + 1
            match['steam'] = str(vndb_vid_steamid_dict[vid])
        else:
            match['steam'] = ""
        # bangumi
        bangumi_matches = []
        for name in names:
            name = normalize_string(name)
            if not bangumi_name_id_dict.__contains__(name):
                continue
            else:
                # match_count = match_count + 1
                # match['bangumi'] = str(bangumi_name_id_dict[name])
                if not bangumi_matches.__contains__(str(bangumi_name_id_dict[name])):
                    bangumi_matches.append(str(bangumi_name_id_dict[name]))
        if bangumi_matches.__len__() > 0:
            if bangumi_matches.__len__() > 1:
                print("bangumi_matches = " + str(bangumi_matches.__len__()) + ", vid = " + vid)
            match_count = match_count + 1
        if match_count > 0:
            if bangumi_matches.__len__() > 0:
                for bangumi_match in bangumi_matches:
                    cur_match = copy.deepcopy(match)
                    cur_match['bangumi'] = bangumi_match
                    cur_match['vndb'] = str(vid)
                    names = []
                    for name in vndb_vid_names_dict[vid]:
                        if not names.__contains__(name):
                            names.append(name)
                    for name in bangumi_id_name_dict[int(cur_match['bangumi'])]:
                        if not names.__contains__(name):
                            names.append(name)
                    cur_match['names'] = names
                    matches.append(cur_match)
            else:
                match['bangumi'] = ""
                match['vndb'] = str(vid)
                names = []
                for name in vndb_vid_names_dict[vid]:
                    if not names.__contains__(name):
                        names.append(name)
                if match['bangumi'] != "":
                    for name in bangumi_id_name_dict[int(match['bangumi'])]:
                        if not names.__contains__(name):
                            names.append(name)
                match['names'] = names
                matches.append(match)
    json_result['entries'] = matches
    with open('../../game_id_connector/2-vndb_automated.json', 'w', encoding='utf8') as f3:
        f3.writelines(json.dumps(json_result, ensure_ascii=False, indent=2))
