#encoding=utf-8
import sys
import os

from digger.a_shares import ASharesFinanceReportDigger
from digger.nasdaq_shares import AmericanSharesFinanceReportDigger

reload(sys)
sys.setdefaultencoding("utf-8")


if __name__ == "__main__":
    data_path = "./american_data"
    config_path = "./config/american_config.json"
    #a_shares = ASharesFinanceReportDigger()
    amer = AmericanSharesFinanceReportDigger(data_path, config_path)
