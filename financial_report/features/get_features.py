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

    def __init__(self, reports_dir, conf_dir, stock_price_dir, feature_output):
        self.reports_dir = reports_dir
        self.conf_dir = conf_dir
        self.stock_price_dir = stock_price_dir
        self.feature_output = feature_output
        self.f_train_out = open(os.path.join(self.feature_output, "train.txt"), "w")
        self.f_test_out = open(os.path.join(self.feature_output, "test.txt"), "w")
        # read feature conf
        self._read_feature_conf()


    def _read_feature_conf(self):
        """

        """
        self.feature_mapping = {}
        self.feat_need_sep_by_quarter = {}
        feature_conf_path = os.path.join(self.conf_dir, "feature_conf")
        with codecs.open(feature_conf_path, "r", "utf-8", "ignore") as f:
            for idx, line in enumerate(f.readlines()):
                self.feature_mapping[line.strip()] = idx

        print ""
        print json.dumps(sorted(self.feature_mapping.iteritems(),
            key = lambda x:x[1]), ensure_ascii = False)
        print ""

        with codecs.open(os.path.join(self.conf_dir, "feat_need_seperate_by_quarter")
            , "r", "utf-8", "ignore") as f:
            for line in f:
                self.feat_need_sep_by_quarter[line.strip()] = None


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
        date_value_dict = raw_info[raw_info.keys()[0]]
        date_value_list = sorted(date_value_dict.iteritems(), key = lambda x:int(x[0]))
        begin_day = int(date_value_list[0][0])
        end_day = -1
        for idx in range(len(date_value_list)-1):
            date_before = date_value_list[idx][0]
            date_after = date_value_list[idx+1][0]
            try:
                diff_days = self._get_diff_days(date_before, date_after)
            except:
                begin_day = int(date_value_list[idx+1][0])
                end_day = -1
                continue
                
            if diff_days < 100:
                end_day = int(date_value_list[idx+1][0])
            else:
                begin_day = int(date_value_list[idx+1][0])
                end_day = -1

        date_list = []
        for date, _ in date_value_list:
            if int(date) >= begin_day and int(date) <= end_day:
                date_list.append(int(date))

        return date_list


    def _get_longest_subsequence_begin_with_march(self, report_date_list):
        """
        从时间序列中找出一个最长子区间，使得区间开头为3月份
        """
        begin_idx = 0
        for idx, date in enumerate(report_date_list):
            date = int(date)
            month = (date - date/10000*10000) / 100
            if month != 3:
                begin_idx += 1
            else:
                break
        return report_date_list[begin_idx:]


    def _truncate_report_by_date_list(self, raw_info, report_date_list):
        """
        报表中只留下有效的日期
        """
        origin_date_list = map(int, raw_info[raw_info.keys()[0]].keys())
        truncate_date_set = {ele for ele in origin_date_list} - {ele for ele in report_date_list}
        if len(truncate_date_set) > 0:
            for date in truncate_date_set:
                date = str(date)
                for key in raw_info:
                    raw_info[key].pop(date)

        return raw_info



    def _seperate_value_by_quarter(self, raw_info):
        """
        把一些每季度累加的值还原回当季度的值
        """
        for item in raw_info:
            if item not in self.feat_need_sep_by_quarter:
                continue
            #print item
            temp_dict = {}
            final_dict = {}
            for date in raw_info[item]:
                year = int(date)/10000
                if year not in temp_dict:
                    temp_dict[year] = []
                temp_dict[year].append([date, raw_info[item][date]])

            for year in temp_dict:
                now_list = temp_dict[year]
                now_list.sort(key = lambda x:int(x[0]))
                #print "\nbefore:"
                #print now_list
                for i in range(len(now_list)-1, 1, -1):
                    now_list[i][1] -= now_list[i-1][1]
                #print "\nafter:"
                #print now_list

        return raw_info



    def _get_stock_price_change(self, stock_id, begin_date, end_date):
        """
        获取某公司特定时间段的股票涨跌幅
        """
        price_change = None
        company_price = None
        now_price = None

        # 股价区间均推迟1个月
        begin_date = int(begin_date)
        end_date = int(end_date)
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
        for i in range(20):
            days_interval = timedelta(days = 25+i)
            delay_before = (before + days_interval).strftime("%Y-%m-%d")
            if delay_before in self.date_price_dict and \
                str(self.date_price_dict[delay_before][0]) != "0.0":
                break
        for i in range(20):
            days_interval = timedelta(days = 25+i)
            delay_after = (after + days_interval).strftime("%Y-%m-%d")
            if delay_after in self.date_price_dict and \
                str(self.date_price_dict[delay_after][0]) != "0.0":
                break
        for i in range(20):
            days_interval = timedelta(days = i)
            valid_begin_date = (before + days_interval).strftime("%Y-%m-%d")
            if valid_begin_date in self.date_price_dict and \
                str(self.date_price_dict[valid_begin_date][0]) != "0.0":
                break

        # 
        if delay_before not in self.date_price_dict or \
            delay_after not in self.date_price_dict or \
            valid_begin_date not in self.date_price_dict:
            print "delay_before:%s, delay_after:%s, valid_begin_date:%s" % \
                (delay_before, delay_after, valid_begin_date)
            return price_change, company_price, now_price

        # 获取股价变化区间的开头及结尾的股价
        begin_price = self.date_price_dict[delay_before][0]
        end_price = self.date_price_dict[delay_after][0]
        now_price = begin_price
        #print delay_before, begin_price
        #print delay_after, end_price
        if str(begin_price) == "0.0" or str(end_price) == "0.0":
            print "b_day:%s, e_day:%s, begin_price:%s, end_price:%s" % \
                (delay_before, delay_after, begin_price, end_price)
            return price_change, company_price, now_price

        # 获取总市值
        company_price = self.date_price_dict[valid_begin_date][1]
        if str(company_price) == "0.0":
            return price_change, company_price, now_price
        
        price_change = end_price/begin_price - 1
        return price_change, company_price, now_price



    def get_report_feature(self, raw_info):
        """
        观察期为一个季度
        """
        date_feature_dict = {}
        for feat_name in raw_info:
            if feat_name not in self.feature_mapping:
                continue
            report_date_list = raw_info[feat_name].keys()
            report_date_list.sort(key = lambda x:int(x))
            for idx, date in enumerate(report_date_list):
                # 获取特定时间点的特征
                if date not in date_feature_dict:
                    feature_list = [None for i in range(len(self.feature_mapping) + 4)]
                    date_feature_dict[date] = feature_list
                else:
                    feature_list = date_feature_dict[date]
                # 填充特征
                feat_value = raw_info[feat_name][date]
                feat_idx = self.feature_mapping[feat_name] 
                feature_list[feat_idx] = feat_value

                # 获取季度特征
                date = int(date)
                month = (date-date/10000*10000) / 100
                if month == 3:
                    feature_list[-4] = 1
                elif month == 6:
                    feature_list[-4] = 2
                elif month == 9:
                    feature_list[-4] = 3
                elif month == 12:
                    feature_list[-4] = 4
        
        return date_feature_dict


    def get_stock_price_feature(self, date_feature_dict, report_path):
        """

        """
        print_feature = True
        report_date_list = date_feature_dict.keys()
        report_date_list.sort(key = lambda x:int(x))
        if print_feature:
            print report_date_list
        for idx, date in enumerate(report_date_list[:-1]):
            feature_list = date_feature_dict[date]
            # 获取股价特征
            stock_id = report_path.split("/")[-1].split("_")[0]
            price_change, company_price, now_price = self._get_stock_price_change(stock_id, report_date_list[idx], report_date_list[idx+1])
            if not price_change:
                print "No price change!"
                continue
            if not company_price:
                print "No company price!"
                continue
            feature_list[-1] = price_change
            feature_list[-2] = company_price
            feature_list[-3] = now_price

        if print_feature:
            pass
            #print "date=%s, feat=%s, value=%s" % \
            #    (date, feat_name, raw_info[feat_name][str(date)])
   
        date_list = report_date_list[:-1]
        for idx, date in enumerate(date_list):
            feature_list = date_feature_dict[date]
            if feature_list[-1] is None:
                continue
            if print_feature:
                print report_path.split("/")[-1] + " " + " ".join(map(str, feature_list))
            if idx != len(date_list) -1:
                self.f_train_out.write(report_path.split("/")[-1] + " " + \
                    str(date) + " " + " ".join(map(str, feature_list)) + "\n")
            else:
                self.f_test_out.write(report_path.split("/")[-1] + " " + \
                    str(date) + " " + " ".join(map(str, feature_list)) + "\n")


    def process_one_company(self, report_path):
        """
        decode one report
        """
        print_feature = False
        with codecs.open(report_path, "r", "utf-8", "ignore") as f:
            raw_info = json.load(f)

        if len(raw_info[raw_info.keys()[0]]) < 4:
            print "Report is incomplete! %s" % report_path
            return

        for key in raw_info.keys():
            if key not in self.feature_mapping:
                raw_info.pop(key)
        #raw_info_list = sorted(raw_info.iteritems(), key = lambda x:int(x[0]))
        #print json.dumps(raw_info.keys(), ensure_ascii = False, indent = 1)

        # 获取最长连续年报周期内的所有年报日期
        report_date_list = self._get_longest_consecutive_period(raw_info)
        if len(report_date_list) < 5:
            print "Report is incomplete! %s" % report_path
            return

        # 从时间序列中找出一个最长子区间，使得区间开头为3月份
        report_date_list = self._get_longest_subsequence_begin_with_march(report_date_list)

        raw_info = self._truncate_report_by_date_list(raw_info, report_date_list)

        raw_info = self._seperate_value_by_quarter(raw_info)

        try:
            date_feature_dict = self.get_report_feature(raw_info)

            self.get_stock_price_feature(date_feature_dict, report_path)
        except Exception as e:
            print e

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

        for idx, report_path in enumerate(reports_path):
            print "Now processing %s" % report_path
            if u"ST" in report_path:
                print "Filter ST company!"
                continue
            self.process_one_company(report_path)

        self.f_train_out.close()
        self.f_test_out.close()


if __name__ == "__main__":
    reports_dir = sys.argv[1]
    conf_path = sys.argv[2]
    stock_price_dir = sys.argv[3]
    feature_output = sys.argv[4]
    fs = FeatureSelector(reports_dir, conf_path, stock_price_dir, feature_output)
    #fs.get_valid_stock_id()
    fs.main()
