#encoding=utf-8
import sys
import os
import codecs
import json

reload(sys)
sys.setdefaultencoding("utf-8")

report_path = sys.argv[1]
stockid_file = sys.argv[2]

with codecs.open(report_path, "r", "utf-8", "ignore") as f:
    report_dict = {line.strip() for line in f}

with codecs.open(stockid_file, "r", "utf-8", "ignore") as f:
    for line in f:
        temp = line.strip().split("\t")
        name = temp[1] + "_" + temp[0]
        #print name
        if name not in report_dict:
            print name
