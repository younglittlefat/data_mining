#encoding=utf-8
import sys
import os
import logging
import math

import numpy as np
import pandas as pd

from feature_extractor import FeatureExtractor
sys.path.append("..")
import utils


class Label(FeatureExtractor):

    def __init__(self):
        super(Label, self).__init__()
        self.feat_name = "Label"
        self.activate_df_names = ["price"]

    def get_features(self, df_dict):
        """

        :param df_dict: 原始数据DataFrame的字典
        :return:
            feature_df: 特征的DataFrame
        """
        if not self._check_df_dict_valid(df_dict):
            return None
        df = df_dict[self.activate_df_names[0]]

        # 如果持有days_hold这么多天，涨幅会超过10%的股票，其label定义为1
        days_hold = 30
        price_up_per = 0.1
        # 缓冲天数，判断days_hold天内涨幅是否满足预期，其天数区间为[0 + buffer_days, days_hold]，以防异常性暴涨行为
        buffer_days = 2

        row_num = df.shape[0]
        label_arr = np.array([np.nan for i in xrange(row_num)], dtype=np.float32)

        prev_idx = 0
        for i in xrange(row_num):

            now_date = df.loc[i, u"日期"]
            # 找出days_hold天前最近的一个交易日
            while prev_idx < row_num:
                prev_date = df.loc[prev_idx, u"日期"]
                days_diff = utils.get_time_diff(now_date, prev_date)
                if days_diff >= days_hold:
                    break
                prev_idx += 1
            logging.debug("i=%s, prev_idx=%s" % (i, prev_idx))
            if prev_idx == row_num:
                # 无法找到更往前的数据了
                break
            # 判断从prev_date到now_date期间股价涨幅有没有超过price_up_per
            price_at_begin = df.loc[prev_idx, u"收盘价"]
            if math.fabs(price_at_begin) < 1e-5:
                # price now is abnormal, set label to 0
                label_arr[prev_idx] = 0
                continue
            raise_enough = False
            for t in xrange(buffer_days, prev_idx - i + 1, 1):
                history_date = df.loc[prev_idx - t, u"日期"]
                history_price = df.loc[prev_idx - t, u"收盘价"]
                logging.debug("t=%s, history_date=%s, history_price=%s" % (t, history_date, history_price))
                if history_price / price_at_begin - 1 >= price_up_per:
                    raise_enough = True
                    logging.debug("Find a point! prev_idx=%s, start_date=%s, point_date=%s, start_price=%s, point_price=%s" %
                                  (prev_idx, df.loc[prev_idx, u"日期"], history_date, price_at_begin, history_price))
                    break

            if raise_enough:
                label_arr[prev_idx] = 1
            else:
                label_arr[prev_idx] = 0

        label_df = pd.DataFrame(label_arr, columns=[self.feat_name])
        label_date_df = pd.concat([df[u"日期"], label_df], axis=1)
        return label_date_df