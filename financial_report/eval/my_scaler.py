#encoding=utf-8
import sys

import numpy as np

class MinMaxScaler:

    def __init__(self):
        self.col_min = []
        self.col_max = []
        self.filter_set = None


    def fit_transform(self, data_list, filter_set = None):
        """

        """
        self.filter_set = filter_set
        print_info = False
        def _value_scale_func(value, min_val, max_val):
            if value == "None":
                return float(2.0)
            else:
                v = float(value)
                return (v - min_val) / (max_val - min_val)
            

        # 获取列向量
        raw_col_vector = []
        for col_idx in range(len(data_list[0])):
            raw_col_vector.append([row[col_idx] for row in data_list])

        new_col_vector = []
        # 找出最大最小值
        for idx, col in enumerate(raw_col_vector):
            if print_info:
                print len(col)
            all_num_list = map(float, filter(lambda x:x != "None", col))
            now_min_val = min(all_num_list)
            now_max_val = max(all_num_list)
            self.col_min.append(now_min_val)
            self.col_max.append(now_max_val)
            if self.filter_set is None or idx not in self.filter_set:
                new_col = map(lambda x:_value_scale_func(x, now_min_val, now_max_val), \
                    col)
            else:
                new_col = map(float, col)
            if print_info:
                print "col_min:"
                print self.col_min
                print "col_max:"
                print self.col_max
            new_col_vector.append(new_col)

        # 还原为行向量并返回
        return np.array(new_col_vector, dtype = np.float).T


    def transform(self, data_list):
        """

        """
        print_info = False
        def _value_scale_func(value, min_val, max_val):
            if value == "None":
                return float(-1)
            else:
                v = float(value)
                return (v - min_val) / (max_val - min_val)
            

        # 获取列向量
        raw_col_vector = []
        for col_idx in range(len(data_list[0])):
            raw_col_vector.append([row[col_idx] for row in data_list])

        new_col_vector = []
        # 找出最大最小值
        for idx, col in enumerate(raw_col_vector):
            if print_info:
                print len(col)
            now_min_val = self.col_min[idx]
            now_max_val = self.col_max[idx]
            if self.filter_set is None or idx not in self.filter_set:
                new_col = map(lambda x:_value_scale_func(x, now_min_val, now_max_val), \
                    col)
            else:
                new_col = map(float, col)
            new_col_vector.append(new_col)

        # 还原为行向量并返回
        return np.array(new_col_vector, dtype = np.float).T

if __name__ == "__main__":
    pass
