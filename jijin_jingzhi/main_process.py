# coding: utf-8

from selenium.webdriver.support.ui import WebDriverWait
from selenium import webdriver
from bs4 import BeautifulSoup
from threading import Thread,Lock
import os
import csv

# 下面是利用 selenium 抓取html页面的代码

# 初始化函数
def initSpider():
    #driver = webdriver.PhantomJS(executable_path=r"你phantomjs可执行文件的绝对路径")
    driver = webdriver.Chrome()
    driver.get("http://fund.eastmoney.com/f10/jjjz_110022.html") # 要抓取的网页地址

    # 找到"下一页"按钮,就可以得到它前面的一个label,就是总页数
#    getPage_text = driver.find_element_by_id("pagebar").find_element_by_xpath(
#        "div[@class='pagebtns']/label[text()='下一页']/preceding-sibling::label[1]").get_attribute("innerHTML")
    getPage_text = driver.find_element_by_xpath(
        "//*[@id='pagebar']/div[1]/label[8]/preceding-sibling::label[1]").get_attribute("innerHTML")
    # 得到总共有多少页
    print getPage_text
    total_page = -1
    try:
        total_page = int(getPage_text)
    except:
        pass

    # 返回
    return (driver,total_page)

# 获取html内容
def getData(myrange,driver,lock):
    for x in myrange:
        # 锁住
        lock.acquire()
#        tonum = driver.find_element_by_id("pagebar").find_element_by_xpath(
#            "div[@class='pagebtns']/input[@class='pnum']")  # 得到 页码文本框
        tonum = driver.find_element_by_xpath(
            "//*[@id='pagebar']/div[1]/input[1]")  # 得到 页码文本框
#        jumpbtn = driver.find_element_by_id("pagebar").find_element_by_xpath(
#            "div[@class='pagebtns']/input[@class='pgo']")  # 跳转到按钮
        jumpbtn = driver.find_element_by_xpath(
            "//*[@id='pagebar']/div[1]/input[2]")  # 跳转到按钮

        #tonum.clear()  # 第x页 输入框
        tonum.send_keys(str(x))  # 去第x页
        jumpbtn.click()  # 点击按钮

        # 抓取
        WebDriverWait(driver, 20).until(lambda driver: driver.find_element_by_id("pagebar").find_element_by_xpath("div[@class='pagebtns']/label[@value={0} and @class='cur']".format(x)) != None)

        # 保存到项目中
        with open("data/%s.txt" % x, 'wb') as f:
            f.write(driver.find_element_by_id("jztable").get_attribute("innerHTML").encode('utf-8'))
            f.close()

        # 解锁
        lock.release()


def getPageSingle(total_page, driver):
    for x in range(2,total_page):

        tonum = driver.find_element_by_xpath(
            "//*[@id='pagebar']/div[1]/input[1]")  # 得到 页码文本框
        print tonum
        jumpbtn = driver.find_element_by_xpath(
            "//*[@id='pagebar']/div[1]/input[2]")  # 跳转到按钮

        tonum.clear()  # 第x页 输入框
        tonum.send_keys(str(x))  # 去第x页
        jumpbtn.click()  # 点击按钮

        # 抓取
        WebDriverWait(driver, 20).until(lambda driver: driver.find_element_by_id("pagebar").find_element_by_xpath("div[@class='pagebtns']/label[@value={0} and @class='cur']".format(x)) != None)

        # 保存到项目中
        with open("data/%s.txt" % x, 'wb') as f:
            f.write(driver.find_element_by_id("jztable").get_attribute("innerHTML").encode('utf-8'))
            f.close()


# 开始抓取函数
def beginSpider():
    # 初始化爬虫
    (driver, total_page) = initSpider()
    getPageSingle(total_page, driver)
    # 创建锁
#    lock = Lock()
#
#    r = range(1, int(total_page)+1)
#    step = 10
#    range_list = [r[x:x + step] for x in  range(0, len(r), step)]   #把页码分段
#    thread_list = []
#    for r in  range_list:
#        t = Thread(target=getData, args=(r,driver,lock))
#        thread_list.append(t)
#        t.start()
#    for t in thread_list:
#        t.join() # 这一步是需要的,等待线程全部执行完成

    print "抓取完成"

beginSpider()
