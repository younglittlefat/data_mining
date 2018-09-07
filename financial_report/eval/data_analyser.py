#encoding=utf-8
import sys
import os
import codecs
import random
import pickle

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.feature_selection import chi2
from sklearn.feature_selection import mutual_info_classif
from sklearn.feature_selection import f_classif

from my_scaler import MinMaxScaler

reload(sys)
sys.setdefaultencoding("utf-8")

class DataAnalyser:


    def __init__(self, train_file, test_file):
        self.train_file = train_file
        self.test_file = test_file

        self._load_data()


    def _load_data(self):
        """

        """
        self.raw_train_list = []
        self.raw_train_label = []
        self.raw_test_list = []
        self.raw_test_label = []
        with codecs.open(self.train_file, "r", "utf-8", "ignore") as f:
            self.raw_train_list = [temp[2:-1] for temp in map(lambda x:x.strip().split(" "), f.readlines())]
        with codecs.open(self.train_file, "r", "utf-8", "ignore") as f:
            self.raw_train_label = [1 if float(temp[-1]) > 0.15 else 0 for temp in map(lambda x:x.strip().split(" "), f.readlines())]

        print "Length of raw_train:%d" % (len(self.raw_train_list))

        with codecs.open(self.test_file, "r", "utf-8", "ignore") as f:
            self.raw_test_list = [temp[2:-1] for temp in map(lambda x:x.strip().split(" "), f.readlines())]
        with codecs.open(self.test_file, "r", "utf-8", "ignore") as f:
            self.raw_test_label = [1 if float(temp[-1]) > 0.15 else 0 for temp in map(lambda x:x.strip().split(" "), f.readlines())]

        print "Length of raw_test:%d" % (len(self.raw_test_list))


    def normalization(self):
        """
        对数据做归一化
        """
        #self.raw_data_list = self._label_normalization(self.raw_data_list)
        train_scaler = MinMaxScaler()
        norm_train_list = train_scaler.fit_transform(self.raw_train_list)
        norm_test_list = train_scaler.transform(self.raw_test_list)
        #with open("scaler", "wb") as f:
        #    pickle.dump(scaler, f)

        return norm_train_list, norm_test_list


    def get_feature_conf(self):
        """

        """
        with open("../config/feature_conf") as f:
            feature_name_list = [line.strip() for line in f.readlines()]

        feature_name_list.append(u"月份")
        feature_name_list.append(u"当前股价")
        feature_name_list.append(u"公司市值")

        return feature_name_list


    def main(self):
        """

        """
        feature_name_list = self.get_feature_conf()
        print len(feature_name_list)

#        col_vector = []
#        for idx in range(len(self.raw_train_list[0]) - 1):
#            now_col = [float(row[idx]) if row[idx] != "None" else 0.0 for row in self.raw_train_list]
#            col_vector.append(now_col)
#
#        col_vector = np.array(col_vector)
#        std_vector = np.std(col_vector, axis = 1, ddof = 1)
#        print std_vector

        norm_train, norm_test = self.normalization()
        train_label = np.array(self.raw_train_label)
        test_label = np.array(self.raw_test_label)
        norm_train_T = norm_train.T
        # calc stddev
        std_arr = np.std(norm_train_T, axis = 1, ddof = 1)
        std_arr = (std_arr - std_arr.min()) / (std_arr.max() - std_arr.min())
        print std_arr
        # calc F score
        F, pval = f_classif(norm_train, train_label)
        F = (F - F.min()) / (F.max() - F.min())
        print F
        # calc mutual info
        mi = mutual_info_classif(norm_train, train_label)
        mi = (mi - mi.min()) / (mi.max() - mi.min())
        print mi

        #show
        all_arr = np.reshape(np.append(np.append(std_arr, F), mi), (3, -1)).T
        print std_arr
        print F
        print all_arr
        df = pd.DataFrame(all_arr, index = feature_name_list, columns = [u"标准差", u"F score", u"互信息"])
        #df = pd.DataFrame(F, index = feature_name_list)
        df.plot.bar()
        plt.show()
        


if __name__ == "__main__":
    train_file = sys.argv[1]
    test_file = sys.argv[2]
    da = DataAnalyser(train_file, test_file)
    da.main()
