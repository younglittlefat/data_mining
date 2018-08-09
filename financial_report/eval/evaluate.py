#encoding=utf-8
import sys
import os
import codecs
import time

from selector import Selector

class Evaluator:

    def __init__(self):
        self.selector = Selector()
        self.data_dir = "../data/" + time.strftime('%Y%m',time.localtime(time.time()))

        self._read_finance_info_filename()
    

    def _read_finance_info_filename(self):
        self.file_list = map(lambda x:os.path.join(self.data_dir, x), 
            os.listdir(self.data_dir))


    def main_process(self):
        for file_name in self.file_list:
            info = self.selector.read_file(file_name)
            self.selector.select_by_require(info, file_name)



if __name__ == "__main__":
    ev = Evaluator()
    ev.main_process()
