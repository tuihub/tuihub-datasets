# 定义一个函数，用来判断两个字符串是否一致，但是要将英文标点符号、简体中文标点符号、繁体中文标点符号、日文标点符号之间的差异，以及两个字符串之间的空格
import unicodedata


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


def parse_infobox(input_str, keyword):
    section = _extract_infobox_section(input_str, keyword)
    if not section:
        return []

    names = _parse_bracketed_values(section)
    if len(names) > 0:
        return names

    section = section.strip().strip("{}")
    return [section] if section else []
