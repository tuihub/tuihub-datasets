# WARN: Currently ALL SHIT MOUNTAIN, proceed WITH CAUTION
import copy
import json

import psycopg2
# 导入一个模块，用来处理不同语言的标点符号
import unicodedata


# 定义一个函数，用来判断两个字符串是否一致，但是要将英文标点符号、简体中文标点符号、繁体中文标点符号、日文标点符号之间的差异，以及两个字符串之间的空格
def compare_strings(str1, str2):
    # 初始化一个空字符串，用来存储处理后的第一个字符串
    new_str1 = ""
    # 遍历第一个字符串中的每个字符
    for char in str1:
        # 如果字符是标点符号
        if unicodedata.category(char).startswith("P"):
            # 将字符转换为通用的标点符号
            char = unicodedata.normalize("NFKC", char)
        # 如果字符不是空格
        if char != " ":
            # 将字符添加到新字符串中
            new_str1 += char
    # 初始化一个空字符串，用来存储处理后的第二个字符串
    new_str2 = ""
    # 遍历第二个字符串中的每个字符
    for char in str2:
        # 如果字符是标点符号
        if unicodedata.category(char).startswith("P"):
            # 将字符转换为通用的标点符号
            char = unicodedata.normalize("NFKC", char)
        # 如果字符不是空格
        if char != " ":
            # 将字符添加到新字符串中
            new_str2 += char
    # 判断两个新字符串是否相等，返回布尔值
    return new_str1 == new_str2


def normalize_string(s):
    new_str = ""
    for char in s:
        if unicodedata.category(char).startswith("P"):
            char = unicodedata.normalize("NFKC", char)
        if char.isupper():
            char = char.lower()
        if char != " ":
            new_str += char
    return new_str


def parse_infobox(input_str, keyword):
    input_str = input_str.replace("\r", "").replace("\n", "")
    input_str = input_str.replace("\\r", "").replace("\\n", "")
    names = []
    try:
        section = input_str.split("|" + keyword + "=")[1].split("|")[0]
        lines = section.strip("{}").replace("[", "").split("]")
        for line in lines:
            if line:
                names.append(line)
    except:
        return {}
    return names


vndb_conn = psycopg2.connect(database='vndb', user='postgres', password='postgres', host='192.168.5.17', port='5432')
vndb_cur = vndb_conn.cursor()
bangumi_conn = psycopg2.connect(database='bangumi', user='postgres', password='postgres', host='192.168.5.17',
                                port='5432')
bangumi_cur = bangumi_conn.cursor()

# bangumi_name_id_dict
bangumi_id_name_dict = {}
bangumi_name_id_dict = {}
bangumi_dup_id_same_name = {}
bangumi_dup_id_list = []


def add_to_bangumi_name_id_dict(s, id):
    s = normalize_string(s)
    if bangumi_name_id_dict.__contains__(s) and bangumi_name_id_dict[s] != id:
        print("W: " + s + " -> " + str(bangumi_name_id_dict[s]) + " already exists")
    bangumi_name_id_dict[s] = id


def get_bangumi_platforms(data):
    platforms = []
    for line in data:
        cur_platforms = parse_infobox(line[4], "平台")
        for platform in cur_platforms:
            platform = normalize_string(platform)
            if not platforms.__contains__(platform):
                platforms.append(platform)
    return platforms


def add_to_bangumi_name_id_dict(s, id):
    s = normalize_string(s)
    if s in bangumi_name_id_dict and bangumi_name_id_dict[s] != id:
        cur_vid = bangumi_name_id_dict[s]
        # print("W: " + s + " -> " + cur_vid + " already exists")
        if not bangumi_dup_id_list.__contains__(id):
            bangumi_dup_id_list.append(id)
            if not bangumi_dup_id_list.__contains__(cur_vid):
                bangumi_dup_id_list.append(cur_vid)
        if not bangumi_dup_id_same_name.__contains__(s):
            bangumi_dup_id_same_name[s] = []
            bangumi_dup_id_same_name[s].append(cur_vid)
            bangumi_dup_id_same_name[s].append(id)
        else:
            if not bangumi_dup_id_same_name[s].__contains__(id):
                bangumi_dup_id_same_name[s].append(id)
    else:
        bangumi_name_id_dict[s] = id


def add_to_bangumi_name_id_dict_with_dup_list(s, id):
    s = normalize_string(s)
    if id in bangumi_dup_id_list:
        return
    if s in bangumi_name_id_dict and bangumi_name_id_dict[s] != id:
        print("W: " + s + " -> " + str(bangumi_name_id_dict[s]) + " already exists")
    else:
        bangumi_name_id_dict[s] = id


sql = """SELECT
    "public".subject."id", 
    "public".subject."type", 
    "public".subject."name", 
    "public".subject.name_cn, 
    "public".subject.infobox
FROM
    "public".subject
WHERE
    "public".subject."type" = 4"""
