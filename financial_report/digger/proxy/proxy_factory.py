#encoding=utf-8
import sys
import urllib2 as u2
import json
import logging
import time
import random

import requests

logging.basicConfig(level=logging.DEBUG,
    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s  %(message)s',
    datefmt='%d %b %H:%M:%S')

class ProxyFactory:


    def __init__(self):
        self.headers = {}
        self.user_agent = "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:55.0) Gecko/20100101 Firefox/55.0"
        self.headers["User-Agent"] = self.user_agent
        self.ip_pool = []
        self.ip_idx = 0
        
        # 读代理api地址
        with open("address.txt", "r") as f:
            self.api_addr = f.readline().strip()

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


    def _check_ip_available(self):
        """
        查看是否所有ip都失效了，如果是则返回False
        失效标准为失败次数大于等于5
        """
        still_valid = False
        for ip_info in self.ip_pool:
            if ip_info["fail_times"] < 5:
                still_valid = True
                break
        return still_valid


    def _get_new_ips(self):
        """
        获取新的一批IP
        """
        time.sleep(2)
        res = requests.get(self.api_addr, self.headers)
        j = json.loads(res.content)
        print json.dumps(j, ensure_ascii = False)
        for ele in j["data"]:
            new_ip = self._ip_info_maker(ele["ip"], ele["port"], ele["expire_time"])
            logging.info(new_ip)
            self.ip_pool.append(new_ip)


    def get_one_ip(self):
        if not self._check_ip_available():
            logging.info("All ips are unavailable. Now re-fetching ips")
            self.ip_pool = []
            self.ip_idx = 0
            self._get_new_ips()

        get_valid_ip = False
        now_ip = None
        while not get_valid_ip:
            now_ip = self.ip_pool[self.ip_idx]
            self.ip_idx += 1
            if self.ip_idx >= 10:
                self.ip_idx = 0
            if now_ip["fail_times"] < 5:
                logging.info("Now ip:" + json.dumps(now_ip))
                get_valid_ip = True
            else:
                continue
        return now_ip


if __name__ == "__main__":
    pf = ProxyFactory()
    for i in range(500):
        now_ip = pf.get_one_ip()
        if random.random() < 0.5:
            now_ip["fail_times"] += 1
