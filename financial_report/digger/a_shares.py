#encoding=utf-8
import sys
import os
import codecs
import json
import logging
import time
from collections import OrderedDict

import requests
from bs4 import BeautifulSoup
from selenium import webdriver

reload(sys)
sys.setdefaultencoding("utf-8")

logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("connectionpool").setLevel(logging.WARNING)
logging.getLogger("webdriver").setLevel(logging.WARNING)


class ASharesFinanceReportDigger(object):

    def __init__(self, data_path, config_path, mapping_file_path=None, blacklist_path=None):
        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s  %(message)s',
                            datefmt='%%d %b %Y %H:%M:%S')
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
        self.blacklist = blacklist_path

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

        with codecs.open(self.blacklist, "r", "utf-8", "ignore") as f:
            blacklist_dict = {line.strip().split("_")[0] for line in f.readlines()}

        self.id_stockname_mapping = {}
        with codecs.open(self.mapping_file_path, "r", "utf-8", "ignore") as f:
            for line in f:
                temp = line.strip().split("\t")
                if temp[1] in blacklist_dict:
                    continue
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
            except Exception as e:
                retry_times += 1
                logging.warn("Error in decoding image url:%s, err=%s, now retry times:%d" % (url, e, retry_times))

        if success:
            return result
        else:
            return None

    def _finance_info_str_to_float(self, finance_info_list):
        """
        对财报数据进行处理，全部转化成数字
        """
        new_list = []
        for idx, ele in enumerate(finance_info_list):
            if idx == 0:
                # 日期
                new_list.append(ele)
                continue
            ele = ele.strip()
            num = None
            if len(ele) == 0:
                new_list.append(num)
            else:
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
                        logging.error("Error in process finance info: %s" % json.dumps(finance_info_list, ensure_ascii = False))
                        num = None

                new_list.append(num)

        return new_list

    def _filter_invalid_row(self, row_name_list, temp_info_list):
        """
        过滤非法的基本面项目（也就是行）

        :param row_name_list: 表格的左栏的行名，如“净利润”，“每股净资产”等
        :param temp_info_list: 存储结果的OrderedDict，key为日期，value为一个list，存储当前日期的所有基本面数据
        :return:
        """
        valid_row_name_list = []
        valid_temp_info_list = []

        for idx, row_name in enumerate(row_name_list):
            now_finance_item_every_date = temp_info_list[idx]
            latest_date_finance_val = now_finance_item_every_date[0]
            if latest_date_finance_val is None:
                continue
            latest_date_finance_val = latest_date_finance_val.strip()
            # 存在当前行没有任何数据的情况
            if len(latest_date_finance_val) == 0:
                # skip the invalid finance item
                continue
            valid_row_name_list.append(row_name)
            valid_temp_info_list.append(now_finance_item_every_date)

        return valid_row_name_list, valid_temp_info_list

    def _decode_left_head(self, soup):
        """
        解析表格的左栏的行名，如“净利润”，“每股净资产”等

        Args:
            soup: BeautifulSoup对象

        Returns:
            result: 结果list，按顺序存储行名
        """
        logging.info("Begin to decode left t_head...")
        result = []
        report_box = soup.find("div", class_ = "m_box finance i_hover_box", id = "finance")
        if report_box is None:
            logging.info("can not find report box")
            return result
        table_data = report_box.find("div", class_ = "table_data")
        if table_data is None:
            logging.info("can not find table data")
            return result
        left_thead = table_data.find("div", class_ = "left_thead")
        if left_thead is None:
            logging.info("can not find left t_head")
            return result
        # get title
        tbody = left_thead.find("table", class_ = "tbody")
        if tbody is None:
            logging.info("can not find tbody")
            return result
        th_list = tbody.find_all("th")
        for th in th_list:
            row_name = th.string
            result.append(row_name)

        return result

    def _decode_table_data(self, soup, row_name_list):
        """
        解析表格数据

        Args:
            soup: BeautifulSoup对象，包含所有网页文字及数据
            row_name_list: 表格行名，如“净利润”，“每股净资产”等，由_decode_left_head函数得到

        Returns:
            row_name_list: 去除了非法基本面项目后的行名列表
            date_finance_val_d: key为财报日，value为当前页面的财报日对应的所有基本面指标数值
        """
        logging.info("Begin to decode table data...")
        date_list = []
        info_list = []
        report_box = soup.find("div", class_ = "m_box finance i_hover_box", id = "finance")
        if report_box is None:
            logging.info("can not find report box")
            return None, None
        table_data = report_box.find("div", class_ = "table_data")
        if table_data is None:
            logging.info("can not find table data")
            return None, None
        # get date
        data_tbody = table_data.find("div", class_ = "data_tbody")
        if data_tbody is None:
            logging.info("can not find data t_body")
            return None, None
        top_thead = data_tbody.find("table", class_ = "top_thead")
        if top_thead is None:
            logging.info("can not find top t_head")
            return None, None
        div_list = top_thead.find_all("div", class_ = "td_w")
        for div in div_list:
            # 由此获取每一个财报日期
            date = div.string
            if date is not None:
                date_list.append(date.replace("-", ""))
            else:
                date_list.append("00000000")
        date_len = len(date_list)

        # 一维数组，数组中的每一项是每一个财报日的所有项目数据
        finance_item_date_list = []
        tbody = data_tbody.find("table", class_="tbody")
        if tbody is None:
            logging.info("can not find tbody")
            return None, None
        tr_list = tbody.find_all("tr")
        rows = 0
        for tr in tr_list:
            # 遍历每一个基本面项目，如净利润
            finance_item_daily_list = []
            td_list = tr.find_all("td")
            for td in td_list:
                # 当前基本面项目（如净利润）的所有财报日的数据
                now_finance_val = td.string
                # 最终加入list
                finance_item_daily_list.append(now_finance_val)
            if len(finance_item_daily_list) == 0:
                # 当前数据行没有任何数据
                continue
            if len(finance_item_daily_list) != date_len:
                logging.info("decode row %d error, length:%d is not equal!" % (rows, len(finance_item_daily_list)))
                return None, None
            finance_item_date_list.append(finance_item_daily_list)
            rows += 1

        if len(finance_item_date_list) != len(row_name_list):
            logging.warning("rows num is not equal! row_name_list len=%s, temp_info_list len=%s" %
                            (len(row_name_list), len(finance_item_date_list)))
            return None, None

        row_name_list, finance_item_date_list = self._filter_invalid_row(row_name_list, finance_item_date_list)

        row_len = len(row_name_list)

        # logging.debug("date_len=%s, row_len=%s" % (date_len, row_len))
        # logging.debug("row_name_list=%s" % json.dumps(row_name_list, ensure_ascii=False))

        date_finance_val_d = OrderedDict()
        # 转换成key为财报日，value为财报日中所有基本面数据列表的dict
        for idx_date, date in enumerate(date_list):
            now_date_finance_info = []
            for idx_item, _ in enumerate(row_name_list):
                now_date_finance_info.append(finance_item_date_list[idx_item][idx_date])
            date_finance_val_d[date] = now_date_finance_info
        # logging.debug("date_finance_val_d=%s" % json.dumps(date_finance_val_d, ensure_ascii=False))

        return row_name_list, date_finance_val_d

    def _merge_all_data(self, row_head_list_list, date_finance_val_d_list):
        """

        :param row_head_list_list: 二维列表，列表中的每一项是每一个页面的基本面项目名的列表
        :param date_finance_val_d_list: date_finance_val_d的列表，包含所有页面的基本面数据信息
        :return:
            final_head_list: 所有基本面项目名的列表
            final_data_list: 二维数组，每一行是每个财报日的所有基本面数据
        """
        final_head_list = []
        final_data_list = []
        col_num_per_page = []
        assert len(row_head_list_list) == len(date_finance_val_d_list)
        table_num = len(row_head_list_list)

        # 获取所有有效的财报日
        date_d = {}
        for date_finance_val_d in date_finance_val_d_list:
            for date in date_finance_val_d.keys():
                date_d[date] = None
        date_list = sorted(date_d.iteritems(), key=lambda x:x[0], reverse=True)
        date_list = map(lambda x: x[0], date_list)
        # logging.debug("final date list=%s" % json.dumps(date_list, ensure_ascii=False))

        # 合并表头
        final_head_list.append(u"日期")
        for row_head_list in row_head_list_list:
            final_head_list += row_head_list
            # 获取每个页面的基本面项目的数量，存在col_num_per_page里
            col_num_per_page.append(len(row_head_list))
        # logging.debug("final head list=%s" % json.dumps(final_head_list, ensure_ascii=False))
        # logging.debug("col_num_per_page=%s" % json.dumps(col_num_per_page))

        # 按时间顺序合并三张表
        for idx_date, date in enumerate(date_list):
            base_col_idx = 1  # 第一列是日期
            table_idx = 0
            now_date_finance_data_list = [None for i in xrange(len(final_head_list))]
            # 第一列是日期
            now_date_finance_data_list[0] = date

            # 主要指标表
            main_table_d = date_finance_val_d_list[table_idx]
            if date not in main_table_d:
                logging.warn("date=%s not in main_table_d" % date)
                continue
            now_date_main_table_val_list = main_table_d[date]
            for idx_now_val, now_val in enumerate(now_date_main_table_val_list):
                # logging.debug("idx_date=%s, idx_now_val=%s, now_val=%s" % (idx_date, idx_now_val, now_val))
                try:
                    now_date_finance_data_list[base_col_idx + idx_now_val] = now_val
                except:
                    logging.error("list index out of range, now_date_finance_data_list len=%s, now_val=%s, "
                                  "base_col_idx=%s, idx_now_val=%s, idx_date=%s" %
                                  (len(now_date_finance_data_list), now_val, base_col_idx, idx_now_val, idx_date))
            # base col idx加至第二张表
            base_col_idx += col_num_per_page[table_idx]
            table_idx += 1

            # 资产负债表
            dept_table_d = date_finance_val_d_list[table_idx]
            if date not in dept_table_d:
                logging.warn("date=%s not in dept_table_d" % date)
                continue
            now_date_dept_table_val_list = dept_table_d[date]
            for idx_now_val, now_val in enumerate(now_date_dept_table_val_list):
                try:
                    now_date_finance_data_list[base_col_idx + idx_now_val] = now_val
                except:
                    logging.error("list index out of range, now_date_finance_data_list len=%s, now_val=%s, "
                                  "base_col_idx=%s, idx_now_val=%s, idx_date=%s" %
                                  (len(now_date_finance_data_list), now_val, base_col_idx, idx_now_val, idx_date))
            # base col idx加至第三张表
            base_col_idx += col_num_per_page[table_idx]
            table_idx += 1

            # 利润表
            profit_table_d = date_finance_val_d_list[table_idx]
            if date not in profit_table_d:
                logging.warn("date=%s not in dept_table_d" % date)
                continue
            now_date_profit_table_val_list = profit_table_d[date]
            for idx_now_val, now_val in enumerate(now_date_profit_table_val_list):
                try:
                    now_date_finance_data_list[base_col_idx + idx_now_val] = now_val
                except:
                    logging.error("list index out of range, now_date_finance_data_list len=%s, now_val=%s, "
                                  "base_col_idx=%s, idx_now_val=%s, idx_date=%s" %
                                  (len(now_date_finance_data_list), now_val, base_col_idx, idx_now_val, idx_date))
            # base col idx加至第四张表
            base_col_idx += col_num_per_page[table_idx]
            table_idx += 1

            # 确认数据列数合法
            assert len(now_date_finance_data_list) == len(final_head_list)

            # 将字符串转为数字
            now_date_finance_data_list = self._finance_info_str_to_float(now_date_finance_data_list)

            # 最后把当前财报日的数据插入总数据表
            final_data_list.append(now_date_finance_data_list)
            # logging.debug("now date=%s, now_date_finance_data_list=%s" %
            #               (date, json.dumps(now_date_finance_data_list, ensure_ascii=False)))

        # logging.debug("final data list=%s" % json.dumps(final_data_list, ensure_ascii=False))

        return final_head_list, final_data_list

    def _decode_one_financial_page(self, stock_id, stock_name):
        """
        解析单张财报表
        """
        # get true url
        true_url = "http://basic.10jqka.com.cn/%s/finance.html#stockpage" % stock_id

        res = self._request_url_with_selenium(true_url)
        if res == None:
            return -1
        soup = BeautifulSoup(self.d.page_source, "html.parser")
        # print soup.prettify()
        # print self.d.page_source

        # 解析表格的左栏
        row_name_list_main = self._decode_left_head(soup)
        if len(row_name_list_main) == 0:
            logging.warn("len(row_name_list_main) == 0, no row names in main financial item")
            return -1

        # 解析“主要指标”页面
        finance_data_dict = OrderedDict()
        row_name_list_main, date_finance_val_d_main = self._decode_table_data(soup, row_name_list_main)
        if row_name_list_main is None or date_finance_val_d_main is None or len(date_finance_val_d_main) == 0:
            return -1
        time.sleep(2)

        # 点击进入资产负债表
        self.d.find_element_by_class_name("icons_page").click()
        time.sleep(2)
        soup = BeautifulSoup(self.d.page_source, "html.parser")
        # 解析表格的左栏
        row_name_list_dept = self._decode_left_head(soup)
        # logging.debug("row_name_list_dept=%s" % json.dumps(row_name_list_dept, ensure_ascii=False))
        if len(row_name_list_dept) == 0:
            return -1
        row_name_list_dept, date_finance_val_d_dept = self._decode_table_data(soup, row_name_list_dept)

        # 点击进入利润表
        self.d.find_element_by_class_name("icons_pie").click()
        time.sleep(2)
        soup = BeautifulSoup(self.d.page_source, "html.parser")
        # 解析表格的左栏
        row_name_list_profit = self._decode_left_head(soup)
        # logging.debug("row_name_list_profit=%s" % json.dumps(row_name_list_profit, ensure_ascii=False))
        if len(row_name_list_profit) == 0:
            return -1
        row_name_list_profit, date_finance_val_d_profit = self._decode_table_data(soup, row_name_list_profit)

        table_head, table_data = self._merge_all_data(
            [row_name_list_main, row_name_list_dept, row_name_list_profit],
            [date_finance_val_d_main, date_finance_val_d_dept, date_finance_val_d_profit]
        )

        file_path = os.path.join(self.data_path, "%s.csv" % stock_id)
        with open(file_path, "w") as f:
            f.write("%s\n" % "|".join(table_head))
            for data_line in table_data:
                f.write("%s\n" % "|".join(map(str, data_line)))
        return 0

    def get_financial_report(self):
        """

        """

        is_debug = False
        logging.info("Now getting financial report")

        if is_debug:
            stock_id = "300253"
            self._decode_one_financial_page(stock_id, self.id_stockname_mapping[stock_id])
        else:
            for stock_id in self.id_stockname_mapping:
                logging.info("%s, %s" % (stock_id, self.id_stockname_mapping[stock_id]))
                file_name = "%s_%s.csv" % (stock_id, self.id_stockname_mapping[stock_id])
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
