#!/usr/bin/env python
#-*- coding:utf-8 -*-

from PyQt4 import QtCore, QtGui

class myDialog(QtGui.QDialog):
    _buttons = 0

    def __init__(self, parent=None):
        super(myDialog, self).__init__(parent)

        self.pushButton = QtGui.QPushButton(self)
        self.pushButton.setText(QtGui.QApplication.translate("self", "Add Button!", None, QtGui.QApplication.UnicodeUTF8))
        self.pushButton.clicked.connect(self.on_pushButton_clicked)

        self.scrollArea = QtGui.QScrollArea(self)
        self.scrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents = QtGui.QWidget(self.scrollArea)
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 380, 247))
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)

        self.verticalLayout = QtGui.QVBoxLayout(self)
        self.verticalLayout.addWidget(self.pushButton)
        self.verticalLayout.addWidget(self.scrollArea)

        self.verticalLayoutScroll = QtGui.QVBoxLayout(self.scrollAreaWidgetContents)

    @QtCore.pyqtSlot()
    def on_pushButton_clicked(self):
        self._buttons  += 1
        pustButtonName = u"Button {0}".format(self._buttons)

        pushButton = QtGui.QPushButton(self.scrollAreaWidgetContents)
        pushButton.setText(pustButtonName)

        self.verticalLayoutScroll.addWidget(pushButton)


if __name__ == "__main__":
    import sys

    app = QtGui.QApplication(sys.argv)
    app.setApplicationName('myDialog')

    main = myDialog()
    main.show()

    sys.exit(app.exec_())