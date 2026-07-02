import os

import psycopg2


def _clean_infobox(input_str):
    if not input_str:
        return ""
    input_str = str(input_str)
    input_str = input_str.replace("\r", "").replace("\n", "")
    return input_str.replace("\\r", "").replace("\\n", "")


def _extract_infobox_section(input_str, keyword):
    input_str = _clean_infobox(input_str)
    if not input_str:
        return ""

    key_pos = input_str.find("|" + keyword)
    if key_pos == -1:
        key_pos = input_str.find(keyword)
    if key_pos == -1:
        return ""

    value_pos = input_str.find("=", key_pos)
    if value_pos == -1:
        return ""

    start = value_pos + 1
    while start < len(input_str) and input_str[start].isspace():
        start += 1
    if start >= len(input_str):
        return ""

    if input_str[start] != "{":
        end = input_str.find("|", start)
        if end == -1:
            end = input_str.find("}}", start)
        if end == -1:
            end = len(input_str)
        return input_str[start:end]

    depth = 0
    for pos in range(start, len(input_str)):
        if input_str[pos] == "{":
            depth += 1
        elif input_str[pos] == "}":
            depth -= 1
            if depth == 0:
                return input_str[start + 1 : pos]
    return input_str[start + 1 :]


def _parse_bracketed_values(section):
    names = []
    pos = 0
    while pos < len(section):
        pos_start = section.find("[", pos)
        if pos_start == -1:
            break
        pos_end = section.find("]", pos_start + 1)
        if pos_end == -1:
            break

        name = section[pos_start + 1 : pos_end].strip()
        if "|" in name:
            name = name.split("|", 1)[1].strip()
        if name and name not in names:
            names.append(name)
        pos = pos_end + 1
    return names


def get_bangumi_conn():
    dbname = os.getenv("BANGUMI_DB")
    user = os.getenv("BANGUMI_USER")
    password = os.getenv("BANGUMI_PASSWORD")
    host = os.getenv("BANGUMI_HOST")
    port = os.getenv("BANGUMI_PORT")

    connection = psycopg2.connect(
        dbname=dbname, user=user, password=password, host=host, port=port
    )
    return connection


def parse_alt_names(line) -> list[str]:
    section = _extract_infobox_section(line, "别名")
    if not section:
        return []

    alt_names = _parse_bracketed_values(section)
    if len(alt_names) > 0:
        return alt_names

    section = section.strip().strip("{}")
    return [section] if section else []


def get_bangumi_id_names() -> dict[int, list[str]]:
    conn = get_bangumi_conn()
    cur = conn.cursor()
    sql = """SELECT DISTINCT
                "public".subject."id", 
                "public".subject."name", 
                "public".subject.name_cn, 
                "public".subject.infobox
            FROM
                "public".subject
            WHERE
                "public".subject."type" = 4"""
    cur.execute(sql)
    data = cur.fetchall()
    conn.close()
    result = {}
    for line in data:
        bid = line[0]
        name = line[1]
        name_cn = line[2]
        infobox = line[3]
        alt_names = parse_alt_names(infobox)
        if bid not in result:
            result[bid] = []
        if name not in result[bid]:
            result[bid].append(name)
        if name_cn not in result[bid]:
            result[bid].append(name_cn)
        for alt_name in alt_names:
            if alt_name not in result[bid]:
                result[bid].append(alt_name)
        # remove None
        result[bid] = [x for x in result[bid] if x is not None]
    return result
