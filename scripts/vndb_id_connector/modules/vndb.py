import copy

from .utils import normalize_string


class Vndb:
    def __init__(self, vndb_cur, vndb_name_vid_dict, vndb_vid_names_dict, vndb_dup_vid_same_name, vndb_dup_vid_list,
                 vndb_rid_vid_dict, vndb_rid_multi_vid_list, vndb_release_name_vid_dict, vndb_dup_release_name_list):
        self.vndb_cur = vndb_cur
        self.vndb_name_vid_dict = vndb_name_vid_dict
        self.vndb_vid_names_dict = vndb_vid_names_dict
        self.vndb_dup_vid_same_name = vndb_dup_vid_same_name
        self.vndb_dup_vid_list = vndb_dup_vid_list
        self.vndb_rid_vid_dict = vndb_rid_vid_dict
        self.vndb_rid_multi_vid_list = vndb_rid_multi_vid_list
        self.vndb_release_name_vid_dict = vndb_release_name_vid_dict
        self.vndb_dup_release_name_list = vndb_dup_release_name_list

    def add_to_vndb_name_vid_dict(self, s, vid):
        s = normalize_string(s)
        if s in self.vndb_name_vid_dict and self.vndb_name_vid_dict[s] != vid:
            cur_vid = self.vndb_name_vid_dict[s]
            # print("W: " + s + " -> " + cur_vid + " already exists")
            if not self.vndb_dup_vid_list.__contains__(vid):
                self.vndb_dup_vid_list.append(vid)
                if not self.vndb_dup_vid_list.__contains__(cur_vid):
                    self.vndb_dup_vid_list.append(cur_vid)
            if not self.vndb_dup_vid_same_name.__contains__(s):
                self.vndb_dup_vid_same_name[s] = []
                self.vndb_dup_vid_same_name[s].append(cur_vid)
                self.vndb_dup_vid_same_name[s].append(vid)
            else:
                if not self.vndb_dup_vid_same_name[s].__contains__(vid):
                    self.vndb_dup_vid_same_name[s].append(vid)
        else:
            self.vndb_name_vid_dict[s] = vid

    def add_to_vndb_name_vid_dict_with_dup_list(self, s, vid):
        s = normalize_string(s)
        if vid in self.vndb_dup_vid_list:
            return
        if s in self.vndb_name_vid_dict and self.vndb_name_vid_dict[s] != vid:
            print("W: " + s + " -> " + self.vndb_name_vid_dict[s] + " already exists")
        else:
            self.vndb_name_vid_dict[s] = vid

    def get_vn_titles_from_db(self):
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
        self.vndb_cur.execute(sql)
        return self.vndb_cur.fetchall()

    def get_dup_vn_titles(self, data):
        # get dup list
        for line in data:
            if line[1]:
                self.add_to_vndb_name_vid_dict(line[1], line[0])
            if line[2]:
                self.add_to_vndb_name_vid_dict(line[2], line[0])
        # clear dict
        self.vndb_name_vid_dict = {}

    def get_dict_vn_titles(self, data):
        # build dict
        for line in data:
            if self.vndb_dup_vid_list.__contains__(line[0]):
                continue
            if line[1]:
                self.add_to_vndb_name_vid_dict_with_dup_list(line[1], line[0])
            if line[2]:
                self.add_to_vndb_name_vid_dict_with_dup_list(line[2], line[0])
            # reverse
            if line[0] not in self.vndb_vid_names_dict:
                self.vndb_vid_names_dict[line[0]] = []
            if line[1]:
                if not self.vndb_vid_names_dict[line[0]].__contains__(line[1]):
                    self.vndb_vid_names_dict[line[0]].append(line[1])
            if line[2]:
                if not self.vndb_vid_names_dict[line[0]].__contains__(line[2]):
                    self.vndb_vid_names_dict[line[0]].append(line[2])

    def add_to_vndb_release_name_vid_dict(self, s, vid):
        n_name = normalize_string(s)
        if self.vndb_release_name_vid_dict.__contains__(n_name) and self.vndb_release_name_vid_dict[n_name] != vid:
            # print("W: release " + n_name + " -> " + str(self.vndb_release_name_vid_dict[n_name]) + " already exists")
            if not self.vndb_dup_release_name_list.__contains__(n_name):
                self.vndb_dup_release_name_list.append(n_name)
        else:
            self.vndb_release_name_vid_dict[n_name] = vid

    def add_to_vndb_release_name_vid_dict_with_dup_list(self, s, vid):
        n_name = normalize_string(s)
        if self.vndb_dup_release_name_list.__contains__(n_name):
            return
        if self.vndb_release_name_vid_dict.__contains__(n_name) and self.vndb_release_name_vid_dict[n_name] != vid:
            print("W: release " + n_name + " -> " + str(self.vndb_release_name_vid_dict[n_name]) + " already exists")
        else:
            self.vndb_release_name_vid_dict[n_name] = vid

    def get_vn_releases_from_db(self):
        sql2 = """SELECT DISTINCT
                    releases_vn.vid AS vid,
                    releases_titles.title AS title,
                    releases_titles.latin AS title_latin,
                    releases_vn."id" AS rid
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
        self.vndb_cur.execute(sql2)
        return self.vndb_cur.fetchall()

    def get_dup_vn_releases(self, data):
        self.vndb_release_name_vid_dict = copy.deepcopy(self.vndb_name_vid_dict)
        # get self.vndb_rid_multi_vid_list
        for line in data:
            if self.vndb_dup_vid_list.__contains__(line[0]):
                continue
            if self.vndb_rid_vid_dict.__contains__(line[3]) and self.vndb_rid_vid_dict[line[3]] != line[0]:
                if not self.vndb_rid_multi_vid_list.__contains__(line[3]):
                    self.vndb_rid_multi_vid_list.append(line[3])
            else:
                self.vndb_rid_vid_dict[line[3]] = line[0]
        self.vndb_release_name_vid_dict = copy.deepcopy(self.vndb_name_vid_dict)
        for line in data:
            if self.vndb_dup_vid_list.__contains__(line[0]):
                continue
            if self.vndb_rid_multi_vid_list.__contains__(line[3]):
                continue
            if line[1]:
                self.add_to_vndb_release_name_vid_dict(line[1], line[0])
            if line[2]:
                self.add_to_vndb_release_name_vid_dict(line[2], line[0])
        self.vndb_release_name_vid_dict = copy.deepcopy(self.vndb_name_vid_dict)

    def get_dict_vn_releases(self, data):
        # add to dict
        for line in data:
            if self.vndb_dup_vid_list.__contains__(line[0]):
                continue
            if self.vndb_rid_multi_vid_list.__contains__(line[3]):
                continue
            if line[0] not in self.vndb_vid_names_dict:
                self.vndb_vid_names_dict[line[0]] = []
            if line[1]:
                if not self.vndb_dup_release_name_list.__contains__(normalize_string(line[1])):
                    self.add_to_vndb_release_name_vid_dict_with_dup_list(line[1], line[0])
                    if not self.vndb_vid_names_dict[line[0]].__contains__(line[1]):
                        self.vndb_vid_names_dict[line[0]].append(line[1])
            if line[2]:
                if not self.vndb_dup_release_name_list.__contains__(normalize_string(line[2])):
                    self.add_to_vndb_release_name_vid_dict_with_dup_list(line[2], line[0])
                    if not self.vndb_vid_names_dict[line[0]].__contains__(line[2]):
                        self.vndb_vid_names_dict[line[0]].append(line[2])

    def main(self):
        data = self.get_vn_titles_from_db()
        self.get_dup_vn_titles(data)
        self.get_dict_vn_titles(data)

        data2 = self.get_vn_releases_from_db()
        self.get_dup_vn_releases(data2)
        self.get_dict_vn_releases(data2)
