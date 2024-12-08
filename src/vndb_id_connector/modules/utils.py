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
