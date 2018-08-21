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

class ASharesFinanceReportDigger:


    def __init__(self, data_path, config_path, mapping_file_path = None):
        self.root_url = None
        self.user_agent = None
        self.host = None
        self.headers = {}
        self.now_month = time.strftime('%Y%m',time.localtime(time.time()))
        self.stock_name_filter_set = set(u"1234567890qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM")
        self.id_stockname_mapping = {}

        self.data_path = data_path
        self.config_path = config_path
        self.mapping_file_path = mapping_file_path

        # 创建当天财报目录
        if not os.path.exists(os.path.join(self.data_path, self.now_month)):
            os.mkdir(os.path.join(self.data_path, self.now_month))
        self.data_path = os.path.join(self.data_path, self.now_month)

        # selenium设置
        self.d = webdriver.Chrome()
        self.d.set_page_load_timeout(5)
        self.d.set_script_timeout(5)

        self.load_config()
        self.load_stock_id_mapping()
    

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
            #self.headers["Host"] = self.host


    def load_stock_id_mapping(self):
        """

        """
        if not self.mapping_file_path:
            return

        with codecs.open(self.mapping_file_path, "r", "utf-8", "ignore") as f:
            self.id_stockname_mapping = {temp[1]:temp[0] for temp in map(lambda x:x.strip().split("\t"), f.readlines())}


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


    def _finance_info_preprocess(self, finance_info_list):
        """
        对财报数据进行处理，全部转化成数字
        """
        new_list = []
        for ele in finance_info_list:
            num = None
            ele = ele.replace(",", "")
            try:
                num = float(ele)
            except:
                if ele.endswith(u"%"):
                    num = float(ele.strip(u"%"))/100.0
                elif ele.endswith(u"万"):
                    num = float(ele.strip(u"万"))*10000
                elif ele.endswith(u"万亿"):
                    num = float(ele.strip(u"万亿"))*1000000000000
                elif ele.endswith(u"亿"):
                    num = float(ele.strip(u"亿"))*100000000
                elif ele == u"--":
                    num = None
                else:
                    logging.error("Error in process finance info: %s" % json.dumps(finance_info_list, ensure_ascii = False, indent = 2))
                    return []

            new_list.append(num)

        return new_list


    def _decode_left_head(self, soup):
        """
        解析表格的左栏
        """
        logging.info("Begin to decode left t_head...")
        result = []
        report_box = soup.find("div", class_ = "m_box finance i_hover_box", id = "finance")
        if report_box == None:
            logging.info("can not find report box")
            return result
        table_data = report_box.find("div", class_ = "table_data")
        if table_data == None:
            logging.info("can not find table data")
            return result
        left_thead = table_data.find("div", class_ = "left_thead")
        if left_thead == None:
            logging.info("can not find left t_head")
            return result
        # get title
        tbody = left_thead.find("table", class_ = "tbody")
        if tbody == None:
            logging.info("can not find tbody")
            return result
        th_list = tbody.find_all("th")
        for th in th_list:
            result.append(th.string)

        return result


    def _decode_table_data(self, soup, row_name_list):
        """
        解析表格数据
        """
        logging.info("Begin to decode table data...")
        result = OrderedDict()
        date_list = []
        info_list = []
        report_box = soup.find("div", class_ = "m_box finance i_hover_box", id = "finance")
        if report_box == None:
            logging.info("can not find report box")
            return result
        table_data = report_box.find("div", class_ = "table_data")
        if table_data == None:
            logging.info("can not find table data")
            return result
        # get date
        data_tbody = table_data.find("div", class_ = "data_tbody")
        if data_tbody == None:
            logging.info("can not find data t_body")
            return result
        top_thead = data_tbody.find("table", class_ = "top_thead")
        if top_thead == None:
            logging.info("can not find top t_head")
            return result
        div_list = top_thead.find_all("div", class_ = "td_w")
        for div in div_list:
            date = div.string
            if date != None:
                date_list.append(date.replace("-", ""))
            else:
                date_list.append("00000000")
        # fill data
        date_len = len(date_list)
        row_len = len(row_name_list)
        #print "date len:%d, row len:%d" % (date_len, row_len)
        temp_info_list = []
        tbody = data_tbody.find("table", class_ = "tbody")
        if tbody == None:
            logging.info("can not find tbody")
            return result
        tr_list = tbody.find_all("tr")
        rows = 0
        for tr in tr_list:
            date_info_list = []
            td_list = tr.find_all("td")
            for td in td_list:
                date_info_list.append(td.string)
            if len(date_info_list) != date_len:
                logging.info("decode row %d error, length:%d is not equal!" % (rows, len(date_info_list)))
                return result
            temp_info_list.append(date_info_list)
            rows += 1

        if len(temp_info_list) != row_len:
            logging.warning("rows num is not equal!")
            return result

        #print "temp_info_list len:%d" % len(temp_info_list)
        #print json.dumps(temp_info_list, ensure_ascii = False, indent = 2)
        
        # 列为科目（如每股基本收益等），行为年度，如2017-09-30
        info_list = [["" for i in range(row_len)] for _ in range(date_len)]
        #print info_list
        for i in range(date_len):
            for j in range(row_len):
                #print "i:%d, j:%d" % (i, j)
                info_list[i][j] = temp_info_list[j][i]
        #print json.dumps(info_list, ensure_ascii = False, indent = 2)

        for idx, date in enumerate(date_list):
            now_date_info = info_list[idx]
            result[date] = self._finance_info_preprocess(now_date_info)

        #print json.dumps(result, ensure_ascii = False, indent = 2)
        return result



    def _decode_one_financial_page(self, stock_id, stock_name):
        """
        解析单张财报表
        """
        # get true url
        true_url = "http://basic.10jqka.com.cn/%s/finance.html#stockpage" % stock_id

        #d = webdriver.Chrome()
        res = self._request_url_with_selenium(true_url)
        if res == None:
            return -1
        #res = self._request_url(true_url, timeout = 1)
        soup = BeautifulSoup(self.d.page_source, "html.parser")
        #print soup.prettify()

        # 解析表格的左栏
        row_name_list = self._decode_left_head(soup)
        if len(row_name_list) == 0:
            return -1
        #print json.dumps(row_name_list, ensure_ascii = False, indent = 2)

        # 解析表格数据
        finance_data_dict = self._decode_table_data(soup, row_name_list)
        if len(finance_data_dict) == 0:
            return -1


        # 点击进入资产负债表
        self.d.find_element_by_class_name("icons_page").click()



        # 拼装表头和数据
        final_finance_dict = OrderedDict()
        for key in finance_data_dict:
            new_dict = OrderedDict()
            data_list = finance_data_dict[key]
            for idx, row_name in enumerate(row_name_list):
                new_dict[row_name] = data_list[idx]
            final_finance_dict[key] = new_dict
        """
        file_path = os.path.join(self.data_path, "%s_%s" % (stock_id, stock_name))
        with open(file_path, "w") as f:
            output_str = json.dumps(final_finance_dict, ensure_ascii = False, indent = 2)
            f.write(output_str)
        """
        return 0



    def get_financial_report(self):
        """

        """

        is_debug = True
        logging.info("Now getting financial report")

        if is_debug:
            stock_id = "300253"
            self._decode_one_financial_page(stock_id, self.id_stockname_mapping[stock_id])
        else:
            for stock_id in self.id_stockname_mapping:
                print "%s\t%s" % (stock_id, self.id_stockname_mapping[stock_id])
                file_name = "%s_%s" % (stock_id, self.id_stockname_mapping[stock_id])
                file_path = os.path.join(self.data_path, file_name)
                if os.path.exists(file_path):
                    logging.info("%s exists! Now continue..." % file_name)
                    continue
                ret = self._decode_one_financial_page(stock_id, self.id_stockname_mapping[stock_id])
                if ret < 0:
                    continue



    def _decode_one_page(self, url):
        """

        """
        pass


    def decode_pages(self):
        """

        """
        pass


if __name__ == "__main__":
    data_path = sys.argv[1]
    config_path = sys.argv[2]
    mapping_file = sys.argv[3]
    a = ASharesFinanceReportDigger(data_path, config_path, mapping_file)
    a.get_financial_report()
