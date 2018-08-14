#encoding=utf-8
import sys
import os
import codecs

from digger.a_shares import ASharesFinanceReportDigger
from digger.nasdaq_shares import AmericanSharesFinanceReportDigger
from digger.stock_history_price import Download_HistoryStock

reload(sys)
sys.setdefaultencoding("utf-8")


def download_history_stock_price():
    output_path = sys.argv[1]
    feature_file_path = sys.argv[2]
    valid_stockid_list = []
    with codecs.open(feature_file_path, "r", "utf-8", "ignore") as f:
        for line in f:
            temp = line.strip().split(" ", 2)
            stock_id = temp[0].split("_")[0].encode("utf-8")
            if not stock_id.startswith("3"):
                continue
            dh = Download_HistoryStock(output_path, stock_id)
            dh.run()



if __name__ == "__main__":
    data_path = "./american_data"
    config_path = "./config/american_config.json"
    #a_shares = ASharesFinanceReportDigger()
    #amer = AmericanSharesFinanceReportDigger(data_path, config_path)
    download_history_stock_price()
