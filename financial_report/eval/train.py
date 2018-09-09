#encoding=utf-8
import sys
import os
import codecs
import random
import pickle
import json

import numpy as np
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.neural_network import MLPClassifier
from sklearn import metrics
#from sklearn.preprocessing import MinMaxScaler

from my_scaler import MinMaxScaler

reload(sys)
sys.setdefaultencoding("utf-8")

class TrainProcess:


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
        self.test_company_name = []
        with codecs.open(self.train_file, "r", "utf-8", "ignore") as f:
            self.raw_train_list = [temp[2:-1] for temp in map(lambda x:x.strip().split(" "), f.readlines())]
        with codecs.open(self.train_file, "r", "utf-8", "ignore") as f:
            self.raw_train_label = [1 if float(temp[-1]) > 0.15 else 0 for temp in map(lambda x:x.strip().split(" "), f.readlines())]

        print "Length of raw_train:%d" % (len(self.raw_train_list))

        with codecs.open(self.test_file, "r", "utf-8", "ignore") as f:
            self.raw_test_list = [temp[2:-1] for temp in map(lambda x:x.strip().split(" "), f.readlines())]
        with codecs.open(self.test_file, "r", "utf-8", "ignore") as f:
            self.test_company_name = [temp[0] for temp in map(lambda x:x.strip().split(" "), f.readlines())]
        with codecs.open(self.test_file, "r", "utf-8", "ignore") as f:
            self.raw_test_label = [1 if float(temp[-1]) > 0.15 else 0 for temp in map(lambda x:x.strip().split(" "), f.readlines())]

        print "Length of raw_test:%d" % (len(self.raw_test_list))


    def feature_cross(self):
        """

        """
        def sub_process(now_list):
            for feat in now_list:
                earning_per_share = feat[0]
                net_asset_per_share = feat[2]
                stock_price = feat[-4]
                net_asset = feat[22]
                net_earning = feat[33]
                total_debt = feat[19]
                # 静态市盈率
                if earning_per_share != "None" and stock_price != "None"and abs(float(earning_per_share) > 1e-7):
                    feat.append(float(stock_price)/float(earning_per_share))
                else:
                    feat.append("None")
                # 当期净资产收益率
                if net_asset != "None" and net_earning != "None" and abs(float(net_asset) > 1e-7):
                    feat.append(float(net_earning)/float(net_asset))
                else:
                    feat.append("None")
                # 市净率
                if stock_price != "None" and net_asset_per_share != "None" and abs(float(net_asset_per_share) > 1e-7):
                    feat.append(float(stock_price)/float(net_asset_per_share))
                else:
                    feat.append("None")
                # 当期总资产收益率
                if net_earning != "None" and net_asset != "None" and total_debt != "None" and abs(float(net_asset)+float(total_debt) > 1e-7):
                    feat.append(float(net_earning) / (float(net_asset)+float(total_debt)))
                else:
                    feat.append("None")


        sub_process(self.raw_train_list)
        sub_process(self.raw_test_list)


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


    def train(self):
        """

        """

        self.feature_cross()

        norm_train, norm_test = self.normalization()
        train_label = np.array(self.raw_train_label)
        test_label = np.array(self.raw_test_label)

        model = GradientBoostingClassifier(verbose = 1, max_depth = 10, n_estimators = 200)
        #model = RandomForestClassifier(verbose = 1, n_estimators = 300, n_jobs = -1)
        #model = MLPClassifier(verbose = True, learning_rate_init = 0.007, tol = 1e-6, hidden_layer_sizes = (30, 15))

        # training
        model.fit(norm_train, train_label)
        result = model.predict(norm_test)
        print metrics.f1_score(test_label, result)


        result = zip(self.test_company_name, result, self.raw_test_label)
        result = filter(lambda x:x[1]>0.5, result)
        for ele in result:
            print " ".join(map(str, ele))

        """
        with open("model", "wb") as f:
            pickle.dump(model, f)
        """

    def eval(self):
        model_path = sys.argv[2]
        scaler_path = sys.argv[3]
        with open(model_path, "rb") as f:
            model = pickle.load(f)
        with open(scaler_path, "rb") as f:
            scaler = pickle.load(f)
        
        self.raw_data_list = scaler.transform(self.raw_data_list)
        feat = map(lambda x:x[:-1], self.raw_data_list)
        label = map(lambda x:x[-1], self.raw_data_list)
        print model.score(feat, label)


if __name__ == "__main__":
    train_path = sys.argv[1]
    test_path = sys.argv[2]
    tp = TrainProcess(train_path, test_path)
    tp.train()
    #tp.eval()
