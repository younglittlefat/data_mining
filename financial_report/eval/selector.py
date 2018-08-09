#encoding=utf-8
import sys
import os
import codecs
import json

reload(sys)
sys.setdefaultencoding("utf-8")

class Selector:

    def __init__(self):
        self.begin_year = 20150500
        self.min_report_num = 11
        self.annual_report_month = 12


    def read_file(self, file_path):
        with codecs.open(file_path, "r", "utf-8", "ignore") as f:
            finance_info = json.load(f)

        return finance_info


    def filter_insufficient_report(self, info):
        new_info = {}
        ret = True
        for key in info:
            if int(key) > self.begin_year:
                new_info[key] = info[key]
            if u"净资产收益率-摊薄" not in info[key].keys():
                ret = False

        if len(new_info) < self.min_report_num:
            ret = False

        return ret, new_info


    def filter_annual_ROE(self, info, file_name, need_print = False):
        ret = True
        
        # annual ROE larger than 10%
        for key in info:
            int_key = int(key)
            month = (int_key - int_key/10000*10000) / 100
            if month != self.annual_report_month:
                continue
            if info[key][u"净资产收益率-摊薄"] < 0.18:
                ret = False

        #delete the company which has empty ROE in some months
        for key in info:
            if info[key][u"净资产收益率-摊薄"] is None:
                ret = False
            
        if ret and need_print:
            sort_list = sorted(info.iteritems(), key = lambda x:x[0])
            print file_name.split("/")[-1]
            for year, sub_info in sort_list:
                try:
                    print "\t%s: %.2f%%" % (year, sub_info[u"净资产收益率-摊薄"]*100)
                except Exception as e:
                    print sub_info[u"净资产收益率-摊薄"]
                    print e
   
        return ret

    
    def select_by_require(self, info, file_name):
        
        # choose latest 2 year
        ret, info = self.filter_insufficient_report(info)
        if not ret:
            #print "insufficient report: %s" % file_name
            return
        #print json.dumps(info, ensure_ascii = False, indent = 1)

        # annual ROE
        ret = self.filter_annual_ROE(info, file_name, True)



if __name__ == "__main__":
    selector = Selector()
    info = selector.read_file("../data/201808/000001_平安银行")
    selector.select_by_require(info)
