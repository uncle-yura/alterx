# -*- coding: utf-8 -*-
#
# AlterX GUI - util
#
# Copyright 2020-2020 uncle-yura uncle-yura@tuta.io
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#

from __future__ import division, absolute_import, print_function, unicode_literals

from alterx.common.locale import _
from alterx.gui.qt_bindings import *

import pkg_resources
import sys
import traceback
import xml.sax.saxutils as saxutils

ALTERX_HOME_DOMAIN = ""
ALTERX_HOME_URL = "https://" + ALTERX_HOME_DOMAIN

IMAGE_DIR = pkg_resources.resource_filename("alterx", "images")
STYLESHEET_DIR = pkg_resources.resource_filename("alterx", "stylesheets")

# Convert an integer to a dual-string
def intToDualString(value, bitWidth):
    string = []
    for bitnr in range(bitWidth - 1, -1, -1):
        string.append('1' if ((value >> bitnr) & 1) else '0')
        if bitnr and bitnr % 4 == 0:
            string.append('_')
    return ''.join(string)

# Get the default fixed font
def getDefaultFixedFont(pointSize=11, bold=False):
    font = QFont()
    font.setStyleHint(QFont.Courier)
    font.setFamily("Courier")
    font.setPointSize(pointSize)
    font.setWeight(QFont.Normal)
    font.setBold(bold)
    return font

# Color used for errors
def getErrorColor():
    return QColor("#FFC0C0")


def handleFatalException(parentWidget=None):
    text = str(traceback.format_exc())
    print(_("Fatal exception:\n"), text)
    text = saxutils.escape(text)
    QMessageBox.critical(parentWidget,
                         _("A fatal exception occurred"),
                         _("<pre>"
                             "A fatal exception occurred:\n\n"
                             "{}\n\n"
                             "AlterX will be terminated."
                             "</pre>", text))
    sys.exit(1)


class HSeparator(QFrame):
    def __init__(self, parent=None):
        QFrame.__init__(self, parent)
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Sunken)


class VSeparator(QFrame):
    def __init__(self, parent=None):
        QFrame.__init__(self, parent)
        self.setFrameShape(QFrame.VLine)
        self.setFrameShadow(QFrame.Sunken)

        
class MessageBox(QDialog):
    def __init__(self,
                 parent,
                 title,
                 text,
                 verboseText=None,
                 icon=QMessageBox.Critical,
                 okButton=True,
                 continueButton=False,
                 cancelButton=False):
        QDialog.__init__(self, parent)
        self.setLayout(QGridLayout())
        self.setWindowTitle(title)

        self.text = "<pre>" + saxutils.escape(text) + "\n</pre>"
        self.verboseText = None
        if verboseText and verboseText.strip() != text.strip():
            self.verboseText = "<pre>" + \
                saxutils.escape(verboseText) + "\n</pre>"

        self.textBox = QLabel(self)
        self.textBox.setTextInteractionFlags(Qt.TextSelectableByMouse |
                                             Qt.TextSelectableByKeyboard |
                                             Qt.LinksAccessibleByMouse |
                                             Qt.LinksAccessibleByKeyboard)
        self.layout().addWidget(self.textBox, 0, 0, 1, 3)

        if self.verboseText:
            self.verboseCheckBox = QCheckBox(
                _("Show verbose information"), self)
            self.layout().addWidget(self.verboseCheckBox, 1, 0, 1, 3)
        else:
            self.verboseCheckBox = None

        buttonsLayout = QHBoxLayout()
        if okButton:
            self.okButton = QPushButton(_("&Ok"), self)
            buttonsLayout.addWidget(self.okButton)
        if continueButton:
            self.continueButton = QPushButton(_("C&ontinue"), self)
            buttonsLayout.addWidget(self.continueButton)
        if cancelButton:
            self.cancelButton = QPushButton(_("&Cancel"), self)
            buttonsLayout.addWidget(self.cancelButton)
        self.layout().addLayout(buttonsLayout, 2, 1)

        self.__updateText()

        if okButton:
            self.okButton.released.connect(self.accept)
        if continueButton:
            self.continueButton.released.connect(self.accept)
        if cancelButton:
            self.cancelButton.released.connect(self.reject)
        if self.verboseCheckBox:
            self.verboseCheckBox.stateChanged.connect(self.__updateText)

    def __updateText(self):
        if self.verboseCheckBox and\
           self.verboseCheckBox.checkState() == Qt.Checked:
            self.textBox.setText(self.verboseText)
        else:
            self.textBox.setText(self.text)

    @classmethod
    def error(cls, parent, text, verboseText=None, **kwargs):
        dlg = cls(parent=parent,
                  title="AlterX - Error",
                  text=text,
                  verboseText=verboseText,
                  icon=QMessageBox.Critical,
                  **kwargs)
        res = dlg.exec_()
        dlg.deleteLater()
        return res

    @classmethod
    def warning(cls, parent, text, verboseText=None, **kwargs):
        dlg = cls(parent=parent,
                  title="AlterX - Warning",
                  text=text,
                  verboseText=verboseText,
                  icon=QMessageBox.Warning,
                  **kwargs)
        res = dlg.exec_()
        dlg.deleteLater()
        return res
