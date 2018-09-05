#encoding=utf-8
import sys
import os
import codecs
import random
import pickle

import numpy as np
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.neural_network import MLPRegressor
from sklearn import metrics
#from sklearn.preprocessing import MinMaxScaler

from my_scaler import MinMaxScaler

class TrainProcess:


    def __init__(self, train_file, test_file):
        self.train_file = train_file
        self.test_file = test_file

        self._load_data()


    def _load_data(self):
        """

        """
        self.raw_train_list = []
        self.raw_test_list = []
        with codecs.open(self.train_file, "r", "utf-8", "ignore") as f:
            for line in f:
                temp = line.strip().split(" ")
                self.raw_train_list.append(temp[2:])

        print "Length of raw_train:%d" % (len(self.raw_train_list))

        with codecs.open(self.test_file, "r", "utf-8", "ignore") as f:
            for line in f:
                temp = line.strip().split(" ")
                self.raw_test_list.append(temp[2:])

        print "Length of raw_test:%d" % (len(self.raw_test_list))


    def _label_normalization(self, data_list):
        """

        """
        label_min = min(map(lambda x:x[-1], data_list))
        label_max = max(map(lambda x:x[-1], data_list))
        print "label min:%.2f" % label_min
        print "label max:%.2f" % label_max
        for feat in data_list:
            feat[-1] = (feat[-1] - label_min) / (label_max - label_min)

        return data_list


    def normalization(self):
        """
        对数据做归一化
        """
        #self.raw_data_list = self._label_normalization(self.raw_data_list)
        train_scaler = MinMaxScaler()
        self.raw_train_list = train_scaler.fit_transform(self.raw_train_list)
        self.raw_test_list = train_scaler.transform(self.raw_test_list)
        #with open("scaler", "wb") as f:
        #    pickle.dump(scaler, f)



    def train(self):
        """

        """
        self.normalization()

        #model = GradientBoostingRegressor(verbose = 1, max_depth = 10, n_estimators = 200, loss = "lad")
        model = RandomForestRegressor(verbose = 1, n_estimators = 100, n_jobs = -1)
        #model = MLPRegressor(verbose = True, hidden_layer_sizes = (30, 15))

        # training
        model.fit(self.raw_train_list[:, :-1], self.raw_train_list[:, -1])
        print model.score(self.raw_test_list[:, :-1], self.raw_test_list[:, -1])

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
