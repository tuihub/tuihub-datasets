import os

import psycopg2


def get_vndb_conn():
    dbname = os.getenv('VNDB_DB')
    user = os.getenv('VNDB_USER')
    password = os.getenv('VNDB_PASSWORD')
    host = os.getenv('VNDB_HOST')
    port = os.getenv('VNDB_PORT')

    connection = psycopg2.connect(
        dbname=dbname,
        user=user,
        password=password,
        host=host,
        port=port
    )
    return connection


# return {vid, [steam_ids]}, {steam_id, vid}
def get_vndb_steam_relation() -> tuple[dict[str, list[int]], dict[int, str]]:
    conn = get_vndb_conn()
    cur = conn.cursor()
    # steamid with multiple vid
    sql = """SELECT DISTINCT
                extlinks."value" AS steamid 
            FROM
                releases
                INNER JOIN releases_vn ON releases."id" = releases_vn."id"
                INNER JOIN releases_extlinks ON releases_extlinks."id" = releases."id"
                INNER JOIN extlinks ON extlinks."id" = releases_extlinks.link 
            WHERE
                extlinks.site = 'steam' 
                AND extlinks."value" IS NOT NULL
            GROUP BY
                steamid
            HAVING
                COUNT(releases_vn.vid) > 1"""
    cur.execute(sql)
    data = cur.fetchall()
    steam_ids_with_multiple_vid = [int(line[0]) for line in data]

    sql = """SELECT DISTINCT
                releases_vn.vid AS vid,
                extlinks."value" AS steamid 
            FROM
                releases
                INNER JOIN releases_vn ON releases."id" = releases_vn."id"
                INNER JOIN releases_extlinks ON releases_extlinks."id" = releases."id"
                INNER JOIN extlinks ON extlinks."id" = releases_extlinks.link 
            WHERE
                extlinks.site = 'steam' 
                AND extlinks."value" IS NOT NULL"""
    cur.execute(sql)
    data = cur.fetchall()
    conn.close()
    result = {}
    r_result = {}
    for line in data:
        vid = str(line[0])
        steam_id = int(line[1])
        # skip steam_id with multiple vid
        if steam_id in steam_ids_with_multiple_vid:
            continue
        # add to {vid, [steam_ids]}
        if vid not in result:
            result[vid] = []
        if steam_id not in result[vid]:
            result[vid].append(steam_id)
        # add to {steam_id, vid}
        if steam_id not in r_result:
            r_result[steam_id] = vid
    return result, r_result
