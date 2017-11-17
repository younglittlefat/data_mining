#encoding=utf-8
import sys
import os
import codecs
import urllib as u
import urllib2 as u2
import json
import logging
import time

import requests
from bs4 import BeautifulSoup
#from selenium import webdriver
#from selenium.webdriver.common.keys import Keys
#from selenium.webdriver.support.ui import WebDriverWait
#from selenium.webdriver import ActionChains

reload(sys)
sys.setdefaultencoding("utf-8")
logging.basicConfig(level=logging.DEBUG,
    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s  %(message)s',
    datefmt='%%d %b %Y %H:%M:%S')
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("connectionpool").setLevel(logging.WARNING)

class FundInfoDigging:


    def __init__(self):
        self.root_url = None
        self.user_agent = None
        self.host = None
        self.headers = {}
        self.all_fund_pages = []

        self.load_config()
    
    def load_config(self):
        """

        """

        with open("config/main_config.json") as f:
            j = json.loads("".join(f.readlines()))
            self.root_url = j["root_url"]
            self.user_agent = j["User-Agent"]

        if self.user_agent and self.host:
            self.headers["User-Agent"] = self.user_agent
            #self.headers["Host"] = self.host


    def _request_url(self, url):
        """
        use requests module to request a url, return a response
        """
        success = False
        retry_times = 0
        while success == False and retry_times < 5:
            try:
                if len(self.headers) > 0:
                    res = requests.get(url, headers = self.headers, timeout = 5)
                else:
                    res = requests.get(url, timeout = 5)
                success = True
            except:
                retry_times += 1
                logging.warn("Error in decoding image url:%s, now retry times:%d" % (url, retry_times))

        if success:
            return res
        else:
            return None


    def get_all_pages(self):
        """

        """
        logging.info("Now getting all pages...")

        res = self._request_url(self.root_url)
        soup = BeautifulSoup(res.content.decode("gb2312", "replace"), "html.parser")
        ul_num_right_list = soup.find_all("ul", class_ = "num_right")
        for each_ul in ul_num_right_list:
            if each_ul == None:
                continue
            all_li_list = each_ul.find_all("li")
            for each_li in all_li_list:
                if each_li == None:
                    continue
                first_a = each_li.find("a")
                if first_a == None:
                    continue
                if "href" in first_a.attrs:
                    self.all_fund_pages.append(first_a["href"])
        logging.info("Done for gettint all pages. num of page:%d" % len(self.all_fund_pages))


    def _decode_one_page(self, url):
        """

        """
        logging.info("Now decoding page: %s" % url)
        res = self._request_url(url)
        if res == None:
            logging.error("timeout in decoding page:%s" % url)
            return 1

        soup = BeautifulSoup(res.content, "html.parser")

        # decode title
        div_fundDetail_tit = soup.find("div", "fundDetail-tit")
        if div_fundDetail_tit == None:
            logging.error("page %s doesn't have title div!")
            return 1
        div_title = div_fundDetail_tit.find("div")
        if div_title == None:
            logging.error("page %s doesn't have title div!")
            return 1
        fund_name = ""
        for s in div_title.strings:
            fund_name = s
            break   # get first string
        if fund_name == "":
            logging.error("page %s title is empty!")
            return 1
        print fund_name

        # get net value






        return 0


    def decode_pages(self):
        """

        """
        for page_id, href in enumerate(self.all_fund_pages):
            # decode this page
            ret = self._decode_one_page(href)
            break


if __name__ == "__main__":
    fig = FundInfoDigging()
    fig.get_all_pages()
    fig.decode_pages()
    #hs.debug_page()
