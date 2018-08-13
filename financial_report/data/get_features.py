#encoding=utf-8
import sys
import os
import json
import codecs
from datetime import datetime

reload(sys)
sys.setdefaultencoding("utf-8")


class FeatureSelector:

    def __init__(self, reports_dir):
        self.reports_dir = reports_dir


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


    def _get_longest_consecutive_period(self, raw_info):
        """

        """
        begin_day = int(raw_info[0][0])
        end_day = -1
        for idx in range(len(raw_info)-1):
            date_before = raw_info[idx][0]
            date_after = raw_info[idx+1][0]
            diff_days = self._get_diff_days(date_before, date_after)
            if diff_days < 100:
                end_day = int(raw_info[idx+1][0])
            else:
                begin_day = int(raw_info[idx+1][0])
                end_day = -1

        return begin_day, end_day
        


    def process_one_report(self, report_path):
        """
        decode one report
        """
        with codecs.open(report_path, "r", "utf-8", "ignore") as f:
            raw_info = json.load(f)
        raw_info = sorted(raw_info.iteritems(), key = lambda x:int(x[0]))
        #print json.dumps(raw_info, ensure_ascii = False, indent = 1)

        print self._get_longest_consecutive_period(raw_info)


    def main(self):
        """
        main process
        """
        reports_path = map(lambda x:os.path.join(self.reports_dir, x), 
            os.listdir(self.reports_dir))

        for report_path in reports_path:
            print "Now processing %s" % report_path
            self.process_one_report(report_path)


if __name__ == "__main__":
    reports_dir = sys.argv[1]
    fs = FeatureSelector(reports_dir)
    fs.main()
