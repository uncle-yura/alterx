#!/usr/bin/env python
# -*- coding:UTF-8 -*-

import time
import os
import sys

try:
    from PyQt5 import QtCore, QtWidgets, QtGui, uic
except:
    from PySide2 import QtCore, QtWidgets, QtGui
    from PySide2.QtUiTools import QUiLoader as uic

class func(QtWidgets.QMainWindow):

    def __init__(self, parent=None):
        super(func, self).__init__(parent)
        dir_path = os.path.dirname(os.path.realpath(__file__))
        uic.loadUi('%s/module.ui' % dir_path, self)
        self.show()

    def testButtonClicked(self):
        print("Button example clicked")
        self.label.setText("Example")


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    ex = func()
    sys.exit(app.exec_())
