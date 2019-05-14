import sys
import urllib2 as u2
import json

import requests

#url = "http://basic.10jqka.com.cn/api/stock/export.php?export=main&type=report&code=002484"
url = "http://webapi.http.zhimacangku.com/getip?num=10&type=2&pro=&city=0&yys=0&port=1&pack=38408&ts=1&ys=0&cs=1&lb=1&sb=0&pb=4&mr=1&regions="
user_agent = "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:55.0) Gecko/20100101 Firefox/55.0"
headers = {}
headers["User-Agent"] = user_agent
res = requests.get(url, headers)
print res.content
j = json.loads(res.content)
for ele in j["data"]:
    print ele
