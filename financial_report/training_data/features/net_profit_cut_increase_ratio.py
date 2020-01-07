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


class NetProfitCutIncreaseRatio(FeatureExtractor):

    def __init__(self):
        super(NetProfitCutIncreaseRatio, self).__init__()
        self.feat_name = u"扣非净利润同比增长率"
        self.activate_df_names = ["finance"]

    def get_features(self, df_dict):
        """

        :param df_dict: 原始数据DataFrame的字典
        :return:
            feature_df: 特征的DataFrame
        """
        if not self._check_df_dict_valid(df_dict):
            return None
        df = df_dict[self.activate_df_names[0]]
        target_df = pd.concat([df[u"日期"], df[self.feat_name]], axis=1)
        return target_df