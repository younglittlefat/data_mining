#encoding=utf-8
import sys
import os
import json
import codecs
import csv
from datetime import datetime
from datetime import timedelta

reload(sys)
sys.setdefaultencoding("utf-8")


class FeatureSelector:

    def __init__(self, reports_dir, feature_conf, stock_price_dir, feature_output):
        self.reports_dir = reports_dir
        self.feature_conf = feature_conf
        self.stock_price_dir = stock_price_dir
        self.feature_output = feature_output
        self.f_out = open(self.feature_output, "w")
        # read feature conf
        self._read_feature_conf()


    def _read_feature_conf(self):
        """

        """
        self.feature_mapping = {}
        with codecs.open(self.feature_conf, "r", "utf-8", "ignore") as f:
            for line in f:
                name, idx = line.strip().split(" ")
                self.feature_mapping[name] = int(idx)

        print ""
        print json.dumps(sorted(self.feature_mapping.iteritems(),
            key = lambda x:x[1]), ensure_ascii = False)
        print ""


    def _get_diff_days(self, date1, date2):
        """
        
        """
        date1 = int(date1)
        date2 = int(date2)
        before = datetime(date1/10000, (date1-date1/10000*10000)/100, 
            date1-date1/100*100)
        after = datetime(date2/10000, (date2-date2/10000*10000)/100, 
            date2-date2/100*100)
        return (after-before).days


    def _check_one_report_integrity(self, info_dict):
        """

        """
        incomplete_num = 0
        for key in info_dict:
            if info_dict[key] == None:
                incomplete_num += 1

        if incomplete_num > 2:
            return False
        else:
            return True


    def _get_longest_consecutive_period(self, raw_info):
        """

        """
        begin_day = int(raw_info[0][0])
        end_day = -1
        for idx in range(len(raw_info)-1):
            date_before = raw_info[idx][0]
            date_after = raw_info[idx+1][0]
            if not self._check_one_report_integrity(raw_info[idx][1]):
                begin_day = int(raw_info[idx+1][0])
                end_day = -1
                continue
            try:
                diff_days = self._get_diff_days(date_before, date_after)
            except:
                begin_day = int(raw_info[idx+1][0])
                end_day = -1
                continue
                
            if diff_days < 100:
                end_day = int(raw_info[idx+1][0])
            else:
                begin_day = int(raw_info[idx+1][0])
                end_day = -1

        date_list = []
        for date, _ in raw_info:
            if int(date) >= begin_day and int(date) <= end_day:
                date_list.append(int(date))

        return date_list


    def _get_stock_price_change(self, stock_id, begin_date, end_date):
        """
        获取某公司特定时间段的股票涨跌幅
        """
        # 股价区间均推迟1个月
        before = datetime(begin_date/10000, (begin_date-begin_date/10000*10000)/100,
            begin_date-begin_date/100*100)
        after = datetime(end_date/10000, (end_date-end_date/10000*10000)/100,
            end_date-end_date/100*100)

        file_path = os.path.join(self.stock_price_dir, stock_id + ".csv")
        f = open(file_path, "rb")
        info_list = list(csv.reader(f))[1:]
        self.date_price_dict = {l[0].encode("utf-8"):[float(l[3]), float(l[-2])] for l in info_list}
        #print json.dumps(map(lambda x:x.decode("gbk"), info_list[0]), ensure_ascii = False)

        # 找到开盘的一天
        for i in range(8):
            days_interval = timedelta(days = 30+i)
            delay_before = (before + days_interval).strftime("%Y-%m-%d")
            if delay_before in self.date_price_dict:
                break
        for i in range(8):
            days_interval = timedelta(days = 30+i)
            delay_after = (after + days_interval).strftime("%Y-%m-%d")
            if delay_after in self.date_price_dict:
                break
        for i in range(8):
            days_interval = timedelta(days = i)
            valid_begin_date = (before + days_interval).strftime("%Y-%m-%d")
            if valid_begin_date in self.date_price_dict:
                break

        # 
        if delay_before not in self.date_price_dict or \
            delay_after not in self.date_price_dict or \
            valid_begin_date not in self.date_price_dict:
            return None, None

        # 获取当天股价
        begin_price = self.date_price_dict[delay_before][0]
        end_price = self.date_price_dict[delay_after][0]
        #print delay_before, begin_price
        #print delay_after, end_price
        if str(begin_price) == "0.0" or str(end_price) == "0.0":
            return None, None

        # 获取总市值
        company_price = self.date_price_dict[valid_begin_date][1]
        if str(company_price) == "0.0":
            return None, None

        return end_price/begin_price - 1, company_price



    def period_is_year(self, report_date_list, raw_info, raw_info_list, report_path):
        """
        观察期为1年
        """
        print_feature = False
        feature_list = [None for i in range(4*len(self.feature_mapping) + 1)]
        for idx, date in enumerate(report_date_list[-4:]):
            for feat_name in self.feature_mapping:
                if feat_name in raw_info[str(date)]:
                    if print_feature:
                        print "date=%s, feat=%s, value=%s" % \
                            (date, feat_name, raw_info[str(date)][feat_name])
                    feat_idx = idx*len(self.feature_mapping) + self.feature_mapping[feat_name]
                    feat_value = raw_info[str(date)][feat_name]
                    feature_list[feat_idx] = feat_value

        # 获取对应时间段的股价涨跌幅
        stock_id = report_path.split("/")[-1].split("_")[0]
        price_change, company_price = self._get_stock_price_change(stock_id, report_date_list[-4:][0], report_date_list[-4:][-1])
        if not price_change:
            return None
        feature_list[-1] = price_change

        if print_feature:
            print report_path.split("/")[-1] + " " + " ".join(map(str, feature_list))
        self.f_out.write(report_path.split("/")[-1] + " " + " ".join(map(str, feature_list)) + "\n")


    def period_is_quarter(self, report_date_list, raw_info, raw_info_list, report_path):
        """
        观察期为一个季度
        """
        print_feature = False
        for idx, date in enumerate(report_date_list[4:-1]):
            feature_list = [None for i in range(len(self.feature_mapping) + 2)]
            for feat_name in self.feature_mapping:
                if feat_name in raw_info[str(date)]:
                    if print_feature:
                        print "date=%s, feat=%s, value=%s" % \
                            (date, feat_name, raw_info[str(date)][feat_name])
                    feat_idx = self.feature_mapping[feat_name] 
                    feat_value = raw_info[str(date)][feat_name]
                    feature_list[feat_idx] = feat_value

            # 获取对应时间段的股价涨跌幅
            stock_id = report_path.split("/")[-1].split("_")[0]
            price_change, company_price= self._get_stock_price_change(stock_id, report_date_list[idx], report_date_list[idx+1])
            if not price_change:
                print "No price change!"
                continue
            if not company_price:
                print "No company price!"
                continue
            feature_list[-1] = price_change
            feature_list[-2] = company_price
    
            if print_feature:
                print report_path.split("/")[-1] + " " + " ".join(map(str, feature_list))
            self.f_out.write(report_path.split("/")[-1] + " " + \
                str(report_date_list[idx]) + " " + str(report_date_list[idx+1]) + " " + \
                " ".join(map(str, feature_list)) + "\n")




    def process_one_company(self, report_path):
        """
        decode one report
        """
        print_feature = False
        with codecs.open(report_path, "r", "utf-8", "ignore") as f:
            raw_info = json.load(f)
        raw_info_list = sorted(raw_info.iteritems(), key = lambda x:int(x[0]))
        #print json.dumps(raw_info, ensure_ascii = False, indent = 1)

        # 获取最长连续年报周期内的所有年报日期
        report_date_list = self._get_longest_consecutive_period(raw_info_list)
        print report_date_list
        if len(report_date_list) < 5:
            print "Report is incomplete! %s" % report_path
            return

        #self.period_is_year(report_date_list, raw_info, raw_info_list, report_path)
        self.period_is_quarter(report_date_list, raw_info, raw_info_list, report_path)



    def get_valid_stock_id(self):
        """
        获取至少有4个完整年报周期的公司股票id及名称
        """
        valid_stock_id_path = "valid_stock_id_china"
        reports_path = map(lambda x:os.path.join(self.reports_dir, x), 
            os.listdir(self.reports_dir))

        f_out = open(valid_stock_id_path, "w")
        for report_path in reports_path:
            print "Now processing %s" % report_path
            with codecs.open(report_path, "r", "utf-8", "ignore") as f:
                raw_info = json.load(f)
            raw_info_list = sorted(raw_info.iteritems(), key = lambda x:int(x[0]))
    
            # 获取最长连续年报周期内的所有年报日期
            report_date_list = self._get_longest_consecutive_period(raw_info_list)
            if len(report_date_list) < 4:
                print "Report is incomplete! %s" % report_path
                continue
            f_out.write(report_path.split("/")[-1] + "\n")

        f_out.close()



    def main(self):
        """
        main process
        """
        reports_path = map(lambda x:os.path.join(self.reports_dir, x), 
            os.listdir(self.reports_dir))

        for report_path in reports_path:
            print "Now processing %s" % report_path
            if u"ST" in report_path:
                print "Filter ST company!"
                continue
            self.process_one_company(report_path)

        self.f_out.close()


if __name__ == "__main__":
    reports_dir = sys.argv[1]
    conf_path = sys.argv[2]
    stock_price_dir = sys.argv[3]
    feature_output = sys.argv[4]
    fs = FeatureSelector(reports_dir, conf_path, stock_price_dir, feature_output)
    #fs.get_valid_stock_id()
    fs.main()
