#encoding=utf-8
import sys
import urllib2 as u2
import json
import logging
import time
import random
from datetime import datetime

import requests

logging.basicConfig(level=logging.DEBUG,
    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s  %(message)s',
    datefmt='%d %b %H:%M:%S')
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("connectionpool").setLevel(logging.WARNING)

class ProxyFactory:


    def __init__(self):
        self.headers = {}
        self.user_agent = "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:55.0) Gecko/20100101 Firefox/55.0"
        self.headers["User-Agent"] = self.user_agent
        self.ip_pool = []
        self.ip_idx = 0
        self.max_failure_times = 1
        
        # 读代理api地址
        #with open("address.txt", "r") as f:
        #    self.api_addr = f.readline().strip()
        self.ip_num = 6
        self.api_addr = "http://webapi.http.zhimacangku.com/getip?num=%s&type=2&pro=&city=0&yys=0&port=1&time=1&ts=1&ys=0&cs=0&lb=1&sb=0&pb=4&mr=1&regions=" % self.ip_num
        #self.api_addr = "http://webapi.http.zhimacangku.com/getip?num=%s&type=2&pro=&city=0&yys=0&port=1&pack=38408&ts=1&ys=0&cs=0&lb=1&sb=0&pb=4&mr=1&regions=" % self.ip_num


        logging.info("API address:%s" % self.api_addr)

        # 获取第一批ip
        self._get_new_ips()


    def _ip_info_maker(self, ip, port, expire_time):
        """
        构造一个基本的IP信息，包含ip，port，过期时间，失败次数        
        """
        d = {}
        d["ip"] = ip
        d["port"] = port
        d["expire_time"] = expire_time
        d["fail_times"] = 0
        return d

    def _check_expire(self, expire_time_str):

        day_str, time_str = expire_time_str.split(" ")
        year, mon, d = day_str.split("-")
        hour, minute, second = time_str.split(":")
        expire_datetime = datetime(int(year), int(mon), int(d), int(hour), int(minute), int(second))
        seconds_to_expire = (expire_datetime - datetime.now()).seconds
        if seconds_to_expire < 60:
            return True
        else:
            return False

    def _check_proxy_valid(self, ip, port):
        is_valid = True

        proxy = "http://%s:%s" % (ip, port)
        try:
            #res = requests.get(url="http://icanhazip.com/", timeout=8, proxies={"http": proxy})
            #returnIP = res.text
            res = requests.get(url="http://basic.10jqka.com.cn/api/stock/export.php?export=benefit&type=report&code=601211", timeout=8, proxies={"http": proxy})
        except:
            is_valid = False
        return is_valid

    def _check_ip_available(self):
        """
        查看是否所有ip都失效了，如果是则返回False
        失效标准为失败次数大于等于5
        """
        still_valid = False
        for ip_info in self.ip_pool:
            if ip_info["fail_times"] < self.max_failure_times:
                still_valid = True
                break
        return still_valid


    def _get_new_ips(self):
        """
        获取新的一批IP
        """
        time.sleep(3)
        res = requests.get(self.api_addr, self.headers)
        j = json.loads(res.content)
        for ele in j["data"]:
            new_ip = self._ip_info_maker(ele["ip"], ele["port"], ele["expire_time"])
            logging.info(new_ip)
            self.ip_pool.append(new_ip)


    def get_one_ip(self):

        get_valid_ip = False
        now_ip = None
        while not get_valid_ip:
            now_ip = self.ip_pool[self.ip_idx]
            self.ip_idx += 1
            if self.ip_idx >= self.ip_num:
                self.ip_idx = 0
            # see if now time was close to the expire time
            is_expired = self._check_expire(now_ip["expire_time"])
            if is_expired:
                if now_ip["fail_times"] < self.max_failure_times:
                    logging.warn("Now ip=%s, seconds to expire time is less than 60s" % (now_ip["ip"]))
                now_ip["fail_times"] += self.max_failure_times
            # check if ip was valid
            is_valid = self._check_proxy_valid(now_ip["ip"], now_ip["port"])
            if not is_valid:
                if now_ip["fail_times"] < self.max_failure_times:
                    logging.warn("Now ip=%s, not valid!!!" % (now_ip["ip"]))
                now_ip["fail_times"] += self.max_failure_times
            if now_ip["fail_times"] < self.max_failure_times:
                get_valid_ip = True
            else:
                if not self._check_ip_available():
                    logging.info("All ips are unavailable. Now re-fetching ips")
                    self.ip_pool = []
                    self.ip_idx = 0
                    self._get_new_ips()
        return now_ip


if __name__ == "__main__":
    pf = ProxyFactory()
    for i in range(290):
        now_ip = pf.get_one_ip()
        if random.random() < 0.5:
            now_ip["fail_times"] += 1
