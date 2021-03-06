# -*- coding: utf-8 -*-
#
# AlterX GUI - macro command 1 widget
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
from alterx.common.compat import *
from alterx.common import *
from alterx.gui.util import *
from alterx.core.linuxcnc import *

class func:
    def __init__(self, button):
        self.button = button
        self.edit = QLineEdit()
        self.edit.setObjectName("edit_in_button_edit_x")
        self.edit.setVisible(False)
        validator = QDoubleValidator()
        validator.setLocale(QLocale(QLocale.English))
        self.edit.setValidator(validator)
        edit_layout = QVBoxLayout(self.button)
        edit_layout.addWidget(self.edit)
        self.edit_lifetime = 0
        dir_path = os.path.dirname(os.path.realpath(__file__))

        if os.path.isfile("%s/icon.png" % dir_path):
            self.button.setIcon(QIcon("%s/icon.png" % dir_path))
            self.button.setIconSize(QSize(90, 90))
            self.button.setText("")
        else:
            self.button.setStyleSheet("color:black")
            self.button.setText("G0 Z%")

    def update(self):
        if not self.edit.hasFocus() and self.edit_lifetime == 0:
            self.edit.setVisible(False)
            self.edit.setText('')
        else:
            self.edit_lifetime -= 1

    def execute(self):
        if self.edit.isVisible():
            self.edit.setVisible(False)
            printVerbose(_("Button macro command {}: {}",1, self.edit.text()))
            if self.edit.text() != "":
                COMMAND.mdi("G0 Z{}".format(self.edit.text()))

        else:
            printVerbose(_("Button macro command {} clicked",1))
            self.edit_lifetime = 5
            self.edit.setText("")
            self.edit.setVisible(True)
            self.edit.setFocus()
