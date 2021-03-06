# -*- coding: utf-8 -*-
#
# AlterX GUI - HAL editor
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

__all__ = ["HalEditor"]

from alterx.common.locale import _
from alterx.common.compat import *
from alterx.common.preferences import *
from alterx.common import *

from alterx.gui.util import *

from alterx.core.linuxcnc import *
from alterx.core.ascope import AScope as osc

import subprocess

class HalCompleter(QCompleter):
    def __init__(self, parent=None):
        QCompleter.__init__(self, [], parent)
        self.parent = parent
        self.setCompletionMode(QCompleter.PopupCompletion)
        self.setCaseSensitivity(Qt.CaseInsensitive)
        self.activated.connect(self.insertCompletion)  

    def modelFromList(self, words):
        model = QStringListModel(words, self)
        self.setModel(model)

    def textUnderCursor(self):
        tc = self.parent.textCursor()
        tc.select(QTextCursor.WordUnderCursor)
        return tc.selectedText()

    def insertCompletion(self, completion):
        tc = self.parent.textCursor()
        extra = len(completion) - len(self.completionPrefix())
        tc.movePosition(QTextCursor.Left)
        tc.movePosition(QTextCursor.EndOfWord)
        tc.insertText(completion[-extra:])
        self.parent.setTextCursor(tc)

    def text_changed(self):
        completionPrefix = self.textUnderCursor()
        if not completionPrefix:
            self.popup().hide()
            return
       
        if (completionPrefix != self.completionPrefix()):
            self.setCompletionPrefix(completionPrefix)
            popup = self.popup()
            popup.setCurrentIndex(
                self.completionModel().index(0,0))
            
        cr = self.parent.cursorRect()
        cr.setWidth(self.popup().sizeHintForColumn(0)
            + self.popup().verticalScrollBar().sizeHint().width())
        self.complete(cr)

class HalEditor(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)

        layout = QVBoxLayout()
        
        label = QLabel(_("HAL Editor"))
        label.setObjectName("lbl_settings_haleditor")
        layout.addWidget(label)
        
        layout_edit = QVBoxLayout()
        layout_view = QVBoxLayout()

        self.halCombo = QComboBox()
        layout.addWidget(self.halCombo)
        self.control = 0
        self.halTextEdit = QTextEdit()
        completer = HalCompleter(self.halTextEdit)
        completer.setWidget(self.halTextEdit)
        
        try:
            data_pin = osc.send_packet(self.control,osc.OSC_LIST,osc.HAL_PIN,0)
            data_pin = data_pin.split('\n')
            
            if "CONTROL" in data_pin[0]:
                self.control = int(data_pin[0].split(' ')[1],16)
                data_pin = data_pin[1:]
            
            data_param = osc.send_packet(self.control,
                                        osc.OSC_LIST,osc.HAL_PARAMETER,0)
            data_param = data_param.split('\n')

            if "CONTROL" in data_param[0]:
                self.control = int(data_param[0].split(' ')[1],16)
                data_param = data_param[1:]

            data = list(data_pin) + list(data_param)
        
            words = []
            for d in data:
                p_list = [c for c in d.split(' ') if len(c)>0]
                if len(p_list) != 4:
                    continue
                words.append(p_list[3])            
            completer.modelFromList(words)
        except Exception as e:
            printInfo(_("Failed to get hal pin list: {}",e))
        
        self.halTextEdit.textChanged.connect(completer.text_changed)
        layout.addWidget(self.halTextEdit)

        lay_h1 = QHBoxLayout()
        self.openButton = QPushButton()
        self.openButton.setText(_("Open"))
        self.openButton.clicked.connect(self.on_openButton_clicked)
        lay_h1.addWidget(self.openButton)
        self.saveButton = QPushButton()
        self.saveButton.setText(_("Save"))
        self.saveButton.clicked.connect(self.on_saveButton_clicked)
        lay_h1.addWidget(self.saveButton)
        self.saveAsButton = QPushButton()
        self.saveAsButton.setText(_("Save as"))
        self.saveAsButton.clicked.connect(self.on_saveAsButton_clicked)
        lay_h1.addWidget(self.saveAsButton)
        layout.addLayout(lay_h1)

        self.hal_dir = INFO.working_dir
        self.setLayout(layout)
        self.setPath()
        self.halCombo.setCurrentIndex(-1)
        self.halCombo.currentIndexChanged.connect(self.selectionChanged)
        
    def setPath(self):
        self.halCombo.clear()
        model = self.halCombo.model()
        try:
            fileNames = [f for f in os.listdir(self.hal_dir) if f.lower().endswith('.hal')]

            for i in(fileNames):
                item = QStandardItem(i)
                item.setData(self.hal_dir , role=Qt.UserRole + 1)
                index = model.appendRow(item)
        except Exception as e:
            printDebug(_("Failed to set hal path,{}",e))
        self.halCombo.setCurrentIndex(-1)
        self.halTextEdit.clear()

    def selectionChanged(self, i):
        path = self.halCombo.itemData(i, role=Qt.UserRole + 1)
        name = self.halCombo.itemData(i, role=Qt.DisplayRole)
        if name:
            halName = os.path.join(path, name)
            self.loadHalFile(halName)

    def loadHalFile(self, halName):
        try:
            with open(halName,'r') as file:
                hal = file.read()
                hal = toUnicode(hal)
        except Exception as e:
            printWarning(_("Failed to load hal-file {}",e))

        self.halTextEdit.setPlainText(hal)

    def on_openButton_clicked(self):
        dialog = QFileDialog(self)
        dialog.setDirectory(self.hal_dir)
        fileName, _ = dialog.getOpenFileName()
        if fileName:
            self.loadHalFile(fileName)

    def on_saveButton_clicked(self):
        currentIndex = self.halCombo.currentIndex()
        if currentIndex > -1:
            path = self.halCombo.itemData(currentIndex, role=Qt.UserRole + 1)
            name = self.halCombo.itemData(currentIndex, role=Qt.DisplayRole)
            fileName = os.path.join(path, name)
            halText = self.halTextEdit.toPlainText()
            try:
                with open(fileName,'w') as file:
                    file.write(halText)
                Notify.Info(_("HAL-file saved."))
            except Exception as e:
                Notify.Warning(_("Failed to save hal-file"))
                printWarning(_("Failed to save hal-file, {}",e))
        else:
            self.on_saveAsButton_clicked()


    def on_saveAsButton_clicked(self):
        dialog = QFileDialog()
        currentIndex = self.halCombo.currentIndex()
        if currentIndex > -1:
            dialog.setDirectory(self.halCombo.itemData(
                                currentIndex, role=Qt.UserRole + 1))
            dialog.selectFile(self.halCombo.itemData(
                                currentIndex, role=Qt.DisplayRole))
        else:
            dialog.setDirectory(self.hal_dir)
        
        dialog.setFilter(dialog.filter()|QDir.Hidden)
        dialog.setDefaultSuffix("hal")
        dialog.setAcceptMode(QFileDialog.AcceptSave)
        dialog.setNameFilters(["HAL (*.hal)"])

        if dialog.exec_() == QDialog.Accepted:
            fileName = dialog.selectedFiles()[0]
            halText = self.halTextEdit.toPlainText()
            try:
                with open(fileName,'w') as file:
                    file.write(halText)
                Notify.Info(_("HAL-file saved."))
            except Exception as e:
                Notify.Warning(_("Failed to save hal-file"))
                printWarning(_("Failed to save hal-file, {}",e))
            self.setPath()
