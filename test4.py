from PyQt4 import QtGui

class TabBar(QtGui.QTabBar):
    def paintEvent(self, event):
        painter = QtGui.QStylePainter(self)
        option = QtGui.QStyleOptionTab()
        for index in range(self.count()):
            self.initStyleOption(option, index)
            bgcolor = QtGui.QColor(self.tabText(index))
            option.palette.setColor(QtGui.QPalette.Window, bgcolor)
            painter.drawControl(QtGui.QStyle.CE_TabBarTabShape, option)
            painter.drawControl(QtGui.QStyle.CE_TabBarTabLabel, option)

class Window(QtGui.QTabWidget):
    def __init__(self):
        QtGui.QTabWidget.__init__(self)
        self.setTabBar(TabBar(self))
        for color in 'tomato orange yellow lightgreen skyblue plum'.split():
            self.addTab(QtGui.QWidget(self), color)

if __name__ == '__main__':

    import sys
    app = QtGui.QApplication(sys.argv)
    window = Window()
    window.resize(420, 200)
    window.show()
    sys.exit(app.exec_())