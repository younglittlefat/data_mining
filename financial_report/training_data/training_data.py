#encoding=utf-8
import logging
import os
import sys
import time
from multiprocessing import Process

import numpy as np
import pandas as pd

from feature_conf import FinancialFeature
from feature_conf import PriceFeature
import utils

from features.label import Label
from features.net_profit_cut_increase_ratio import NetProfitCutIncreaseRatio


reload(sys)
sys.setdefaultencoding("utf-8")
logging.basicConfig(level=logging.INFO,
    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
    datefmt='%d %b %Y %H:%M:%S')


class TrainingData(object):

    def __init__(self, financial_data_dir, price_data_dir):
        self.financial_data_dir = financial_data_dir
        self.price_data_dir = price_data_dir
        self.feature_extractors = [
            NetProfitCutIncreaseRatio(),
            Label(),
        ]

        self.thread_num = 2

    @staticmethod
    def _load_single_stock_info(data_dir, stock_id, active_feature_names, sep=",", encoding="utf-8"):
        """
        根据股票id读取股票信息，如股价信息、基本面信息等，返回DataFrame
        :param stock_id:
        :return:
            df: 股票数据的DataFrame
        """
        stock_data_path = os.path.join(data_dir, "%s.csv" % stock_id)
        if not os.path.isfile(stock_data_path):
            logging.error("Stock price file of id=%s doesn't exist!" % stock_id)
            return None

        df = pd.read_csv(stock_data_path, sep=sep, encoding=encoding, na_values=["None"])
        # choose the active features
        df = pd.concat([df[feat_name] for feat_name in active_feature_names], axis=1)
        return df

    @staticmethod
    def _get_closest_date_idx_from_date_df(target_date, date_df):
        """
        从date_df中获取距离target_date最近的日期idx
        :param target_date: 当前日期
        :param date_df: 待寻找的日期Series
        :return:
            date_idx: 距离target_date最近的日期idx
        """
        prev_date_idx = 0
        days_num = date_df.shape[0]

        for idx in xrange(days_num):
            now_date = str(date_df.loc[idx])
            days_diff = utils.get_time_diff(now_date, target_date)
            if days_diff <= 0:
                break
            prev_date_idx += 1
        return prev_date_idx

    @staticmethod
    def _get_one_stock_features(stock_id, price_data_dir, financial_data_dir, feature_extractors, output_dir=None):
        """
        获取单支股票的特征，并选择性地落地为文件
        :param stock_id:
        :param price_data_dir:
        :param financial_data_dir:
        :param feature_extractors:
        :param output_dir:
        :return:
        """

        price_df = td._load_single_stock_info(
            price_data_dir, stock_id, PriceFeature.active_feature_name, sep=",", encoding="gbk")
        financial_df = td._load_single_stock_info(
            financial_data_dir, stock_id, FinancialFeature.active_feature_name, sep="|", encoding="utf-8")

        date_df = price_df[u"日期"]
        total_days_num = date_df.shape[0]
        logging.info("total days num=%s" % total_days_num)

        feature_list = []

        for fe in feature_extractors:
            # 创建一个容纳当前特征的array，长度与total_days_num一致
            feat_arr = np.array([np.nan for i in xrange(total_days_num)], dtype=np.float32)

            # 获取提取好的特征DataFrame
            feat_df = fe.get_features({"price": price_df, "finance": financial_df})
            date_series_from_feat_df = feat_df[u"日期"]

            # 遍历每个交易日，获取距离当前交易日的最近的特征
            everyday_feat_val_list = []
            for date_idx in xrange(total_days_num):
                now_date = date_df.loc[date_idx]
                closest_date_idx_from_feat_df = None
                if date_series_from_feat_df.shape[0] == total_days_num:
                    # 如果当前的特征，每行是每个开盘日，就不用一个个去找最近日期的，最近的日期直接就是date_idx
                    closest_date_idx_from_feat_df = date_idx
                else:
                    # 如果当前特征，每行不是每个开盘日，例如每行是每个财报日，就得去找距离date_idx最近的日期
                    closest_date_idx_from_feat_df = \
                        TrainingData._get_closest_date_idx_from_date_df(now_date, date_series_from_feat_df)

                # 获取距离date_idx最近日期的特征
                feat_val = feat_df.loc[closest_date_idx_from_feat_df][fe.get_feat_name()]
                logging.debug("now date=%s, the closest date from feat_df is %s, feature value=%s" %
                              (now_date, date_series_from_feat_df.loc[closest_date_idx_from_feat_df], feat_val))

                everyday_feat_val_list.append(feat_val)

            everyday_feat_df = pd.DataFrame(everyday_feat_val_list, columns=[fe.get_feat_name()])
            feature_list.append(everyday_feat_df)

        total_feature_df = pd.concat([date_df] + feature_list, axis=1)

        if output_dir is not None:
            output_path = os.path.join(output_dir, "%s.csv" % stock_id)
            total_feature_df.to_csv(output_path, sep="|", index=False, na_rep="None")

        logging.info("Done processing stock_id=%s" % stock_id)

    @staticmethod
    def _read_valid_stock_id_list(price_data_dir, financial_data_dir, training_data_dir, regenerate=False):
        """
        挑选出合法的股票id
        :param price_data_dir:
        :param financial_data_dir:
        :param training_data_dir:
        :param regenerate:
        :return:
        """
        valid_id_file = os.path.join(training_data_dir, "valid_stock_id_list")
        if regenerate or not os.path.isfile(valid_id_file):
            valid_price_stock_id_list, _ = \
                utils.check_if_all_stock_has_active_feat(price_data_dir, PriceFeature.active_feature_name, sep=",",
                                                         encoding="gbk")
            valid_financial_stock_id_list, _ = \
                utils.check_if_all_stock_has_active_feat(financial_data_dir, FinancialFeature.active_feature_name,
                                                         sep="|",
                                                         encoding="utf-8")

            valid_price_stock_id_d = {stock_id: None for stock_id in valid_price_stock_id_list}
            valid_financial_stock_id_d = {stock_id: None for stock_id in valid_financial_stock_id_list}
            valid_stock_id_list = []
            for stock_id in valid_price_stock_id_d:
                if stock_id in valid_financial_stock_id_d:
                    valid_stock_id_list.append(stock_id)

            with open(valid_id_file, "w") as f:
                for stock_id in valid_stock_id_list:
                    f.write("%s\n" % stock_id)
        else:
            with open(valid_id_file, "r") as f:
                valid_stock_id_list = [line.strip() for line in f.readlines()]

        logging.info("valid_stock_id_list size=%s" % len(valid_stock_id_list))
        return valid_stock_id_list

    @staticmethod
    def thread_func(stock_id_list, price_data_dir, financial_data_dir, feature_extractors, training_data_dir):
        """
        线程处理函数，循环遍历每支股票，获取其特征
        :param stock_id_list:
        :param price_data_dir:
        :param financial_data_dir:
        :param feature_extractors:
        :param training_data_dir:
        :return:
        """
        pid = os.getpid()
        logging.info("Start a thread pid=%s, stock_id_list size=%s" % (pid, len(stock_id_list)))
        for stock_id in stock_id_list:
            TrainingData._get_one_stock_features(stock_id, price_data_dir, financial_data_dir, feature_extractors, training_data_dir)
        logging.info("Done processing pid=%s" % pid)

    def write_training_data_with_multi_thread(self, price_data_dir, financial_data_dir, training_data_dir):
        """
        主函数
        :param price_data_dir:
        :param financial_data_dir:
        :param training_data_dir:
        :return:
        """
        is_test = True
        valid_stock_id_list = self._read_valid_stock_id_list(price_data_dir, financial_data_dir, training_data_dir)
        if is_test:
            valid_stock_id_list = valid_stock_id_list[:10]

        # 拆分线程
        num_per_thread = len(valid_stock_id_list) / self.thread_num
        t_list = []
        for i in range(self.thread_num):
            if i == self.thread_num - 1:
                now_list = valid_stock_id_list[i * num_per_thread:]
            else:
                now_list = valid_stock_id_list[i * num_per_thread: (i + 1) * num_per_thread]
            t = Process(target=TrainingData.thread_func,
                        args=(now_list, price_data_dir, financial_data_dir, self.feature_extractors, training_data_dir))
            t_list.append(t)

        for t in t_list:
            t.start()
        for t in t_list:
            t.join()

if __name__ == "__main__":
    financial_data_dir = "/home/younglittlefat/stock_data/financial_data/202001"
    price_data_dir = "/home/younglittlefat/stock_data/price_data/202001"
    training_data_dir = "/home/younglittlefat/stock_data/training_data/202001"
    td = TrainingData(financial_data_dir, price_data_dir)
    # td._get_one_stock_features("600000", price_data_dir, financial_data_dir, td.feature_extractors, training_data_dir)
    td.write_training_data_with_multi_thread(price_data_dir, financial_data_dir, training_data_dir)
