#encoding=utf-8
import sys
import os
import codecs
import time
import logging

#from digger.a_shares import ASharesFinanceReportDigger
#from digger.nasdaq_shares import AmericanSharesFinanceReportDigger
from digger.stock_history_price import Download_HistoryStock

reload(sys)
sys.setdefaultencoding("utf-8")
logging.basicConfig(level=logging.DEBUG,
    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s  %(message)s',
    datefmt='%%d %b %Y %H:%M:%S')


def download_history_stock_price(output_dir, stock_name_id_dir):
    now_month = time.strftime('%Y%m',time.localtime(time.time()))
    # 创建当月股价目录
    if not os.path.exists(os.path.join(output_dir, now_month)):
        os.mkdir(os.path.join(output_dir, now_month))
    output_dir = os.path.join(output_dir, now_month)
    # 读取已存在的当月股价文件列表
    existed_stockid_dict = {}
    for stock_id_filename in os.listdir(output_dir):
        stock_id = stock_id_filename.split(".")[0]
        existed_stockid_dict[stock_id] = None
    # 获取当月股票名称-id文件路径
    now_month_stock_id_path = os.path.join(stock_name_id_dir, now_month)
    if not os.path.exists(now_month_stock_id_path):
        logging.error("Stock name-id file doesn't exist! Now exiting...")
        return

    valid_stockid_list = []
    with codecs.open(now_month_stock_id_path, "r", "utf-8", "ignore") as f:
        for line in f:
            temp = line.strip().split("\t", 2)
            stock_id = temp[1]
            if stock_id in existed_stockid_dict:
                continue
            dh = Download_HistoryStock(output_dir, stock_id)
            dh.run()



if __name__ == "__main__":
    #data_path = "./american_data"
    #data_path = "./china_data"
    #config_path = "./config/main_config.json"
    #a_shares = ASharesFinanceReportDigger()
    #amer = AmericanSharesFinanceReportDigger(data_path, config_path)
    stock_price_output_dir = "data/stock_price"
    stock_name_id_path = "data/stock_list"
    download_history_stock_price(stock_price_output_dir, stock_name_id_path)
