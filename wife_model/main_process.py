#encoding=utf-8
import sys
import os
import codecs
import urllib as u
import urllib2 as u2
import json
import logging
import time
import re

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver import ActionChains

reload(sys)
sys.setdefaultencoding("utf-8")
logging.basicConfig(level=logging.DEBUG,
    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s  %(message)s',
    datefmt='%%d %b %Y %H:%M:%S')
#logging.getLogger("requests").setLevel(logging.WARNING)

class HousePrice:


    def __init__(self):
        self.root_url = None
        self.user_agent = None
        self.host = None
        self.headers = {}
        self.img_path = ""
        self.pages_list = []
        self.title_set = set()

        self.load_config()
    
    def load_config(self):
        """

        """

        with open("config/main_config.json") as f:
            j = json.loads("".join(f.readlines()))
            self.root_url = j["root_url"]
            self.user_agent = j["User-Agent"]
            self.host = j["Host"]
            self.img_path = j["img_path"]

        if self.user_agent and self.host:
            self.headers["User-Agent"] = self.user_agent
            #self.headers["Host"] = self.host

        self.title_set = set([line for line in os.listdir(self.img_path)])


    def get_all_pages(self):
        """

        """
        logging.info("Now getting all pages...")
        now_page = self.root_url
        while now_page:
            try:
                if len(self.headers) > 0:
                    res = requests.get(now_page, headers = self.headers)
                else:
                    res = requests.get(now_page)
            except:
                logging.error("Error in decoding page:%s" % now_page)
                break
            res.encoding = "gb2312"
            soup = BeautifulSoup(res.text, "html.parser")
            ul_content = soup.find("ul", class_ = "content")
            li_list = ul_content.find_all("li")
            for li in li_list:
                pic_text_div = li.find("div", class_ = "pic_txt")
                title = ""
                href = ""
                try:
                    title = pic_text_div.p.a.string
                except:
                    print "Error in reading title!"
                    print li
                try:
                    href = pic_text_div.p.a["href"]
                except:
                    print "Error in reading href!"
                    print li
                if title != "" and href != "":
                    title = title.replace("/", "")
                    self.pages_list.append((title, href))
            
            # get next page
            try:
                afpage_a = soup.find("a", class_ = "afpage")
                next_page_suffix = afpage_a["href"]
                page_prefix = "http://club.autohome.com.cn"
                now_page = page_prefix + next_page_suffix.lower()
                #now_page = None # debug!!!
            except:
                now_page = None

        debug = False
        if debug:
            for title in self.pages_list:
                print "%s\t%s" % (title, self.pages_list[title])

        logging.info("Pages all done.")


    def _save_img(self, url, save_path, img_no):
        """

        """
        try:
            res = requests.get(url, headers = self.headers)
        except:
            logging.error("Error in decoding image url:%s" % url)
            return
        #time.sleep(0.5)
        file_name = str(img_no) + ".jpg"
        full_path = save_path + "/" + file_name
        with open(full_path, "ab") as f:
            f.write(res.content)


    def _create_folder_for_page(self, folder_path):
        """

        """
        if os.path.exists(folder_path):
            logging.warning("Folder:%s already exists!" % folder_path)
        else:
            logging.info("Create folder:%s" % folder_path)
            os.makedirs(folder_path)


    def _check_folder_complement(self, folder):
        """

        """
        if os.path.exists(folder+"/done"):
            logging.info("folder %s is complete!" % folder)
            return True
        else:
            return False




    def _decode_one_page(self, now_page, folder_path, is_debug = False):
        logging.info("Start decoding page: %s" % now_page)
        res = requests.get(now_page, headers = self.headers)
            #logging.error("Error in decoding page:%s" % now_page)
            #return False
        res.encoding = "gb2312"
        """
        browser.get(now_page)
        logging.info("Waiting for getting page...")
        time.sleep(1)
        logging.info("Waiting done.")
        js="var q=document.documentElement.scrollTop=100" 
        browser.execute_script(js)
        browser.find_element_by_xpath("//*[@id='topic_detail_main']").send_keys(Keys.DOWN)
        soup = BeautifulSoup(browser.page_source, "html.parser")
        """
        soup = BeautifulSoup(res.text, "html.parser")
        tz_figure_div_list = soup.find_all("div", class_ = "tz-figure")
        tz_picture_div_list = soup.find_all("div", class_ = "tz-picture")
        img_no = 0
        for tz_figure_div in tz_figure_div_list:
            #x_loaded_div = tz_figure_div.find("div", class_ = "x-loaded")
            x_loaded_div = tz_figure_div.find("div", class_ = "pic")
            if not x_loaded_div:
                x_loaded_div = tz_figure_div.find("span", class_ = "pic")
            img_wrapper = x_loaded_div.find("img")
            try:
                img_url = img_wrapper["src9"]
            except:
                img_url = img_wrapper["src"]
            if not is_debug:
                logging.info("Now saving image: %d" % img_no)
                self._save_img(img_url, folder_path, img_no)
            img_no += 1

        for tz_figure_div in tz_picture_div_list:
            #x_loaded_div = tz_figure_div.find("div", class_ = "x-loaded")
            x_loaded_div = tz_figure_div.find("div", class_ = "pic")
            if not x_loaded_div:
                x_loaded_div = tz_figure_div.find("span", class_ = "pic")
            img_wrapper = x_loaded_div.find("img")
            try:
                img_url = img_wrapper["src9"]
            except:
                img_url = img_wrapper["src"]
            if not is_debug:
                logging.info("Now saving image: %d" % img_no)
                self._save_img(img_url, folder_path, img_no)
            img_no += 1

        if img_no == 0:
            # old version
            w740_div = soup.find("div", class_ = "w740")
            if not w740_div:
                # maybe deleted
                return True
            span_list = w740_div.find_all("span", class_ = "pic")
            for span in span_list:
                img_wrapper = span.find("img")
                try:
                    img_url = img_wrapper["src9"]
                except:
                    img_url = img_wrapper["src"]
                if not is_debug:
                    logging.info("Now saving image: %d" % img_no)
                    self._save_img(img_url, folder_path, img_no)
                img_no += 1

        if img_no == 0:
            # final way: regex
            img_rgx = re.compile(ur"<img.*?src=\"http://club2\.autoimg\.cn(.*?)\"", re.S)
            img9_rgx = re.compile(ur"<img.*?src9=\"http://club2\.autoimg\.cn(.*?)\"", re.S)
            common_prefix = "http://club2.autoimg.cn"
            all_match = re.findall(img_rgx, res.text)
            all_match9 = re.findall(img9_rgx, res.text)
            for img_url in all_match:
                img_url = common_prefix + img_url
                if not is_debug:
                    logging.info("Now saving image: %d" % img_no)
                    self._save_img(img_url, folder_path, img_no)
                img_no += 1
            for img_url in all_match9:
                img_url = common_prefix + img_url
                if not is_debug:
                    logging.info("Now saving image: %d" % img_no)
                    self._save_img(img_url, folder_path, img_no)
                img_no += 1


        return True


    def debug_page(self):
        url = "http://club.autohome.com.cn/bbs/thread-c-209-65345071-1.html#pvareaid=102410"
        self._decode_one_page(url, 0, True)



    def decode_pages(self):
        """

        """
        #browser = webdriver.Firefox()
        #browser = webdriver.Chrome()
        for page_id, (title, href) in enumerate(self.pages_list):
            # create a folder for this page
            folder_path = self.img_path + "/" + title.replace("/", "")
            self._create_folder_for_page(folder_path)
            # check if this folder was completed
            if self._check_folder_complement(folder_path):
                continue
            # decode this page
            ret = self._decode_one_page(href, folder_path)
            # write a done file
            if ret:
                with open(folder_path + "/done", "w") as f:
                    f.write(" ")


if __name__ == "__main__":
    hs = HousePrice()
    hs.get_all_pages()
    hs.decode_pages()
    #hs.debug_page()
