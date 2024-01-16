from .utils import parse_infobox, normalize_string


class Bangumi:
    BANGUMI_INCLUDED_PLATFORMS = ["pc", "win", "dos", "linux", "mac", "mac"]
    BANGUMI_EXCLUDED_PLATFORMS = ["windowsphone"]

    def __init__(self, bangumi_cur, bangumi_id_name_dict, bangumi_name_id_dict, bangumi_dup_id_list,
                 bangumi_dup_id_same_name):
        self.bangumi_cur = bangumi_cur
        self.bangumi_id_name_dict = bangumi_id_name_dict
        self.bangumi_name_id_dict = bangumi_name_id_dict
        self.bangumi_dup_id_list = bangumi_dup_id_list
        self.bangumi_dup_id_same_name = bangumi_dup_id_same_name

    def get_bangumi_platforms(self, data):
        platforms = []
        for line in data:
            cur_platforms = parse_infobox(line[4], "平台")
            for platform in cur_platforms:
                platform = normalize_string(platform)
                if not platforms.__contains__(platform):
                    platforms.append(platform)
        return platforms

    def add_to_bangumi_name_id_dict(self, s, id):
        s = normalize_string(s)
        if s in self.bangumi_name_id_dict and self.bangumi_name_id_dict[s] != id:
            cur_vid = self.bangumi_name_id_dict[s]
            # print("W: " + s + " -> " + cur_vid + " already exists")
            if not self.bangumi_dup_id_list.__contains__(id):
                self.bangumi_dup_id_list.append(id)
                if not self.bangumi_dup_id_list.__contains__(cur_vid):
                    self.bangumi_dup_id_list.append(cur_vid)
            if not self.bangumi_dup_id_same_name.__contains__(s):
                self.bangumi_dup_id_same_name[s] = []
                self.bangumi_dup_id_same_name[s].append(cur_vid)
                self.bangumi_dup_id_same_name[s].append(id)
            else:
                if not self.bangumi_dup_id_same_name[s].__contains__(id):
                    self.bangumi_dup_id_same_name[s].append(id)
        else:
            self.bangumi_name_id_dict[s] = id

    def add_to_bangumi_name_id_dict_with_dup_list(self, s, id):
        s = normalize_string(s)
        if id in self.bangumi_dup_id_list:
            return
        if s in self.bangumi_name_id_dict and self.bangumi_name_id_dict[s] != id:
            print("W: " + s + " -> " + str(self.bangumi_name_id_dict[s]) + " already exists")
        else:
            self.bangumi_name_id_dict[s] = id

    def get_data_from_db(self):
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
        self.bangumi_cur.execute(sql)
        return self.bangumi_cur.fetchall()

    def platform_supported(self, cur_platforms):
        cur_platforms = normalize_string(cur_platforms)
        for ep in self.BANGUMI_EXCLUDED_PLATFORMS:
            if ep in cur_platforms:
                return False
        for ip in self.BANGUMI_INCLUDED_PLATFORMS:
            if ip in cur_platforms:
                return True
        return False

    def get_dup(self, data):
        for line in data:
            cur_platforms = parse_infobox(line[4], "平台")
            if cur_platforms.__len__() > 0 and not self.platform_supported(cur_platforms[0]):
                continue
            if line[2]:
                self.add_to_bangumi_name_id_dict(line[2], line[0])
            if line[3] and line[2] and line[3] != line[2]:
                self.add_to_bangumi_name_id_dict(line[3], line[0])
        self.bangumi_name_id_dict = {}

    def get_dict(self, data):
        for line in data:
            cur_platforms = parse_infobox(line[4], "平台")
            if cur_platforms.__len__() > 0 and not self.platform_supported(cur_platforms[0]):
                continue
            if line[2]:
                self.add_to_bangumi_name_id_dict_with_dup_list(line[2], line[0])
            if line[3] and line[2] and line[3] != line[2]:
                self.add_to_bangumi_name_id_dict_with_dup_list(line[3], line[0])
            # TODO: '{[en|Tun Town 2]}' not handled, dropping "别名" section
            # cur_alt_names = parse_infobox(line[4], "别名")
            # for alt_name in cur_alt_names:
            #     add_to_bangumi_name_id_dict(alt_name, line[0])
            if not self.bangumi_id_name_dict.__contains__(line[0]):
                self.bangumi_id_name_dict[line[0]] = []
            if line[2]:
                if not self.bangumi_id_name_dict[line[0]].__contains__(line[2]):
                    self.bangumi_id_name_dict[line[0]].append(line[2])
            if line[3] and line[2] and line[3] != line[2]:
                if not self.bangumi_id_name_dict[line[0]].__contains__(line[3]):
                    self.bangumi_id_name_dict[line[0]].append(line[3])

    def main(self):
        data = self.get_data_from_db()
        self.get_dup(data)
        self.get_dict(data)
