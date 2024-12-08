from .utils import parse_infobox, normalize_string


class Bangumi:
    BANGUMI_INCLUDED_PLATFORMS = ["pc", "win", "dos", "linux", "mac", "mac"]
    BANGUMI_EXCLUDED_PLATFORMS = ["windowsphone"]

    def __init__(
        self,
        bangumi_cur,
        bangumi_id_name_dict,
        bangumi_name_id_dict,
        bangumi_dup_id_list,
        bangumi_dup_id_same_name,
    ):
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
            print(
                "W: "
                + s
                + " -> "
                + str(self.bangumi_name_id_dict[s])
                + " already exists"
            )
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

    def parse_alt_names(self, line):
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
        altn = line[pos_start : pos_end + 1]
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
                    cnt_alt_name = altn[p + 1 : pe]
                else:
                    cnt_alt_name = altn[p2 + 1 : pe]
                alt_names.append(cnt_alt_name)
                p = pe + 1
            else:
                p += 1
        return alt_names

    def get_dup(self, data):
        for line in data:
            cur_platforms = parse_infobox(line[4], "平台")
            if cur_platforms.__len__() > 0 and not self.platform_supported(
                cur_platforms[0]
            ):
                continue
            if line[2]:
                self.add_to_bangumi_name_id_dict(line[2], line[0])
            if line[3] and line[2] and line[3] != line[2]:
                self.add_to_bangumi_name_id_dict(line[3], line[0])
            if line[4]:
                cur_alt_names = self.parse_alt_names(line[4])
                for alt_name in cur_alt_names:
                    self.add_to_bangumi_name_id_dict(alt_name, line[0])
        self.bangumi_name_id_dict = {}

    def get_dict(self, data):
        for line in data:
            cur_platforms = parse_infobox(line[4], "平台")
            if cur_platforms.__len__() > 0 and not self.platform_supported(
                cur_platforms[0]
            ):
                continue
            if line[2]:
                self.add_to_bangumi_name_id_dict_with_dup_list(line[2], line[0])
            if line[3] and line[2] and line[3] != line[2]:
                self.add_to_bangumi_name_id_dict_with_dup_list(line[3], line[0])
            alt_names = self.parse_alt_names(line[4])
            for alt_name in alt_names:
                self.add_to_bangumi_name_id_dict_with_dup_list(alt_name, line[0])
            if not self.bangumi_id_name_dict.__contains__(line[0]):
                self.bangumi_id_name_dict[line[0]] = []
            if line[2]:
                if not self.bangumi_id_name_dict[line[0]].__contains__(line[2]):
                    self.bangumi_id_name_dict[line[0]].append(line[2])
            if line[3] and line[2] and line[3] != line[2]:
                if not self.bangumi_id_name_dict[line[0]].__contains__(line[3]):
                    self.bangumi_id_name_dict[line[0]].append(line[3])
            for alt_name in alt_names:
                if not self.bangumi_id_name_dict[line[0]].__contains__(alt_name):
                    self.bangumi_id_name_dict[line[0]].append(alt_name)

    def main(self):
        data = self.get_data_from_db()
        self.get_dup(data)
        self.get_dict(data)
