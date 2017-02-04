from PyQt4 import QtGui, QtCore
import sys
import time


####################################################################
class MyThread(QtCore.QThread):
    def __init__(self, item):
        super(MyThread, self).__init__()
        self.item = item

    #####################################################################
    def run(self):
        for angle in range(180, 0, -1):
            start_angle = angle * 16
            span_angle = (180 - angle) * 2 * 16
            self.item.set_angles(start_angle, span_angle)
            time.sleep(0.05)

####################################################################
class AudioListWidgetItemDelegate(QtGui.QItemDelegate):
    def __init__(self, list_widget, parent=None):
        QtGui.QItemDelegate.__init__(self, parent)
        self.list_widget = list_widget

    def paint(self, painter, option, index):
        painter.save()

        painter.setBrush(QtGui.QBrush(QtCore.Qt.red))
        painter.drawRect(option.rect)

        # set background color
        painter.setPen(QtGui.QPen(QtCore.Qt.NoPen))

        center_x = option.rect.width() * 4 / 5
        center_y = option.rect.height() * index.row() + option.rect.height() / 2
        painter.setBrush(QtGui.QBrush(QtCore.Qt.white))
        painter.drawEllipse(QtCore.QPointF(center_x, center_y), 10, 10)
        painter.setBrush(QtGui.QBrush(QtCore.Qt.green))
        rectangle = QtCore.QRectF(10.0, 20.0, 60.0, 60.0)
        startAngle = self.list_widget.item(0).start_angle
        spanAngle = self.list_widget.item(0).span_angle
        painter.drawChord(rectangle, startAngle, spanAngle)

        painter.restore()


#####################################################################
class AudioListWidgetItem(QtGui.QListWidgetItem):
    #####################################################################
    def __init__(self, url):
        super(AudioListWidgetItem, self).__init__()
        self.setSizeHint(QtCore.QSize(200,100))
        self.url = url

    #####################################################################
    def set_angles(self, start_angle, span_angle):
        self.start_angle = start_angle
        self.span_angle = span_angle
        self.setText(str(self.start_angle))


#####################################################################
class AudioListWidget(QtGui.QListWidget):

    #####################################################################
    def __init__(self, parent=None):
        super(AudioListWidget, self).__init__(parent)

        de = AudioListWidgetItemDelegate(self)

        # model = QtGui.QStandardItemModel()  # declare model
        # self.setModel(model)  # assign model to table view

        self.setItemDelegate(de)

    #####################################################################
    def add(self, url):
        for i in range(self.count()):
            if self.item(i).url == url:
                return
        item = AudioListWidgetItem(url)
        self.addItem(item)
        # item.add_button()

    #####################################################################
    def mousePressEvent(self, event):
        if event.buttons() == QtCore.Qt.LeftButton:
            width = self.rectForIndex(self.indexFromItem(self.itemAt(event.pos()))).width()
            x = event.pos().x()
            if width > 0 and x * 100 / width > 70:
                print 'heyyyyyyyyyy'
        return QtGui.QListWidget.mousePressEvent(self, event)


#####################################################################
class Browser(QtGui.QWidget):
    #####################################################################
    def __init__(self, mother):
        super(Browser, self).__init__(mother)
        self.add_layout()

    #####################################################################
    def add_layout(self):
        layout = QtGui.QVBoxLayout()

        self.audio_list = AudioListWidget()
        self.audio_list.add('hello')
        layout.addWidget(self.audio_list)

        self.setLayout(layout)



app = QtGui.QApplication(sys.argv)

browser = Browser(None)
browser.show()
thread = MyThread(browser.audio_list.item(0))
thread.start()

app.exec_()