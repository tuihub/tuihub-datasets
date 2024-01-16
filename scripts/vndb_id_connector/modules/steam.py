class Steam:
    def __init__(self, vndb_cur, vndb_vid_steamid_dict):
        self.vndb_cur = vndb_cur
        self.vndb_vid_steamid_dict = vndb_vid_steamid_dict

    def main(self):
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
        self.vndb_cur.execute(sql)
        data = self.vndb_cur.fetchall()
        for line in data:
            if not self.vndb_vid_steamid_dict.__contains__(line[0]):
                self.vndb_vid_steamid_dict[line[0]] = []
            if not self.vndb_vid_steamid_dict[line[0]].__contains__(line[1]):
                self.vndb_vid_steamid_dict[line[0]].append(line[1])
        # print("vndb_vid_steamid_dict len = " + str(vndb_vid_steamid_dict.__len__()))
