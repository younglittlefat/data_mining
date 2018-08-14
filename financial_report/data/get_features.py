#encoding=utf-8
import sys
import os
import json
import codecs
from datetime import datetime

reload(sys)
sys.setdefaultencoding("utf-8")


class FeatureSelector:

    def __init__(self, reports_dir, feature_conf, feature_output):
        self.reports_dir = reports_dir
        self.feature_conf = feature_conf
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
        if len(report_date_list) < 4:
            print "Report is incomplete! %s" % report_path
            return

        feature_list = [None for i in range(4*len(self.feature_mapping))]
        #print feature_list
        for idx, date in enumerate(report_date_list[-4:]):
            for feat_name in self.feature_mapping:
                if feat_name in raw_info[str(date)]:
                    if print_feature:
                        print "date=%s, feat=%s, value=%s" % \
                            (date, feat_name, raw_info[str(date)][feat_name])
                    feat_idx = idx*len(self.feature_mapping) + self.feature_mapping[feat_name]
                    feat_value = raw_info[str(date)][feat_name]
                    feature_list[feat_idx] = feat_value

        if print_feature:
            print report_path.split("/")[-1] + " " + " ".join(map(str, feature_list))
        self.f_out.write(report_path.split("/")[-1] + " " + " ".join(map(str, feature_list)) + "\n")


    def main(self):
        """
        main process
        """
        reports_path = map(lambda x:os.path.join(self.reports_dir, x), 
            os.listdir(self.reports_dir))

        for report_path in reports_path:
            print "Now processing %s" % report_path
            self.process_one_company(report_path)

        self.f_out.close()


if __name__ == "__main__":
    reports_dir = sys.argv[1]
    conf_path = sys.argv[2]
    feature_output = sys.argv[3]
    fs = FeatureSelector(reports_dir, conf_path, feature_output)
    fs.main()
