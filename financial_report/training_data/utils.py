#encoding=utf-8
import os
import logging
from datetime import datetime
from datetime import timedelta

import pandas as pd


def check_if_all_stock_has_active_feat(stock_data_dir, active_feature_names, sep=",", encoding="utf-8"):
    """

    :param stock_data_dir:
    :param active_feature_names:
    :param sep:
    :param encoding:
    :return:
    """
    # check price data first
    valid_stock_id_list = []
    invalid_stock_id_list = []
    data_name_list = os.listdir(stock_data_dir)
    processed_num = 0

    logging.info("Now checking if all stocks has active features, dir=%s" % stock_data_dir)
    for data_name in data_name_list:
        full_path = os.path.join(stock_data_dir, data_name)
        if not os.path.isfile(full_path):
            logging.error("File path of name=%s doesn't exist" % full_path)
            continue
        df = pd.read_csv(full_path, sep=sep, encoding=encoding)
        all_valid = True
        # every column name in DataFrame
        col_name_d = {col_name: None for col_name in df.columns}
        miss_col_name_list = []
        for col_name in active_feature_names:
            if col_name not in col_name_d:
                miss_col_name_list.append(col_name)
                all_valid = False
        stock_id = data_name.split(".")[0]
        if not all_valid:
            invalid_stock_id_list.append(stock_id)
            logging.error("stock_id=%s, not all valid, miss column name=%s" %
                          (stock_id, ",".join(miss_col_name_list)))
        else:
            valid_stock_id_list.append(stock_id)
        processed_num += 1
        if processed_num % 100 == 0:
            logging.info("Check if all stocks has active features, already processed %s" % processed_num)

    return valid_stock_id_list, invalid_stock_id_list


def uniform_time_str_format(time_str):
    """
    将YYYYmmdd格式的时间字串转变成YYYY-mm-dd格式
    :param time_str:
    :return:
    """
    if type(time_str) != type(""):
        time_str = str(time_str)
    if "-" not in time_str:
        time_str = "%s-%s-%s" % (time_str[:4], time_str[4:6], time_str[6:])
    return time_str


def get_time_diff(now_time, dst_time):
    """
    获取now_time和dst_time之间的天数差
    :param now_time: 格式为YYYY-mm-dd
    :param dst_time: 格式为YYYY-mm-dd
    :return:
    """
    # uniform the format of time
    now_time = uniform_time_str_format(now_time)
    dst_time = uniform_time_str_format(dst_time)

    now_time_datetime = datetime.strptime(now_time, "%Y-%m-%d")
    dst_time_datetime = datetime.strptime(dst_time, "%Y-%m-%d")

    return (now_time_datetime - dst_time_datetime).days


def get_dst_timestamp(now_time, diff_days):
    """

    :param now_time: 格式为YYYY-mm-dd
    :param diff_days: 天数差
    :return:
    """
    # uniform the format of time
    now_time = uniform_time_str_format(now_time)

    now_time_datetime = datetime.strptime(now_time, "%Y-%m-%d")
    td = timedelta(days=diff_days)
    return (now_time_datetime + td).strftime("%Y-%m-%d")


if __name__ == "__main__":
    price_dir = "../data/stock_price/202001"
    financial_dir = "../china_data/202001"
    # valid_stock_id_list, invalid_stock_id_list = \
    #     check_if_all_stock_has_active_feat(price_dir, PriceFeature.active_feature_name, sep=",", encoding="gbk")
    # print invalid_stock_id_list
    # valid_stock_id_list, invalid_stock_id_list = \
    #     check_if_all_stock_has_active_feat(financial_dir, FinancialFeature.active_feature_name, sep="|", encoding="utf-8")
    # print invalid_stock_id_list
    # print get_time_diff("2020-01-02", "2020-01-02")
    print get_dst_timestamp("2020-01-02", diff_days=-20)