bangumi_cur.execute(sql)
data = bangumi_cur.fetchall()
# bangumi_platforms = get_bangumi_platforms(data)
bangumi_included_platforms = ["pc", "win", "dos", "linux", "mac", "mac"]
bangumi_excluded_platforms = ["windowsphone"]


def platform_supported(cur_platforms):
    cur_platforms = normalize_string(cur_platforms)
    for ep in bangumi_excluded_platforms:
        if ep in cur_platforms:
            return False
    for ip in bangumi_included_platforms:
        if ip in cur_platforms:
            return True
    return False


for line in data:
    cur_platforms = parse_infobox(line[4], "平台")
    if cur_platforms.__len__() > 0 and not platform_supported(cur_platforms[0]):
        continue
    if line[2]:
        add_to_bangumi_name_id_dict(line[2], line[0])
    if line[3] and line[2] and line[3] != line[2]:
        add_to_bangumi_name_id_dict(line[3], line[0])
bangumi_name_id_dict = {}
for line in data:
    cur_platforms = parse_infobox(line[4], "平台")
    if cur_platforms.__len__() > 0 and not platform_supported(cur_platforms[0]):
        continue
    if line[2]:
        add_to_bangumi_name_id_dict_with_dup_list(line[2], line[0])
    if line[3] and line[2] and line[3] != line[2]:
        add_to_bangumi_name_id_dict_with_dup_list(line[3], line[0])
    # TODO: '{[en|Tun Town 2]}' not handled, dropping "别名" section
    # cur_alt_names = parse_infobox(line[4], "别名")
    # for alt_name in cur_alt_names:
    #     add_to_bangumi_name_id_dict(alt_name, line[0])
    if not bangumi_id_name_dict.__contains__(line[0]):
        bangumi_id_name_dict[line[0]] = []
    if line[2]:
        if not bangumi_id_name_dict[line[0]].__contains__(line[2]):
            bangumi_id_name_dict[line[0]].append(line[2])
    if line[3] and line[2] and line[3] != line[2]:
        if not bangumi_id_name_dict[line[0]].__contains__(line[3]):
            bangumi_id_name_dict[line[0]].append(line[3])
print("bangumi_name_id_dict len = " + str(bangumi_name_id_dict.__len__()))

# vndb_vid_steamid_dict
vndb_vid_steamid_dict = {}
sql = """SELECT DISTINCT
    releases_vn.vid AS vid, 
    releases.l_steam AS steamid
FROM
    releases
    INNER JOIN
    releases_vn
    ON 
        releases."id" = releases_vn."id"
WHERE
    releases.l_steam <> 0"""
vndb_cur.execute(sql)
data = vndb_cur.fetchall()
for line in data:
    vndb_vid_steamid_dict[line[0]] = line[1]
print("vndb_vid_steamid_dict len = " + str(vndb_vid_steamid_dict.__len__()))

# vndb_name_vid_dict
vndb_name_vid_dict = {}
vndb_vid_names_dict = {}
vndb_dup_vid_same_name = {}
vndb_dup_vid_list = []


def add_to_vndb_name_vid_dict(s, vid):
    s = normalize_string(s)
    if s in vndb_name_vid_dict and vndb_name_vid_dict[s] != vid:
        cur_vid = vndb_name_vid_dict[s]
        # print("W: " + s + " -> " + cur_vid + " already exists")
        if not vndb_dup_vid_list.__contains__(vid):
            vndb_dup_vid_list.append(vid)
            if not vndb_dup_vid_list.__contains__(cur_vid):
                vndb_dup_vid_list.append(cur_vid)
        if not vndb_dup_vid_same_name.__contains__(s):
            vndb_dup_vid_same_name[s] = []
            vndb_dup_vid_same_name[s].append(cur_vid)
            vndb_dup_vid_same_name[s].append(vid)
        else:
            if not vndb_dup_vid_same_name[s].__contains__(vid):
                vndb_dup_vid_same_name[s].append(vid)
    else:
        vndb_name_vid_dict[s] = vid


def add_to_vndb_name_vid_dict_with_dup_list(s, vid):
    s = normalize_string(s)
    if vid in vndb_dup_vid_list:
        return
    if s in vndb_name_vid_dict and vndb_name_vid_dict[s] != vid:
        print("W: " + s + " -> " + vndb_name_vid_dict[s] + " already exists")
    else:
        vndb_name_vid_dict[s] = vid


sql = """SELECT DISTINCT
    vn_titles."id" AS vid,
    vn_titles.title AS title,
    vn_titles.latin AS title_latin 
FROM
    vn_titles 
WHERE
    ( vn_titles.title IS NOT NULL OR vn_titles.latin IS NOT NULL ) 
    AND (
        vn_titles.lang = 'ja' 
        OR vn_titles.lang = 'zh-Hans' 
        OR vn_titles.lang = 'zh-Hant' 
        OR vn_titles.lang = 'en' 
        OR vn_titles.lang = 'uk' 
    ) 
ORDER BY
    vid ASC"""
