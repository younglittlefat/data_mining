# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'mzitu.ui'
#
# Created by: PyQt4 UI code generator 4.11.4
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui


try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

image_path_list = []

def load_image_path(file_name):
    global image_path_list
    with codecs.open(file_name, "r", "utf-8", "ignore") as f:
        image_path_list = [(line.strip().split("\t")[0], int(line.strip().split("\t")[1])) for line in f.readlines()]
        


class Ui_Dialog(object):

    img_no = 0

    def setupUi(self, Dialog):
        Dialog.setObjectName(_fromUtf8("Dialog"))
        Dialog.resize(1003, 706)
        self.pushButton = QtGui.QPushButton(Dialog)
        self.pushButton.setGeometry(QtCore.QRect(720, 600, 99, 27))
        self.pushButton.setObjectName(_fromUtf8("pushButton"))
        self.pushButton_2 = QtGui.QPushButton(Dialog)
        self.pushButton_2.setGeometry(QtCore.QRect(210, 600, 99, 27))
        self.pushButton_2.setObjectName(_fromUtf8("pushButton_2"))
        self.radioButton = QtGui.QRadioButton(Dialog)
        self.radioButton.setGeometry(QtCore.QRect(540, 600, 117, 22))
        self.radioButton.setObjectName(_fromUtf8("radioButton"))
        self.radioButton_2 = QtGui.QRadioButton(Dialog)
        self.radioButton_2.setGeometry(QtCore.QRect(380, 600, 117, 22))
        self.radioButton_2.setObjectName(_fromUtf8("radioButton_2"))
        self.graphicsView = QtGui.QGraphicsView(Dialog)
        self.graphicsView.setGeometry(QtCore.QRect(280, 80, 431, 441))
        self.graphicsView.setObjectName(_fromUtf8("graphicsView"))
        self.pushButton_3 = QtGui.QPushButton(Dialog)
        self.pushButton_3.setGeometry(QtCore.QRect(790, 460, 151, 51))
        self.pushButton_3.setObjectName(_fromUtf8("pushButton_3"))

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        global image_path_list
        Dialog.setWindowTitle(_translate("Dialog", "Dialog", None))
        self.pushButton.setText(_translate("Dialog", "下一张", None))
        self.pushButton_2.setText(_translate("Dialog", "上一张", None))
        self.radioButton.setText(_translate("Dialog", "负样本", None))
        self.radioButton_2.setText(_translate("Dialog", "正样本", None))
        self.pushButton_3.setText(_translate("Dialog", "保存结果", None))

        pixmap = QtGui.QPixmap(image_path_list[0][0])
        l=QtGui.QLabel(self)
        l.setPixmap(pixmap)



if __name__ == "__main__":
    import sys
    import codecs
    reload(sys)
    sys.setdefaultencoding("utf-8")
    load_image_path("all_image_path")
    app = QtGui.QApplication(sys.argv)
    Dialog = QtGui.QDialog()
    ui = Ui_Dialog()
    ui.setupUi(Dialog)
    Dialog.show()
    sys.exit(app.exec_())

