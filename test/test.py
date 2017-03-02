from PyQt4 import QtGui, QtCore
import sys
import time


class TabWidget(QtGui.QTabWidget):
    def __init__(self, action):
        super(TabWidget, self).__init__()
        self.setTabsClosable(True)
        self.tabCloseRequested.connect(action)

app = QtGui.QApplication(sys.argv)

main_dialog = QtGui.QDialog()
tab_widget = TabWidget(lambda x: close(x, 'hi'))
def close(index, msg):
    print(index, msg)


main_layout = QtGui.QVBoxLayout()
main_dialog.setLayout(main_layout)

main_layout.addWidget(tab_widget)

corner_widget = QtGui.QWidget()
layout = QtGui.QHBoxLayout()
label = QtGui.QLabel('hi')
layout.addWidget(label)
corner_widget.setLayout(layout)

tab_widget.setCornerWidget(corner_widget)

tab = QtGui.QWidget()
layout = QtGui.QHBoxLayout()
label = QtGui.QLabel('bye')
layout.addWidget(label)
tab.setLayout(layout)

tab_widget.addTab(tab, 'oh')

main_dialog.show()

app.exec_()