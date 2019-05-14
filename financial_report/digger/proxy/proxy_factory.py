#encoding=utf-8
import sys
import urllib2 as u2
import json
import logging

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
        
        # 读代理api地址
        with open("address.txt", "r") as f:
            self.api_addr = f.readline().strip()

        logging.info("API address:%s" % self.api_addr)

        # 获取第一批ip
        self._get_new_ips()


    def _ip_info_maker(ip, port, expire_time):
        """
        
        """
        d = {}
        d

    def _get_new_ips(self):
        """
        获取新的一批IP
        """
        new_ip_pool = []
        res = requests.get(self.api_addr, self.headers)
        j = json.loads(res.content)
        for ele in j["data"]:
            new_ip = proxy_tuple(ele["ip"], ele["port"], ele["expire_time"])
            logging.info(new_ip)
            new_ip_pool.append(new_ip)


    def get_one_ip():
        pass


if __name__ == "__main__":
    pf = ProxyFactory()
