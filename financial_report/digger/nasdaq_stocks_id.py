#encoding=utf-8
import sys
import os
import codecs
import urllib as u
import urllib2 as u2
import json
import logging
import time
from collections import OrderedDict

import requests
from bs4 import BeautifulSoup
from selenium import webdriver

reload(sys)
sys.setdefaultencoding("utf-8")
logging.basicConfig(level=logging.DEBUG,
    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s  %(message)s',
    datefmt='%%d %b %Y %H:%M:%S')
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("connectionpool").setLevel(logging.WARNING)

class AmericanStockIDDigger:

    def __init__(self, id_file_path, init_url):
        self.id_file_path = id_file_path
        self.stock_root_url = init_url
        self.stock_id_name_dict = {}

        # selenium设置
        self.d = webdriver.Chrome()
        self.d.set_page_load_timeout(5)
        self.d.set_script_timeout(5)


    def _decode_one_page(self, soup):
        """
        decode single page
        """
        tbody = soup.find("tbody")
        if tbody == None:
            logging.info("can not find tbody")
            return

        tr_list = tbody.find_all("tr")
        if tr_list == None or len(tr_list) == 0:
            logging.info("can not find tr")
            return

        for tr in tr_list:
            a_list = tr.find_all("a", target = "_blank")
            if len(a_list) != 2:
                logging.info("len of list is less than 2")
                continue
            tmp_list = []
            for a in a_list:
                tmp_list.append(a.string.strip())
            self.stock_id_name_dict[tmp_list[0].strip()] = tmp_list[1].strip()


    def get_all_stock_id(self):
        """
        获取所有股票代码
        """
        logging.info("Now getting stock ID...")

        try:
            self.d.get(self.stock_root_url)
            result = self.d.page_source
        except:
            logging.warn("Error in requesting url:%s" % (self.stock_root_url))

        if result is None:
            logging.error("result is empty! url:%s" % (self.stock_root_url))

        soup = BeautifulSoup(result, "html.parser")
        # decode the first page
        self._decode_one_page(soup)

        for i in range(134):
            attemps = 0
            while attemps < 5:
                try:
                    self.d.find_elements_by_class_name("changePage")[-2].click()
                    break
                except:
                    time.sleep(0.5)
                    attemps += 1

            soup = BeautifulSoup(self.d.page_source, "html.parser")
            self._decode_one_page(soup)

        with codecs.open(self.id_file_path, "w", "utf-8", "ignore") as f:
            for key in self.stock_id_name_dict:
                f.write("%s %s\n" % (key, self.stock_id_name_dict[key]))
            

        #f_w = open(self.stock_id_filepath, "w")
        #f_w.close()
        logging.info("Done for getting stock ID.")


if __name__ == "__main__":
    url = "http://q.10jqka.com.cn/usa/detail"
    file_path = "info"
    a = AmericanStockIDDigger(file_path, url)
    a.get_all_stock_id()
