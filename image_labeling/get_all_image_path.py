#encoding=utf-8
import sys
import os
import codecs

reload(sys)
sys.setdefaultencoding("utf-8")

root_path = "/home/younglittlefat/data_mining/mzitu/imgs"

path_list = os.listdir(root_path)
for path in path_list:
    path = os.path.join(root_path, path)
    file_list = os.listdir(path)
    for file_name in file_list:
        if file_name.endswith("jpg"):
            file_path = os.path.join(path, file_name)
            print "%s\t-1" % file_path
