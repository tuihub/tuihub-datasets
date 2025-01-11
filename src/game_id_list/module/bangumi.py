import os

import psycopg2


def get_bangumi_conn():
    dbname = os.getenv('BANGUMI_DB')
    user = os.getenv('BANGUMI_USER')
    password = os.getenv('BANGUMI_PASSWORD')
    host = os.getenv('BANGUMI_HOST')
    port = os.getenv('BANGUMI_PORT')

    connection = psycopg2.connect(
        dbname=dbname,
        user=user,
        password=password,
        host=host,
        port=port
    )
    return connection


def parse_alt_names(line) -> list[str]:
    line = line.replace("\r", "").replace("\n", "")
    line = line.replace("\\r", "").replace("\\n", "")
    pos = line.find("别名")
    if pos == -1:
        return []
    pos_start = pos + 2
    while pos_start < pos + 5 and line[pos_start] != "{":
        pos_start += 1
    if pos_start == pos + 5 and line[pos_start] != "{":
        return []
    pos_end = pos + 2
    while line[pos_end] != "}":
        pos_end += 1
    altn = line[pos_start: pos_end + 1]
    alen = altn.__len__()
    p = 0
    alt_names = []
    while p < alen:
        if altn[p] == "[":
            pe = p
            while altn[pe] != "]":
                pe += 1
            p2 = p
            while p2 < pe and altn[p2] != "|":
                p2 += 1
            cnt_alt_name = ""
            # no '|'
            if p2 >= pe:
                cnt_alt_name = altn[p + 1: pe]
            else:
                cnt_alt_name = altn[p2 + 1: pe]
            alt_names.append(cnt_alt_name)
            p = pe + 1
        else:
            p += 1
    return alt_names


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
