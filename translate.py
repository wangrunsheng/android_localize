import os
import time
import hashlib
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom
import requests as net
import urllib.parse

# 百度翻译 API 配置
BAIDU_APP_ID = "2023120800*******"
BAIDU_SECRET_KEY = "H8xZggYl__**********"

SOURCE_PATH = "strings.xml"
TARGET_PATH = "after/res/"

# 调用翻译接口
def translate(content, languageCode):
    host = "https://fanyi-api.baidu.com/api/trans/vip/translate"
    appid = BAIDU_APP_ID
    salt = str(int(time.time() / 1000))
    
    replaceStr = "☀"
    replaceNum = "☁"
    replaceStr1 = "☀☀"
    replaceStr2 = "☀☀☀"
    replaceStr3 = "☀☀☀☀"
    replaceNum1 = "☁☁"
    replaceNum2 = "☁☁☁"
    replaceNum3 = "☁☁☁☁"

    content = content.replace("%3$s", replaceStr3).replace("%2$s", replaceStr2).replace("%1$s", replaceStr1).replace("%s", replaceStr)
    content = content.replace("%3$d", replaceNum3).replace("%2$d", replaceNum2).replace("%1$d", replaceNum1).replace("%d", replaceNum)

    signStr = appid + content + salt + BAIDU_SECRET_KEY
    sign = hashlib.md5(signStr.encode()).hexdigest()
    map = {"q" : content, "from" : "zh", "to": languageCode, "appid":appid, "salt": salt, "sign" : sign}
    params = urllib.parse.urlencode(map)
    url = host + "?" + params
    result = net.get(url).json()

    if ("trans_result" not in result):
        print(languageCode + " : " + content + "  翻译失败")
        return ""
    res = result['trans_result'][0]['dst']
    res = res.replace(replaceStr3, "%3$s").replace(replaceStr2, "%2$s").replace(replaceStr1, "%1$s").replace(replaceStr, "%s")
    res = res.replace(replaceNum3, "%3$d").replace(replaceNum2, "%2$d").replace(replaceNum1, "%1$d").replace(replaceNum, "%d")
    return res


# 从指定 xml 文件读取最后一个注释标签之后的 item
def get_items_after_last_comment(xml_path):
    dom = minidom.parse(xml_path)
    elements = dom.documentElement.childNodes

    last_comment_index = -1
    last_comment_text = ""
    items_dict = {}

    for i, node in enumerate(elements):
        if node.nodeType == node.COMMENT_NODE:  # 识别注释节点
            last_comment_index = i
            last_comment_text = node.data

    # 获取注释后面的元素
    if last_comment_index != -1 and last_comment_index + 1 < len(elements):
        items = [node for node in elements[last_comment_index + 1:] if node.nodeType == node.ELEMENT_NODE]
        for item in items:
            name = item.getAttribute("name")
            text = item.firstChild.nodeValue.strip() if item.firstChild else ""
            items_dict[name] = text

    result = {
        "last_comment": last_comment_text,
        "items": items_dict
    }

    return result


# 保留原文档格式, 并追加新内容
def append_translated_strings(target_xml_path, last_comment, translated_list):
    """ 在目标 XML 的 <resources> 末尾追加翻译后的内容，并先插入最后的注释 """
    
    with open(target_xml_path, "r", encoding="utf-8") as f:
        xml_text = f.read()

    dom = minidom.parseString(xml_text)
    root = dom.documentElement  # 获取 <resources> 节点

    # 添加注释
    if last_comment:
        comment_node = dom.createComment(last_comment)
        root.appendChild(comment_node)

    # 添加翻译后的 <string> 元素
    for model in translated_list:
        new_element = dom.createElement("string")
        new_element.setAttribute("name", model["name"])
        new_text = dom.createTextNode(model["txt"])
        new_element.appendChild(new_text)
        root.appendChild(new_element)

    # 格式化输出，去掉空行
    pretty_xml = "\n".join([line for line in dom.toprettyxml(indent="    ").split("\n") if line.strip()])

    with open(target_xml_path, "w", encoding="utf-8") as f:
        f.write(pretty_xml.split("\n", 1)[1])  # 避免重复写入 XML 头部


baiduCodeMap = {
    "en"   : "values",         # 英语
    "ara"  : "values-ar",      # 阿拉伯语
    "cs"   : "values-cs",      # 捷克语
    "dan"  : "values-da",      # 丹麦语
    "de"   : "values-de",      # 德语
    "el"   : "values-el",      # 希腊语
    "en"   : "values-en",      # 英语
    "spa"  : "values-es",      # 西班牙语
    "fra"  : "values-fr",      # 法语
    "hu"   : "values-hu",      # 匈牙利文
    "id"   : "values-in-rID",  # 印尼语
    "it"   : "values-it",      # 意大利语
    "jp"   : "values-ja",      # 日语
    "kor"  : "values-ko",      # 韩语
    "may"  : "values-ms",      # 马来语
    "nl"   : "values-nl",      # 荷兰语
    "pl"   : "values-pl",      # 波兰语
    "pt"   : "values-pt",      # 葡萄牙语
    "ru"   : "values-ru",      # 俄语
    "th"   : "values-th",      # 泰语
    "tr"   : "values-tr",      # 土耳其语
    "vie"  : "values-vi",      # 越南语
    "cht"  : "values-zh-rHK",  # 中文-香港
    "cht"  : "values-zh-rTW",  # 中文-台湾
}

# 读取 xml 需要翻译的部分
result = get_items_after_last_comment(SOURCE_PATH)
last_comment = result['last_comment']
original = result['items']

map = {}
for code, fileName in baiduCodeMap.items():
    list =[]
    for name, txt in original.items():
        res = translate(txt, code)
        list.append({'name': name, 'txt': res})
    map[fileName] = list
    print(code + " 翻译完成")

for dirName, list in map.items():
    filePath = TARGET_PATH + dirName + "/strings.xml"
    if os.path.exists(filePath):
        append_translated_strings(filePath, last_comment, list)
    else:
        print(filePath + "not exists")