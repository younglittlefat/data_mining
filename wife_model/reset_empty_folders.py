import os
import shutil

folder_list = os.listdir("imgs")
for folder in folder_list:
    full_path = "imgs/" + folder
    sub_list = os.listdir(full_path)
    if len(sub_list) < 2:
        print full_path
        shutil.rmtree(full_path)
        #commands.getstatusoutput("rm -rf %s" % full_path)
