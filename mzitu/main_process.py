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
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver import ActionChains

reload(sys)
sys.setdefaultencoding("utf-8")
logging.basicConfig(level=logging.DEBUG,
    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s  %(message)s',
    datefmt='%%d %b %Y %H:%M:%S')

class HousePrice:


    def __init__(self):
        self.root_url = None
        self.user_agent = None
        self.host = None
        self.headers = {}
        self.img_path = ""
        self.pages_list = []
        self.title_set = set()
        #self.driver = webdriver.Chrome()

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
        self.pages_list = [self.root_url]
        try:
            if len(self.headers) > 0:
                res = requests.get(self.root_url, headers = self.headers)
            else:
                res = requests.get(self.root_url)
        except:
            logging.error("Error in decoding page:%s" % self.root_url)
        soup = BeautifulSoup(res.text, "html.parser")
        nav_links_div = soup.find("div", class_ = "nav-links")
        max_page_id = 0
        a_list = nav_links_div.find_all("a", class_ = "page-numbers")
        for a in a_list:
            href = a["href"]
            page_id = int(href.strip("/").split("/")[-1])
            if page_id > max_page_id:
                max_page_id = page_id

        # build pages
        common_prefix = "http://www.mzitu.com/page/"
        for i in range(2, max_page_id+1):
            self.pages_list.append(common_prefix + str(i))



    def _save_img(self, url, save_path, img_no, from_url):
        self.headers["Referer"] = from_url
        self.headers["Accept"] = "*/*"
        self.headers["Accept-Language"] = "h-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3"
        self.headers["Accept-Encoding"] = "gzip, deflate"
        self.headers["Connection"] = "keep-alive"
        try:
            res = requests.get(url, headers = self.headers)
        except:
            logging.error("Error in decoding image url:%s" % url)
            return
        
        #self.driver.get(url)
        #time.sleep(0.5)
        file_name = str(img_no) + ".jpg"
        full_path = save_path + "/" + file_name
        with open(full_path, "wb") as f:
            #f.write(self.driver.page_source)
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




    def _decode_one_page(self, now_page, is_debug = False):

        res = requests.get(now_page, headers = self.headers)
            #logging.error("Error in decoding page:%s" % now_page)
            #return False
        soup = BeautifulSoup(res.text, "html.parser")
        pins_ul = soup.find("ul", id = "pins")
        num = 0
        for li in pins_ul.find_all("li"):
            # get title
            title = ""
            try:
                title = li.find("span").a.string
            except:
                pass
            if title != "":
                folder_path = self.img_path + "/" + title
                if self._check_folder_complement(folder_path):
                    continue
            href = li.a["href"]
            self._decode_one_image_set(href)
            num += 1
            #if num == 2:
            #    break


    def _decode_one_image_set(self, url):
        """

        """
        logging.info("Now decoding %s" % url)
        res = requests.get(url, headers = self.headers)
        soup = BeautifulSoup(res.text, "html.parser")
        content_div= soup.find("div", class_ = "content")
        # get title
        title_h2 = content_div.find("h2", class_ = "main-title")
        title = title_h2.string.replace("/", "")
        if title == "" or not title:
            logging.error("Cant find title in %s" % url)
            return False
        logging.info("title: %s" % title)

        # create folder
        folder_path = self.img_path + "/" + title
        self._create_folder_for_page(folder_path)
        # check if this folder was completed(has done file)
        if self._check_folder_complement(folder_path):
            return

        # get tags
        tags_list = []
        tags_div = content_div.find("div", class_ = "main-tags")
        for a in tags_div.find_all("a"):
            tags_list.append(a.string)
        logging.info("tags: %s" % ", ".join(tags_list))
        # write tags
        tags_file = folder_path + "/tags"
        with open(tags_file, "w") as f:
            for tag in tags_list:
                f.write("%s\n" % tag)

        # get pages
        pages_list = [url]
        pagenavi_div = content_div.find("div", class_ = "pagenavi")
        max_page_id = 0
        for span in pagenavi_div.find_all("span"):
            try:
                page_id = int(span.string)
            except:
                continue
            if page_id > max_page_id:
                max_page_id = page_id
        # build pages list
        common_prefix = url + "/"
        for i in range(2, max_page_id+1):
            pages_list.append(common_prefix + str(i))

        # get every image
        for page_id, now_url in enumerate(pages_list):
            self._decode_one_image(now_url, page_id, folder_path)

        # write done file
        with open(folder_path + "/done", "w") as f:
            f.write(" ")



    def _decode_one_image(self, url, img_id, folder_path):
        """

        """
        try:
            res = requests.get(url, headers = self.headers)
            soup = BeautifulSoup(res.text, "html.parser")
            content_div= soup.find("div", class_ = "content")
            main_image_div = content_div.find("div", class_ = "main-image")
            img_wrapper = main_image_div.find("img")
            img_url = img_wrapper["src"]
            self._save_img(img_url, folder_path, img_id, url)
        except:
            logging.error("Error in decoding one image: %s" % url)

        


    def debug_page(self):
        url = "http://club.autohome.com.cn/bbs/thread-c-209-65345071-1.html#pvareaid=102410"
        self._decode_one_page(url, 0, True)



    def decode_pages(self):
        """

        """
        #browser = webdriver.Firefox()
        #browser = webdriver.Chrome()
        for page_id, href in enumerate(self.pages_list):
            # decode this page
            logging.info("Now decoding page id:%s" % page_id)
            ret = self._decode_one_page(href)


if __name__ == "__main__":
    hs = HousePrice()
    hs.get_all_pages()
    hs.decode_pages()
    #hs.debug_page()