vndb_cur.execute(sql)
data = vndb_cur.fetchall()
# get dup list
for line in data:
    if line[1]:
        add_to_vndb_name_vid_dict(line[1], line[0])
    if line[2]:
        add_to_vndb_name_vid_dict(line[2], line[0])
# clear dict
vndb_name_vid_dict = {}
# build dict
for line in data:
    if vndb_dup_vid_list.__contains__(line[0]):
        continue
    if line[1]:
        add_to_vndb_name_vid_dict_with_dup_list(line[1], line[0])
    if line[2]:
        add_to_vndb_name_vid_dict_with_dup_list(line[2], line[0])
    # reverse
    if line[0] not in vndb_vid_names_dict:
        vndb_vid_names_dict[line[0]] = []
    if line[1]:
        if not vndb_vid_names_dict[line[0]].__contains__(line[1]):
            vndb_vid_names_dict[line[0]].append(line[1])
    if line[2]:
        if not vndb_vid_names_dict[line[0]].__contains__(line[2]):
            vndb_vid_names_dict[line[0]].append(line[2])
vndb_name_vid_dict_title_only = copy.deepcopy(vndb_name_vid_dict)



sql2 = """SELECT DISTINCT
    releases_vn.vid AS vid,
    releases_titles.title AS title,
    releases_titles.latin AS title_latin
FROM
    releases_vn
    INNER JOIN releases_titles ON releases_vn."id" = releases_titles."id"
    INNER JOIN releases_platforms ON releases_vn."id" = releases_platforms."id"
WHERE
    ( releases_titles.title IS NOT NULL OR releases_titles.latin IS NOT NULL )
    AND ( releases_platforms.platform = 'win' OR releases_platforms.platform = 'dos' OR releases_platforms.platform = 'lin' OR releases_platforms.platform = 'mac' )
    AND (
        releases_titles.lang = 'ja'
        OR releases_titles.lang = 'zh-Hans'
        OR releases_titles.lang = 'zh-Hant'
        OR releases_titles.lang = 'en'
        OR releases_titles.lang = 'uk'
    )
ORDER BY
    vid ASC"""
vndb_cur.execute(sql2)
data2 = vndb_cur.fetchall()
# get dup list
vndb_dup_vid_same_name = {}
vndb_dup_vid_list = []
for line in data:
    if line[1]:
        add_to_vndb_name_vid_dict(line[1], line[0])
    if line[2]:
        add_to_vndb_name_vid_dict(line[2], line[0])
for line in data2:
    if line[1]:
        add_to_vndb_name_vid_dict(line[1], line[0])
    if line[2]:
        add_to_vndb_name_vid_dict(line[2], line[0])
# clear dict
vndb_name_vid_dict = {}
# build dict
for line in data:
    if vndb_dup_vid_list.__contains__(line[0]):
        continue
    if line[1]:
        add_to_vndb_name_vid_dict_with_dup_list(line[1], line[0])
    if line[2]:
        add_to_vndb_name_vid_dict_with_dup_list(line[2], line[0])
    # reverse
    if line[0] not in vndb_vid_names_dict:
        vndb_vid_names_dict[line[0]] = []
    if line[1]:
        if not vndb_vid_names_dict[line[0]].__contains__(line[1]):
            vndb_vid_names_dict[line[0]].append(line[1])
    if line[2]:
        if not vndb_vid_names_dict[line[0]].__contains__(line[2]):
            vndb_vid_names_dict[line[0]].append(line[2])
for line in data2:
    if vndb_dup_vid_list.__contains__(line[0]):
        continue
    if line[1]:
        add_to_vndb_name_vid_dict_with_dup_list(line[1], line[0])
    if line[2]:
        add_to_vndb_name_vid_dict_with_dup_list(line[2], line[0])
    # reverse
    if line[0] not in vndb_vid_names_dict:
        vndb_vid_names_dict[line[0]] = []
    if line[1]:
        if not vndb_vid_names_dict[line[0]].__contains__(line[1]):
            vndb_vid_names_dict[line[0]].append(line[1])
    if line[2]:
        if not vndb_vid_names_dict[line[0]].__contains__(line[2]):
            vndb_vid_names_dict[line[0]].append(line[2])


print("vndb_name_vid_dict len = " + str(vndb_name_vid_dict.__len__()))
print("vndb_vid_names_dict len = " + str(vndb_vid_names_dict.__len__()))


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
    for name in names:
        name = normalize_string(name)
        if not bangumi_name_id_dict.__contains__(name):
            continue
        else:
            match_count = match_count + 1
            match['bangumi'] = str(bangumi_name_id_dict[name])
            break
    if not match.__contains__('bangumi'):
        match['bangumi'] = ""
    if match_count > 0:
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
