#encoding=utf-8
import sys
import os
import codecs
import random

from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.neural_network import MLPRegressor
from sklearn import metrics

class TrainProcess:


    def __init__(self, data_file):
        self.data_file = data_file

        self._load_data()


    def _load_data(self):
        """

        """
        self.raw_data_list = []
        with codecs.open(self.data_file, "r", "utf-8", "ignore") as f:
            for line in f:
                temp = line.strip().split(" ")
                try:
                    self.raw_data_list.append(map(float, temp[3:]))
                except:
                    continue

        print "Length of raw_data_list:%d" % len(self.raw_data_list)


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
        self.raw_data_list = self._label_normalization(self.raw_data_list)




    def main(self):
        """

        """
        self.normalization()

        #model = GradientBoostingRegressor(verbose = 1, max_depth = 5, n_estimators = 200, loss = "lad")
        model = RandomForestRegressor(verbose = 1, n_estimators = 150)
        #model = MLPRegressor(verbose = True, hidden_layer_sizes = (30, 15))

        # data process
        random.shuffle(self.raw_data_list)
        test_num = int(0.1 * len(self.raw_data_list))
        train_set = self.raw_data_list[test_num:]
        print len(train_set)
        test_set = self.raw_data_list[:test_num]
        print len(test_set)
        train_feat = map(lambda x:x[:-1], train_set)
        train_label = map(lambda x:x[-1], train_set)
        test_feat = map(lambda x:x[:-1], test_set)
        test_label = map(lambda x:x[-1], test_set)

        # training
        model.fit(train_feat, train_label)
        print model.score(test_feat, test_label)




if __name__ == "__main__":
    data_path = sys.argv[1]
    tp = TrainProcess(data_path)
    tp.main()
