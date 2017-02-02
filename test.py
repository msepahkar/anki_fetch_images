from PyQt4 import QtGui, QtCore
import sys

####################################################################
class AudioListWidgetItemDelegate(QtGui.QItemDelegate):
    def __init__(self, list_widget, parent=None):
        QtGui.QItemDelegate.__init__(self, parent)
        self.list_widget = list_widget

    def paint(self, painter, option, index):
        painter.save()

        # set background color
        painter.setPen(QtGui.QPen(QtCore.Qt.NoPen))

        opt = QtGui.QStyleOptionButton()
        opt.text = 'cancel'
        font = QtGui.QFont("times", 8)
        fm = QtGui.QFontMetrics(font)
        opt.fontMetrics = fm
        # opt.icon = QtGui.QIcon('cancel_button_icon.jpg')
        opt.iconsize = QtCore.QSize(2, 2)
        opt.rect = QtCore.QRect(option.rect.width() * 4 / 5, option.rect.height() * index.row(), option.rect.width(), option.rect.height())

        self.list_widget.style().drawControl(QtGui.QStyle.CE_PushButton, opt, painter)

        painter.restore()


#####################################################################
class AudioListWidgetItem(QtGui.QListWidgetItem):
    #####################################################################
    def __init__(self, url):
        super(AudioListWidgetItem, self).__init__()
        self.url = url

    #####################################################################
    def add_button(self):
        # Create widget
        self.widget = QtGui.QWidget()
        self.widget_button = QtGui.QPushButton("Push Me")
        self.widget_button.clicked.connect(self.set_progress_bar_value)
        self.progress_bar = QtGui.QProgressBar()
        self.progress_bar.setRange(0,100)
        self.progress_bar.setValue(1)
        widget_layout = QtGui.QHBoxLayout()
        widget_layout.addWidget(self.widget_button)
        widget_layout.addWidget(self.progress_bar)
        widget_layout.addStretch()

        widget_layout.setSizeConstraint(QtGui.QLayout.SetFixedSize)
        self.widget.setLayout(widget_layout)
        # self.widget.setMaximumHeight(self.sizeHint().height())
        # self.setSizeHint(widget.sizeHint())

        # Add widget to QListWidget funList
        self.listWidget().setItemWidget(self, self.widget)

    #####################################################################
    def set_progress_bar_value(self):
        self.progress_bar.setValue(self.progress_bar.value() + 2)

    #####################################################################
    def audio_fetched(self, ok):
        if ok:
            self.set_status(AudioListWidget.Status.fetched)
            self.play_audio()
        else:
            self.set_status(AudioListWidget.Status.failed)

    #####################################################################
    def set_status(self, status):
        self.status = status
        self.setText(AudioListWidget.Status.names[self.status] + ':  ' + self.url)

    #####################################################################
    def update_progress(self, current_bytes, total_bytes):
        self.progress = current_bytes * 100 / total_bytes
        self.setText(str(self.progress))
        # self.progress_bar.setValue(self.progress)

    #####################################################################
    def load_audio(self):
        pass

    #####################################################################
    def play_audio(self):
        print 'playing audio for: ', self.url
        pygame.mixer.music.load(self.audio_file)
        pygame.mixer.music.play()


#####################################################################
class AudioListWidget(QtGui.QListWidget):

    #####################################################################
    def __init__(self, parent=None):
        super(AudioListWidget, self).__init__(parent)

        self.itemClicked.connect(self.load_audio)
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
    def load_audio(self, item):
        item.load_audio()

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

app.exec_()