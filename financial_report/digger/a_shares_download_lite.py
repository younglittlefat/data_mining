#encoding=utf-8
import sys
import os
import codecs
import urllib as u
import urllib2 as u2
import json
import logging
import time
import subprocess
from collections import OrderedDict

import requests
import xlrd
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

class ASharesFinanceReportDigger:


    def __init__(self, data_dir, stock_list_dir, config_path):
        self.root_url = None
        self.user_agent = None
        self.host = None
        self.headers = {}
        self.now_month = time.strftime('%Y%m',time.localtime(time.time()))
        self.stock_name_filter_set = set(u"1234567890qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM")
        self.id_stockname_mapping = {}

        self.data_dir = data_dir
        self.stock_list_dir = stock_list_dir
        self.config_path = config_path
        #self.blacklist = "config/china_shares_blacklist"

        self.latest_insuff_report_date = None

        # 创建当天财报目录
        if not os.path.exists(os.path.join(self.data_dir, self.now_month)):
            os.mkdir(os.path.join(self.data_dir, self.now_month))
        self.data_dir = os.path.join(self.data_dir, self.now_month)

        self.load_config()
    

    def load_config(self):
        """

        """

        with open(self.config_path) as f:
            j = json.loads("".join(f.readlines()))
            self.stock_root_url = j["stock_root_url"]
            self.financial_root_url = j["financial_root_url"]
            self.user_agent = j["User-Agent"]

        if self.user_agent and self.host:
            self.headers["User-Agent"] = self.user_agent
            #self.headers["Host"] = self.host


    def load_stock_id_mapping(self):
        """

        """
        stock_list_path = os.path.join(self.stock_list_dir, self.now_month)
        if not os.path.exists(stock_list_path):
            logging.warn("Stock name-id mapping file doesn't exist, now downloading...")
            self._get_all_stock_id(stock_list_path)

        #with codecs.open(self.blacklist, "r", "utf-8", "ignore") as f:
        #    blacklist_dict = {line.strip().split("_")[0] for line in f.readlines()}

        self.id_stockname_mapping = {}
        with codecs.open(stock_list_path, "r", "utf-8", "ignore") as f:
            for line in f:
                temp = line.strip().split("\t")
                #if temp[1] in blacklist_dict:
                #    continue
                self.id_stockname_mapping[temp[1]] = temp[0]


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
            except Exception as e:
                retry_times += 1
                logging.warn("Error in decoding image url:%s, now retry times:%d" % (url, retry_times))
                logging.warn(e)

        if success:
            return res
        else:
            return None


    def _request_url_with_selenium(self, url):
        """
        如果访问超时则重试最多5次
        """
        success = False
        retry_times = 0
        while success == False and retry_times < 5:
            try:
                self.d.get(url)
                result = self.d.page_source
                success = True
            except:
                retry_times += 1
                logging.warn("Error in decoding image url:%s, now retry times:%d" % (url, retry_times))

        if success:
            return result
        else:
            return None



    def _get_all_stock_id(self, stock_list_path):
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

        f_w = open(stock_list_path, "w")
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
            if u"B股" in stock_name:
                continue
            if u"港股" in stock_name:
                continue 
            self.id_stockname_mapping[stock_id] = stock_name
            f_w.write("%s\t%s\n" % (stock_name, stock_id))
        f_w.close()
        logging.info("Done for getting stock ID.")


    def _decode_one_xls_file(self, file_name, item_date_dict, stock_id, stock_name):
        """

        """
        try:
            x = xlrd.open_workbook(file_name)
        except Exception as e:
            logging.error("Can not open %s_%s %s" % (stock_id, stock_name, file_name))
            return
        x_sheet = x.sheet_by_index(0)

        # get title
        item_list = x_sheet.col_values(0)[2:]
        idx_item_mapping = OrderedDict()
        for idx, item_name in enumerate(item_list):
            idx_item_mapping[idx] = item_name
            item_date_dict[item_name] = OrderedDict()

        col_idx = 1
        # 只在主要指标的解析中赋初值
        if "main" in file_name:
            self.latest_insuff_report_date = None

        while True:
            try:
                date = x_sheet.cell_value(1, col_idx).replace("-", "")
            except:
                break
            try:
                int(date)
            except:
                logging.error("Date:%s is invalid!" % date)
                col_idx += 1
                continue
            now_col = x_sheet.col_values(col_idx)[2:]
            insuff_num = 0
            for idx, v in enumerate(now_col):
                true_value = None
                try:
                    true_value = float(v)
                    if abs(true_value) < 0.00000001:
                        true_value = None
                except:
                    if "%" in v:
                        true_value = float(v.replace("%", ""))/100.0
                    else:
                        pass
                        #logging.error("Error in decode cell! v=%s" % v)
                if true_value is None:
                    insuff_num += 1
                # 获取距离现在最近的，不完整的年报的日期
                if "main" in file_name and self.latest_insuff_report_date is None and insuff_num >= 2:
                    self.latest_insuff_report_date = date
                belong_name = idx_item_mapping[idx]
                item_date_dict[belong_name][date] = true_value
            col_idx += 1

        #print json.dumps(item_date_dict, ensure_ascii = False, indent = 1)



    def _decode_one_financial_page(self, stock_id, stock_name):
        """
        解析单张财报表
        """
        item_date_dict = OrderedDict() # item-date-value

        # get download url
        #true_url = "http://basic.10jqka.com.cn/%s/finance.html#stockpage" % stock_id
        main_url = "http://basic.10jqka.com.cn/api/stock/export.php?export=main&type=report&code=%s" % stock_id
        debt_url = "http://basic.10jqka.com.cn/api/stock/export.php?export=debt&type=report&code=%s" % stock_id
        benefit_url = "http://basic.10jqka.com.cn/api/stock/export.php?export=benefit&type=report&code=%s" % stock_id

        # download main report
        command = "wget -O %s \"%s\"" % ("main.xls", main_url)
        res = subprocess.Popen(command, shell = True, stdout = subprocess.PIPE, stderr = subprocess.STDOUT)
        res.stdout.readlines()
        # read main report
        self._decode_one_xls_file("main.xls", item_date_dict, stock_id, stock_name)
        os.remove("main.xls")

        # download debt report
        command = "wget -O %s \"%s\"" % ("debt.xls", debt_url)
        res = subprocess.Popen(command, shell = True, stdout = subprocess.PIPE, stderr = subprocess.STDOUT)
        res.stdout.readlines()
        # read debt report
        self._decode_one_xls_file("debt.xls", item_date_dict, stock_id, stock_name)
        os.remove("debt.xls")

        # download benefit report
        command = "wget -O %s \"%s\"" % ("benefit.xls", benefit_url)
        res = subprocess.Popen(command, shell = True, stdout = subprocess.PIPE, stderr = subprocess.STDOUT)
        res.stdout.readlines()
        # read benefit report
        self._decode_one_xls_file("benefit.xls", item_date_dict, stock_id, stock_name)
        os.remove("benefit.xls")


        # 删除信息不足无效的年报
        if self.latest_insuff_report_date is not None:
            for item_name in item_date_dict:
                for date in item_date_dict[item_name]:
                    if int(date) <= int(self.latest_insuff_report_date):
                        item_date_dict[item_name].pop(date)


        if len(item_date_dict) > 0:
            file_path = os.path.join(self.data_dir, "%s_%s" % (stock_id, stock_name))
            with open(file_path, "w") as f:
                out_str = json.dumps(item_date_dict, ensure_ascii = False, indent = 1)
                f.write(out_str)
        return 0



    def get_financial_report(self):
        """

        """

        is_debug = False
        logging.info("Now getting financial report")

        if is_debug:
            stock_id = "601211"
            self._decode_one_financial_page(stock_id, self.id_stockname_mapping[stock_id])
        else:
            for stock_id in self.id_stockname_mapping:
                logging.info("%s\t%s" % (stock_id, self.id_stockname_mapping[stock_id]))
                file_name = "%s_%s" % (stock_id, self.id_stockname_mapping[stock_id])
                file_path = os.path.join(self.data_dir, file_name)
                if os.path.exists(file_path):
                    logging.info("%s exists! Now continue..." % file_name)
                    continue
                ret = self._decode_one_financial_page(stock_id, self.id_stockname_mapping[stock_id])
                if ret < 0:
                    continue



if __name__ == "__main__":
    data_dir = sys.argv[1]
    stock_list_dir = sys.argv[2]
    config_path = sys.argv[3]
    a = ASharesFinanceReportDigger(data_dir, stock_list_dir, config_path)
    a.load_stock_id_mapping()
    #a.get_all_stock_id()
    a.get_financial_report()
