#encoding=utf-8
import sys
import json
import logging

import requests
from bs4 import BeautifulSoup

reload(sys)
sys.setdefaultencoding("utf-8")
logging.basicConfig(level=logging.DEBUG,
    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s  %(message)s',
    datefmt='%%d %b %Y %H:%M:%S')
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("connectionpool").setLevel(logging.WARNING)


class StockIdFetcher:
    def __init__(self, config_path):
        self.root_url = None
        self.user_agent = None
        self.host = None
        self.headers = {}
        self.stock_name_filter_set = set(u"1234567890qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM")
        self.id_stockname_mapping = {}

        self.config_path = config_path

        self.load_config()

    def load_config(self):
        """

        """

        with open(self.config_path) as f:
            j = json.loads("".join(f.readlines()))
            self.stock_root_url = j["stock_root_url"]
            self.financial_root_url = j["financial_root_url"]
            self.user_agent = j["User-Agent"]
            self.stock_id_filepath = j["stock_id_filepath"]

        if self.user_agent and self.host:
            self.headers["User-Agent"] = self.user_agent

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

    def get_all_stock_id(self):
        """
        获取所有股票代码
        """
        logging.info("Now getting stock ID...")

        res = self._request_url(self.stock_root_url)
        if res == None:
            return

        soup = BeautifulSoup(res.content.decode("gb2312", "replace"), "html.parser")
        div_quotesearch = soup.find("div", id = "quotesearch")
        if div_quotesearch == None:
            logging.error("Can not find quote search div!")
            exit(1)
        li_list = div_quotesearch.find_all("li")

        f_w = open(self.stock_id_filepath, "w")
        for li in li_list:
            a = li.find("a")
            raw_txt = a.string
            raw_txt = raw_txt.strip("()（）").replace("(", " ").replace("（", " ")
            try:
                stock_name, stock_id = raw_txt.split(" ")
            except:
                continue
            name_set = set(stock_name)
            # some filter
            if len(name_set - self.stock_name_filter_set) == 0:
                continue
            if u"基金" in stock_name:
                continue
            if u"ETF" in stock_name:
                continue
            if u"ST" in stock_name:
                continue
            self.id_stockname_mapping[stock_id] = stock_name
            f_w.write("%s\t%s\n" % (stock_name, stock_id))
        f_w.close()
        logging.info("Done for getting stock ID.")