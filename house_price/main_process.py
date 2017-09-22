#encoding=utf-8
import sys
import os
import codecs
import urllib as u
import urllib2 as u2
import json
import logging
import time
import datetime

from bs4 import BeautifulSoup

reload(sys)
sys.setdefaultencoding("utf-8")
logging.basicConfig(level=logging.DEBUG,
    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s  %(message)s',
    datefmt='%d %b %Y %H:%M:%S')

class HousePrice:


    def __init__(self):
        self.root_url = None
        self.price_missing = 0
        self.title_missing = 0
        self.house_type_missing = 0
        self.house_orient_missing = 0
        self.house_level_missing = 0
        self.house_area_missing = 0
        self.court_missing = 0
        self.district_missing = 0
        self.address_missing = 0
        self.date = datetime.datetime.now().strftime("%Y%m%d")

        self.result_dict = {}

    
    def load_config(self):
        """

        """

        with open("config/main_config.json") as f:
            j = json.loads("".join(f.readlines()))
            if "root_url" in j:
                self.root_url = j["root_url"]



    def get_todays_all_page_link_from_58(self):
        """
        
        """
        logging.info("Start to get all pages from 58...")
        self.all_page_url = [self.root_url]
        now_page_url = self.root_url
        # get the max page_no
        request = u2.Request(now_page_url)
        res = u2.urlopen(request)
        soup = BeautifulSoup(res.read(), "html.parser")
        pager = soup.find_all("div", class_ = "pager")
        a = pager[0].find_all("a")
        max_page_no = 1
        for ele in a:
            href = ele["href"].rstrip("/")
            page_no = int(href.split("/")[-1][2:])
            if page_no > max_page_no:
                max_page_no = page_no

        # get all pages
        page_prefix = "http://nn.58.com/ershoufang/pn"
        for i in range(2,max_page_no+1):
            self.all_page_url.append(page_prefix + str(i))


    def _check_info_and_record(self, price, title, house_type, house_orient, house_level, house_area, court, district, address):
        """
        检查信息是否缺失
        """
        if price == -1:
            self.price_missing += 1
        if title == "":
            self.title_missing += 1
        if house_type == "":
            self.house_type_missing += 1
        if house_orient == "":
            self.house_orient_missing += 1
        if house_level == "":
            self.house_level_missing += 1
        if house_area <= 0:
            self.house_area_missing += 1
        if court == "":
            self.court_missing += 1
        if district == "":
            self.district_missing += 1
        if address == "":
            self.address_missing += 1
            


    def _decode_price(self, price_div):
        """
        decode the price div
        """
        true_price = -1 
        for i in price_div.find("p", class_ = "sum").strings:
            try:
                true_price = float(i)
                break
            except:
                continue
        if true_price == -1:
            print price_div
        return true_price


    def _decode_house_list_info(self, list_info_div):
        """
        decode the house list info
        """
        title = ""
        house_type = ""
        house_orient = ""
        house_level = ""
        house_area = -1.0
        court = ""
        district = ""
        address = ""
        # get title
        title_h2 = list_info_div.find("h2", class_ = "title")
        for s in title_h2.strings:
            if s == "" or s == " " or s == "\n" or len(s) < 2:
                continue
            title = s.replace("\n", "").replace("\r", "")
            break
        # get other base info
        baseinfo_p_list = list_info_div.find_all("p", class_ = "baseinfo")
        no = 0
        for baseinfo_p in baseinfo_p_list:
            if no == 0:
                info_list = []
                for s in baseinfo_p.strings:
                    if s == "" or s == " " or s == "\n":
                        continue
                    if "室" in s or "厅" in s or "卫" in s:
                        house_type = s.replace(" ", "").replace("\n", "").replace("\r", "")
                    elif "东" in s or "南" in s or "西" in s or "北" in s:
                        house_orient = s.replace(" ", "").replace("\n", "").replace("\r", "")
                    elif "层" in s:
                        house_level = s.replace(" ", "").replace("\n", "").replace("\r", "")
                    elif "㎡" in s:
                        try:
                            house_area = float(s.replace(" ", "").replace("\n", "").replace("\r", "").replace("㎡", ""))
                        except:
                            pass
            else:
                a_list = baseinfo_p.find_all("a")
                info_list = []
                for a in a_list:
                    true_str = a.string.replace(" ", "").replace("\n", "").replace("\r", "")
                    if true_str == "" or true_str == "\n":
                        continue
                    info_list.append(true_str)
                try:
                    court = info_list[0]
                    district = info_list[1]
                    address = info_list[2]
                except:
                    pass
            no += 1

        debug = 0
        if debug == 1:
            print title
            print house_type
            print house_orient
            print house_level
            print house_area
            print court
            print district
            print address
        return (title, house_type, house_orient, house_level, house_area, court, district, address)


    def _decode_one_page(self, now_page):
        """

        """
        req = u2.Request(now_page)
        try:
            res = u2.urlopen(req)
        except:
            logging.info("Can not open page: %s" % now_page)    
        soup = BeautifulSoup(res.read(), "html.parser")
        house_list_wrap = soup.find_all("ul", class_ = "house-list-wrap")
        try:
            li_list = house_list_wrap[0].find_all("li")
        except:
            logging.error("Error! Can not fin house_list_wrap! %s" % now_page)
            return
        for li in li_list:
            # every li is a house info
            pic = li.find("div", class_ = "pic")
            list_info = li.find("div", class_ = "list-info")
            # decode list_info
            title, house_type, house_orient, house_level, house_area, court, district, address = self._decode_house_list_info(list_info)
            # decode price
            price_div = li.find("div", class_ = "price")
            price = self._decode_price(price_div)
            # check the info
            self._check_info_and_record(price, title, house_type, house_orient, house_level, house_area, court, district, address)
            self.result_dict[title] = (price, house_type, house_orient, house_level, house_area, court, district, address)


    def _write_into_file(self):
        """

        """
        file_name = "houseprice_day_" + self.date
        full_path = os.path.join("data", file_name)
        with open(full_path, "w") as f:
            for title in self.result_dict:
                f.write("%s\t%s\n" % (title, "\t".join(map(str,list(self.result_dict[title])))))

    

    def decode_pages(self):
        """

        """
        self.result_dict = {}
        for page in self.all_page_url:
            diff_num = 9999
            while diff_num > 5:
                prev_info_num = len(self.result_dict)
                self._decode_one_page(page)
                now_info_num = len(self.result_dict)
                diff_num = now_info_num - prev_info_num
                logging.info("Done with page: %s, added num:%d" % (page, diff_num))
                #time.sleep(1)

        logging.info("price missing: %d" % self.price_missing)
        logging.info("house type missing: %d" % self.house_type_missing)
        logging.info("house orient missing: %d" % self.house_orient_missing)
        logging.info("house level missing: %d" % self.house_level_missing)
        logging.info("house area missing: %d" % self.house_area_missing)
        logging.info("court missing: %d" % self.court_missing)
        logging.info("district missing: %d" % self.district_missing)
        logging.info("address missing: %d" % self.address_missing)
        
        logging.info("Now write results...")
        self._write_into_file()
        logging.info("Done.")


if __name__ == "__main__":
    hs = HousePrice()
    hs.load_config()
    hs.get_todays_all_page_link_from_58()
    hs.decode_pages()
