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
#from selenium import webdriver

reload(sys)
sys.setdefaultencoding("utf-8")
logging.basicConfig(level=logging.DEBUG,
    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s  %(message)s',
    datefmt='%%d %b %Y %H:%M:%S')
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("connectionpool").setLevel(logging.WARNING)

base_url = "http://emweb.securities.eastmoney.com/CompanySurvey/CompanySurveyAjax?code="

class CategoryInAShares:

    def __init__(self, report_dir, cate_dir):
        self.now_month = time.strftime('%Y%m',time.localtime(time.time()))
        self.report_dir = os.path.join(report_dir, self.now_month)
        self.cate_dir = cate_dir
        self.headers = {}

        # 创建当天目录
        if not os.path.exists(os.path.join(self.cate_dir, self.now_month)):
            os.mkdir(os.path.join(self.cate_dir, self.now_month))
        self.cate_dir = os.path.join(self.cate_dir, self.now_month)


    def _request_url(self, url, timeout = 5):
        """
        use requests module to request a url, return a response
        """
        success = False
        retry_times = 0
        while success == False and retry_times < 5:
            try:
                if len(self.headers) > 0:
                    res = requests.get(url, headers = self.headers, timeout = timeout)
                else:
                    res = requests.get(url, timeout = timeout)
                success = True
            except:
                retry_times += 1
                logging.warn("Error in decoding image url:%s, now retry times:%d" % (url, retry_times))

        if success:
            return res
        else:
            return None


    def _get_cate(self, stock_id):
        """

        """
        sh_url = base_url + "SH" + stock_id
        sz_url = base_url + "SZ" + stock_id

        # get sh first
        res = self._request_url(sh_url)
        print res.content["status"]
        #print res.content.decode("gb2312", "replace")
        # get sz last
        res = self._request_url(sz_url)
        #print res.content.decode("gb2312", "replace")
        print res.content["status"]


    def main_process(self):
        if not os.path.exists(self.report_dir):
            logging.error("You should get the financial report today first!")
            return

        file_list = os.listdir(self.report_dir)
        for file_name in file_list:
            try:
                stock_id, name = file_name.strip().split("_")
            except:
                logging.error("Error in split %s" % file_name)
                continue
            print file_name
            self._get_cate(stock_id)
            break


if __name__ == "__main__":
    report_dir = sys.argv[1]
    cate_dir = sys.argv[2]
    cias = CategoryInAShares(report_dir, cate_dir)
    cias.main_process()
