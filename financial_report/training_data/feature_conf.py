#encoding=utf-8


class PriceFeature(object):
    active_feature_name = [u"日期", u"收盘价", u"成交量", u"成交金额", u"总市值", u"流通市值"]
    def __init__(self):
        pass


class FinancialFeature(object):
    active_feature_name = [
        u"日期",
        u"净利润(元)",
        u"净利润同比增长率",
        u"扣非净利润(元)",
        u"扣非净利润同比增长率",
        u"营业总收入(元)",
        u"营业总收入同比增长率",
        u"基本每股收益(元)",
        u"每股净资产(元)",
        u"每股资本公积金(元)"]

    def __init__(self):
        pass