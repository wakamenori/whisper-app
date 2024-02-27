import json
from urllib import request
import os

APPID = os.getenv("YAHOO_APP_ID")
URL = "https://jlp.yahooapis.jp/FuriganaService/V2/furigana"


def format_furigana(response: dict) -> str:
    """
    Yahoo!日本語形態素解析APIの結果を整形する
    Args:
        response (dict): Yahoo!日本語形態素解析APIの結果
    Returns:
        str: 整形された結果
    """
    formatted = ""
    for word in response["result"]["word"]:
        if "furigana" in word:
            # formatted += word["furigana"]
            formatted += "{}({})".format(word["surface"], word["furigana"])
        else:
            formatted += word["surface"]
    return formatted


def get_furigana(query: str) -> dict:
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Yahoo AppID: {}".format(APPID),
    }
    param_dic = {
        "id": "1234-1",
        "jsonrpc": "2.0",
        "method": "jlp.furiganaservice.furigana",
        "params": {"q": query, "grade": 1},
    }
    params = json.dumps(param_dic).encode()
    req = request.Request(URL, params, headers)
    with request.urlopen(req) as res:
        body = res.read()
    data = json.loads(body.decode())

    return data


def add_furigana_to_text(text: str) -> str:
    furigana = get_furigana(text)
    if "error" in furigana:
        print("Error: {}".format(furigana["error"]["message"]))
        return text
    return format_furigana(furigana)
