#encoding=utf-8
import sys
import os
import codecs
import random
import pickle

import numpy as np
from sklearn.ensemble import GradientBoostingRegressor, RandomForestClassifier
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


    def train(self):
        """

        """
        norm_train, norm_test = self.normalization()
        train_label = np.array(self.raw_train_label)
        test_label = np.array(self.raw_test_label)

        #model = GradientBoostingRegressor(verbose = 1, max_depth = 10, n_estimators = 200, loss = "lad")
        model = RandomForestClassifier(verbose = 1, n_estimators = 300, n_jobs = -1)
        #model = MLPRegressor(verbose = True, hidden_layer_sizes = (30, 15))

        # training
        model.fit(norm_train, train_label)
        print model.score(norm_test, test_label)

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
