#encoding=utf-8
import sys
import codecs
import random

from PyQt4 import QtCore, QtGui

reload(sys)
sys.setdefaultencoding("utf-8")

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s



class Example(QtGui.QWidget):

    def __init__(self):
        super(Example, self).__init__()
        self.img_no = 0
        self.labeled_dict = {}
        self.image_path_list = []
        self.load_image_path("all_image_path")
        self.initUI()


    def load_image_path(self, file_name):
        with codecs.open("labeled_image", "r", "utf-8", "ignore") as f:
            for line in f:
                temp = line.strip().split("\t")
                self.labeled_dict[temp[0]] = int(temp[1])

        with codecs.open(file_name, "r", "utf-8", "ignore") as f:
            for line in f:
                temp = line.strip().split("\t")
                if temp[0] in self.labeled_dict:
                    self.image_path_list.append((temp[0], self.labeled_dict[temp[0]]))
                else:
                    self.image_path_list.append((temp[0], -1))
        random.shuffle(self.image_path_list)


    def initUI(self):
        self.setGeometry(300, 300, 1100, 1300)
        self.hbox = QtGui.QHBoxLayout(self)
        while self.image_path_list[self.img_no][1] != -1:
            self.img_no += 1
        pixmap = QtGui.QPixmap(self.image_path_list[self.img_no][0])
        self.qlabel = QtGui.QLabel(self)
        self.qlabel.setPixmap(pixmap.scaled(700,700,1))
        self.hbox.addWidget(self.qlabel)
        self.setLayout(self.hbox)
        self.setWindowTitle(_fromUtf8("图片标注"))
        self.move(250, 200)

        self.pushButton = QtGui.QPushButton(self)
        self.pushButton.setGeometry(QtCore.QRect(900, 700, 150, 40))
        self.pushButton.setObjectName(_fromUtf8("下一张"))
        self.pushButton.setText(_fromUtf8("下一张"))

        self.pushButton_2 = QtGui.QPushButton(self)
        self.pushButton_2.setGeometry(QtCore.QRect(900, 400, 150, 40))
        self.pushButton_2.setObjectName(_fromUtf8("上一张"))
        self.pushButton_2.setText(_fromUtf8("上一张"))

        self.radioButton = QtGui.QRadioButton(self)
        self.radioButton.setGeometry(QtCore.QRect(900, 600, 200, 42))
        self.radioButton.setObjectName(_fromUtf8("radioButton"))
        self.radioButton_2 = QtGui.QRadioButton(self)
        self.radioButton_2.setGeometry(QtCore.QRect(900, 500, 200, 42))
        self.radioButton_2.setObjectName(_fromUtf8("radioButton_2"))
        self.radioButton.setText(_fromUtf8("负样本"))
        self.radioButton_2.setText(_fromUtf8("正样本"))

        self.pushButton_3 = QtGui.QPushButton(self)
        self.pushButton_3.setGeometry(QtCore.QRect(900, 200, 151, 51))
        self.pushButton_3.setObjectName(_fromUtf8("pushButton_3"))
        self.pushButton_3.setText(_fromUtf8("保存"))

        # connect
        self.connect(self.pushButton, QtCore.SIGNAL('clicked()'), self.next_pic)
        self.connect(self.pushButton_2, QtCore.SIGNAL('clicked()'), self.last_pic)
        self.connect(self.pushButton_3, QtCore.SIGNAL('clicked()'), self.save_result)
        self.connect(self.radioButton, QtCore.SIGNAL("clicked()"), self.neg_sample)
        self.connect(self.radioButton_2, QtCore.SIGNAL("clicked()"), self.pos_sample)


    def next_pic(self):
        self.radioButton.setDown(False)
        self.radioButton_2.setDown(False)

        self.img_no += 1
        if self.img_no >= len(self.image_path_list):
            self.img_no -= len(self.image_path_list)
        while self.image_path_list[self.img_no][1] != -1:
            self.img_no += 1
            if self.img_no >= len(self.image_path_list):
                self.img_no -= len(self.image_path_list)
                break

        pix = QtGui.QPixmap(self.image_path_list[self.img_no][0])
        self.qlabel.setPixmap(pix.scaled(700,700,1))

    def last_pic(self):
        self.img_no -= 1
        if self.img_no < 0:
            self.img_no += len(self.image_path_list)
        while self.image_path_list[self.img_no][1] != -1:
            self.img_no += 1
            if self.img_no < 0:
                self.img_no += len(self.image_path_list)
                break

        pix = QtGui.QPixmap(self.image_path_list[self.img_no][0])
        self.qlabel.setPixmap(pix.scaled(700,700,1))

    def pos_sample(self):
        self.labeled_dict[self.image_path_list[self.img_no][0]] = 1

    def neg_sample(self):
        self.labeled_dict[self.image_path_list[self.img_no][0]] = 0


    def save_result(self):
        with open("labeled_image", "w") as f:
            for path in self.labeled_dict:
                f.write("%s\t%d\n" % (path, self.labeled_dict[path]))
            


def main():
    app = QtGui.QApplication([])
    exm = Example()
    exm.show()
    app.exec_()

if __name__ == "__main__":
    main()
