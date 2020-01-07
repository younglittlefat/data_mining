#encoding=utf-8
import sys
import os
import codecs
import time
import logging

from digger.stock_id_fetcher import StockIdFetcher
from digger.a_shares import ASharesFinanceReportDigger
from digger.nasdaq_shares import AmericanSharesFinanceReportDigger
from digger.stock_history_price import Download_HistoryStock

reload(sys)
sys.setdefaultencoding("utf-8")
logging.basicConfig(level=logging.INFO,
    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s  %(message)s',
    datefmt='%%d %b %Y %H:%M:%S')

logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("connectionpool").setLevel(logging.WARNING)


def download_history_stock_price(output_dir, stock_name_id_path):
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
    if not os.path.exists(stock_name_id_path):
        logging.error("Stock name-id file doesn't exist! Now exiting...")
        return

    valid_stockid_list = []
    with codecs.open(stock_name_id_path, "r", "utf-8", "ignore") as f:
        for line in f:
            temp = line.strip().split("\t", 2)
            stock_name = temp[0]
            stock_id = temp[1]
            if stock_id in existed_stockid_dict:
                logging.info("Duplicated stock_id=%s" % stock_id)
                continue
            logging.info("Now downloading stock_name=%s, stock_id=%s" % (stock_name, stock_id))
            dh = Download_HistoryStock(output_dir, stock_id)
            dh.run()



if __name__ == "__main__":
    # data_path = "./american_data"
    data_path = "/home/younglittlefat/git/data_mining/financial_report/china_data"
    config_path = "/home/younglittlefat/git/data_mining/financial_report/config/main_config.json"
    id_mapping_path = "./config/stock_id_mapping"
    blacklist_path = "/home/younglittlefat/git/data_mining/financial_report/config/china_shares_blacklist"
    # stock_id_fetcher = StockIdFetcher(config_path)
    # stock_id_fetcher.get_all_stock_id()
    # a_shares = ASharesFinanceReportDigger(data_path, config_path, id_mapping_path, blacklist_path)
    # a_shares.get_financial_report()
    # amer = AmericanSharesFinanceReportDigger(data_path, config_path)
    stock_price_output_dir = "/home/younglittlefat/stock_data/price_data"
    stock_name_id_path = "config/stock_id_mapping"
    download_history_stock_price(stock_price_output_dir, stock_name_id_path)
