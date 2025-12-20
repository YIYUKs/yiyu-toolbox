# uncompyle6 version 3.9.3
# Python bytecode version base 3.6 (3379)
# Decompiled from: Python 3.11.9 (tags/v3.11.9:de54cf5, Apr  2 2024, 10:12:12) [MSC v.1938 64 bit (AMD64)]
# Embedded file name: contact.py
from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_contact(object):

    def setupUi(self, contact):
        contact.setObjectName("contact")
        contact.resize(820, 358)
        contact.setStyleSheet("")
        self.label = QtWidgets.QLabel(contact)
        self.label.setGeometry(QtCore.QRect(20, 20, 401, 331))
        self.label.setStyleSheet("image: url(:/新前缀/paypal.jpg);")
        self.label.setText("")
        self.label.setObjectName("label")
        self.label_2 = QtWidgets.QLabel(contact)
        self.label_2.setGeometry(QtCore.QRect(400, 20, 401, 331))
        self.label_2.setStyleSheet("image: url(:/新前缀/wechat.jpg);")
        self.label_2.setText("")
        self.label_2.setObjectName("label_2")
        self.retranslateUi(contact)
        QtCore.QMetaObject.connectSlotsByName(contact)

    def retranslateUi(self, contact):
        _translate = QtCore.QCoreApplication.translate
        contact.setWindowTitle(_translate("contact", "打赏我"))


import res_rc
