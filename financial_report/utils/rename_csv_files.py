import os
import shutil

raw_data_dir = "../china_data/202001"
new_data_dir = "../china_data/202001_new"

filename_list = os.listdir(raw_data_dir)
for filename in filename_list:
    filepath = os.path.join(raw_data_dir, filename)
    stock_id = filename.split(".")[0].split("_")[0]
    new_name = "%s.csv" % stock_id
    new_path = os.path.join(new_data_dir, new_name)
    shutil.copy(filepath, new_path)