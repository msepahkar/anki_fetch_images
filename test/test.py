from PyQt4 import QtGui, QtCore
import sys
import time


class ProgressChord:
    # ===========================================================================#########
    def __init__(self, center_x, center_y, radius, progress=0):
        self.center_x = center_x
        self.center_y = center_y
        self.radius = radius
        rect_x = self.center_x - self.radius
        rect_y = self.center_y - self.radius
        rect_width = self.radius * 2
        rect_height = self.radius * 2
        self.rect = QtCore.QRect(rect_x, rect_y, rect_width, rect_height)
        self.progress = progress
        self.start_angle = 0
        self.span_angle = 0
        self.update_progress(self.progress)

    # ===========================================================================#########
    def update_progress(self, progress):
        self.progress = progress
        angle = 180 - self.progress * 180 / 100
        self.start_angle = angle * 16
        self.span_angle = (180 - angle) * 2 * 16
        print angle, self.span_angle / 16

# ===========================================================================#########
class MyThread(QtCore.QThread):
    def __init__(self, item):
        super(MyThread, self).__init__()
        self.item = item

    # ===========================================================================
    def run(self):
        for progress in range(101):
            self.item.update_progress(progress)
            time.sleep(0.05)

# ===========================================================================#########
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
        radius = 60

        painter.setPen(QtGui.QPen(QtCore.Qt.black))
        painter.drawLine(center_x, center_y, center_x - 2 * radius, center_y)
        # progress_chord = ProgressChord(center_x, center_y, radius, self.list_widget.item(0).progress)
        #
        # painter.setBrush(QtGui.QBrush(QtCore.Qt.green))
        # painter.drawChord(progress_chord.rect, progress_chord.start_angle, progress_chord.span_angle)

        painter.restore()


# ===========================================================================
class AudioListWidgetItem(QtGui.QListWidgetItem):
    # ===========================================================================
    def __init__(self, url):
        super(AudioListWidgetItem, self).__init__()
        self.setSizeHint(QtCore.QSize(200,100))
        self.url = url

    # ===========================================================================
    def update_progress(self, progress):
        self.progress = progress
        self.setText(str(self.progress))


# ===========================================================================
class AudioListWidget(QtGui.QListWidget):

    # ===========================================================================
    def __init__(self, parent=None):
        super(AudioListWidget, self).__init__(parent)

        de = AudioListWidgetItemDelegate(self)

        # model = QtGui.QStandardItemModel()  # declare model
        # self.setModel(model)  # assign model to table view

        self.setItemDelegate(de)

    # ===========================================================================
    def add(self, url):
        for i in range(self.count()):
            if self.item(i).url == url:
                return
        item = AudioListWidgetItem(url)
        self.addItem(item)
        # item.add_button()

    # ===========================================================================
    def mousePressEvent(self, event):
        if event.buttons() == QtCore.Qt.LeftButton:
            width = self.rectForIndex(self.indexFromItem(self.itemAt(event.pos()))).width()
            x = event.pos().x()
            if width > 0 and x * 100 / width > 70:
                print 'heyyyyyyyyyy'
        return QtGui.QListWidget.mousePressEvent(self, event)


# ===========================================================================
class Browser(QtGui.QWidget):
    # ===========================================================================
    def __init__(self, mother):
        super(Browser, self).__init__(mother)
        self.add_layout()

    # ===========================================================================
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