#encoding=utf-8
import sys
import os
import logging

import numpy as np
import pandas as pd


class FeatureExtractor(object):

    def __init__(self):
        self.feat_name = ""
        self.activate_df_names = []

    def get_info(self):
        """

        :return:
        """
        return "feat_name=%s, activate_df_name=%s" % (self.feat_name, ",".join(self.activate_df_names))

    def get_feat_name(self):
        return self.feat_name

    def _check_df_dict_valid(self, df_dict):
        """

        :param df_dict:
        :return:
        """
        for df_name in self.activate_df_names:
            if df_name not in df_dict:
                logging.error("df_name=%s not in df_dict" % df_name)
                return False

        return True

    def get_features(self, df_dict):
        """

        :param df_dict:
        :return:
        """
        return None
