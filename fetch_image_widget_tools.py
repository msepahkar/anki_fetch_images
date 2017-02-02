# -*- coding: utf-8 -*-

import tempfile
import pygame
import os
from PyQt4 import QtGui, QtCore
import ImageQt
import threading
from PyQt4 import QtWebKit
from PIL.ImageQt import ImageQt
from fetch_image_general_tools import enum, OperationResult, Language, ImageType
from fetch_image_thread_tools import ThreadFetchAudio, ThreadFetchImage, ThreadFetchImageUrls


#####################################################################
class GraphicsView(QtGui.QGraphicsView):
    #####################################################################
    def __init__(self, number, w, h, main_dialog, parent=None):
        super(GraphicsView, self).__init__(parent)
        self.main_dialog = main_dialog
        self.setTransformationAnchor(QtGui.QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QtGui.QGraphicsView.AnchorUnderMouse)
        self.setMouseTracking(True)
        self.parent = parent
        self.scene = QtGui.QGraphicsScene()
        self.url = None
        self.scene.setBackgroundBrush(QtCore.Qt.white)
        self.setScene(self.scene)
        self.setSceneRect(0, 0, w, h)
        self.number = number
        self.resize(w, h)
        self.image = None

    #####################################################################
    def resizeEvent(self, event):
        self.fit()

    #####################################################################
    def fit(self):
        if self.scene is not None:
            rect = QtCore.QRectF(self.sceneRect())
            if not rect.isNull():
                unity = self.transform().mapRect(QtCore.QRectF(0, 0, 1, 1))
                self.scale(1 / unity.width(), 1 / unity.height())
                viewrect = self.viewport().rect()
                scenerect = self.transform().mapRect(rect)
                factor = min((self.size().width() - 10) / scenerect.width(),
                             (self.size().height() - 10) / scenerect.height())
                self.scale(factor, factor)
                self.centerOn(rect.center())

    #####################################################################
    def display_image(self, image_number, image):
        self.scene.clear()
        # w, h = image.size
        self.imgQ = ImageQt(image)  # we need to hold reference to imgQ, or it will crash
        self.pixMap = QtGui.QPixmap.fromImage(self.imgQ)#self.imgQ)
        self.scene.addPixmap(self.pixMap)
        # self.fitInView(QtCore.QRectF(0, 0, w, h), QtCore.Qt.KeepAspectRatio)
        self.scene.update()

    #####################################################################
    def contextMenuEvent(self, QContextMenuEvent):
        menu = QtGui.QMenu(self)

        Action = menu.addAction("set this image")
        Action.triggered.connect(self.set_image)

        menu.exec_(self.mapToGlobal(QContextMenuEvent.pos()))

    #####################################################################
    def set_image(self):
        # full_base_name = os.path.join(self.main_dialog.media_dir, self.main_dialog.word)
        # full_f_name = full_base_name + ".png"
        # if os.path.exists(full_f_name):
        #     i = 0
        #     while os.path.exists(full_f_name):
        #         i += 1
        #         full_f_name = full_base_name + '_' + str(i) + '.png'
        # self.main_dialog.full_image_file_name = full_f_name
        self.main_dialog.selected_image = self.image
        # self.image.save(full_f_name)


#####################################################################
class Widget(QtGui.QWidget):
    #####################################################################
    def __init__(self, mother, parent=None):
        super(Widget, self).__init__(parent)
        self.mother = mother


#####################################################################
class Dialog(QtGui.QDialog):
    #####################################################################
    def __init__(self, mother, parent=None):
        super(Dialog, self).__init__(parent)
        self.mother = mother


#####################################################################
class TabWidget(QtGui.QTabWidget):
    #####################################################################
    def __init__(self, mother, closable=False, parent=None):
        super(TabWidget, self).__init__(parent)
        self.mother = mother
        self.tabBar().setTabsClosable(closable)
        self.label = ''

    #####################################################################
    def addTab(self, QWidget, label):
        super(TabWidget, self).addTab(QWidget, label)
        QWidget.label = label


#####################################################################
class TabWidgetProgress(TabWidget, OperationResult):
    #####################################################################
    def __init__(self, mother, closable=False, parent=None):
        TabWidget.__init__(self, mother, closable, parent)
        OperationResult.__init__(self)

    #####################################################################
    def update_progress(self):
        mother = self.mother
        if type(mother) is not TabWidgetProgress:
            return
        index = mother.indexOf(self)
        tab_bar = mother.tabBar()

        self.failed = False
        self.succeeded = False
        self.in_progress = False
        self.progress = 0

        total_started = 0
        total_failed = 0
        total_succeeded = 0
        total_in_progress = 0

        for i in range(self.count()):
            if self.widget(i).started:
                total_started += 1
            if self.widget(i).failed:
                total_failed += 1
            if self.widget(i).succeeded:
                total_succeeded += 1
                self.progress += 100
            if self.widget(i).in_progress:
                total_in_progress += 1
                self.progress += self.widget(i).progress

        if total_in_progress + total_succeeded > 0:
            self.progress /= (total_in_progress + total_succeeded)

        # all started
        if total_started == self.count():
            self.started = True
            tab_bar.setTabText(index, self.label)
            tab_bar.setTabTextColor(index, OperationResult.started_color)
        # all failed
        elif total_failed == self.count():
            self.failed = True
            tab_bar.setTabText(index, self.label)
            tab_bar.setTabTextColor(index, OperationResult.failed_color)
        # all succeeded
        elif total_succeeded == self.count():
            self.succeeded = True
            tab_bar.setTabText(index, self.label)
            tab_bar.setTabTextColor(index, OperationResult.succeeded_color)
        # all in progress
        elif total_in_progress == self.count():
            self.in_progress = True
            tab_bar.setTabText(index, self.label + ' ' + str(self.progress) + '%')
            tab_bar.setTabTextColor(index, OperationResult.in_progress_color)
        # at least one in progress
        elif total_in_progress > 0:
            self.in_progress = True
            tab_bar.setTabText(index, self.label + ' ' + str(self.progress) + '%')
            # any failed or any started?
            if total_failed > 0 or total_started > 0:
                tab_bar.setTabTextColor(index, OperationResult.weak_in_progress_color)
            # no fail and no started
            else:
                tab_bar.setTabTextColor(index, OperationResult.in_progress_color)
        # nothing in progress, but at least one started
        elif total_started > 0:
            self.started = True
            tab_bar.setTabText(index, self.label)
            tab_bar.setTabTextColor(index, OperationResult.started_color)
        # nothing in progress and nothing started, but at least one succeeded
        elif total_succeeded > 0:
            self.succeeded = True
            # any failed?
            if total_failed > 0:
                tab_bar.setTabText(index, self.label)
                tab_bar.setTabTextColor(index, OperationResult.weak_succeeded_color)
            # no fail
            else:
                tab_bar.setTabText(index, self.label)
                tab_bar.setTabTextColor(index, OperationResult.succeeded_color)

        mother.update_progress()


####################################################################
class AudioListWidgetItemDelegate(QtGui.QItemDelegate, QtGui.QStandardItem):
    def __init__(self, list_widget, parent=None):
        QtGui.QItemDelegate.__init__(self, parent)
        self.list_widget = list_widget

    def paint(self, painter, option, index):
        painter.save()

        # set background color
        painter.setPen(QtGui.QPen(QtCore.Qt.NoPen))
        # if option.state & QtGui.QStyle.State_Selected:
        #     painter.setBrush(QtGui.QBrush(QtCore.Qt.red))
        # else:
        #     painter.setBrush(QtGui.QBrush(QtCore.Qt.white))
        # painter.drawRect(option.rect)

        item = self.list_widget.item(index.row())

        opt = QtGui.QStyleOptionProgressBar()
        opt.rect = QtCore.QRect(0, option.rect.height() * index.row(), option.rect.width(), option.rect.height())
        opt.minimum = 0
        opt.maximum = 100
        opt.progress = item.progress
        self.list_widget.style().drawControl(QtGui.QStyle.CE_ProgressBar, opt, painter)

        if item.status == AudioListWidget.Status.fetching:
            opt = QtGui.QStyleOptionButton()
            opt.text = 'cancel'
            font = QtGui.QFont("times", 8)
            fm = QtGui.QFontMetrics(font)
            opt.fontMetrics = fm
            # opt.icon = QtGui.QIcon('cancel_button_icon.jpg')
            opt.iconsize = QtCore.QSize(2, 2)
            opt.rect = QtCore.QRect(option.rect.width() * 4 / 5, option.rect.height() * index.row(), option.rect.width(), option.rect.height())

            self.list_widget.style().drawControl(QtGui.QStyle.CE_PushButton, opt, painter)

        # set text color
        painter.setPen(QtGui.QPen(QtCore.Qt.black))
        painter.drawText(option.rect, QtCore.Qt.AlignLeft, item.url)
        # set text color
        painter.setPen(QtGui.QPen(QtCore.Qt.green))
        painter.drawText(option.rect, QtCore.Qt.AlignRight, AudioListWidget.Status.names[item.status])

        # item.widget_button.resize(option.rect.width(), option.rect.height())
        # item.progress_bar.resize(option.rect.width(), option.rect.height())

        painter.restore()


#####################################################################
class AudioListWidgetItem(QtGui.QListWidgetItem):
    #####################################################################
    def __init__(self, url):
        super(AudioListWidgetItem, self).__init__()
        self.url = url
        f = tempfile.NamedTemporaryFile(delete=False)
        f.close()
        self.audio_file = f.name
        self.status = AudioListWidget.Status.discovered
        self.set_status(self.status)
        self.progress = 0
        self.fetching_thread = ThreadFetchAudio(url, f.name)
        QtCore.QObject.connect(self.fetching_thread, ThreadFetchAudio.signal_audio_fetched, self.audio_fetched)
        QtCore.QObject.connect(self.fetching_thread, ThreadFetchAudio.signal_audio_fetching_progress, self.update_progress)

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
        if self.status == AudioListWidget.Status.fetching:
            return
        if self.status == AudioListWidget.Status.fetched:
            self.play_audio()
            return
        print 'loading audio for:', self.url
        self.set_status(AudioListWidget.Status.fetching)
        self.fetching_thread.start()

    #####################################################################
    def play_audio(self):
        print 'playing audio for: ', self.url
        pygame.mixer.music.load(self.audio_file)
        pygame.mixer.music.play()


#####################################################################
class AudioListWidget(QtGui.QListWidget):
    Status = enum(empty=1, discovered=2, fetching=3, fetched=4, failed=5)

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
class InlineBrowser(QtWebKit.QWebView):
    InfoType = enum(dictionary=1, image=2, dictionary_image=3)
    SignalType = enum(started=1, progress=2, finished=3)

    #####################################################################
    def __init__(self, mother, parent=None):
        super(InlineBrowser, self).__init__(parent)
        self.mother = mother

    #####################################################################
    def contextMenuEvent(self, event):
        word = str(self.selectedText())

        menu = QtGui.QMenu(self)
        sub_menu_definition = QtGui.QMenu(menu)
        sub_menu_definition.setTitle('definition for "{}"'.format(word))
        menu.addMenu(sub_menu_definition)
        sub_menu_image = QtGui.QMenu(menu)
        sub_menu_image.setTitle('image for "{}"'.format(word))
        menu.addMenu(sub_menu_image)
        sub_menu_definition_image = QtGui.QMenu(menu)
        sub_menu_definition_image.setTitle('definition and image for "{}"'.format(word))
        menu.addMenu(sub_menu_definition_image)


        menu_item = sub_menu_definition.addAction('english')
        menu_item.triggered.connect(lambda: self.fetch_this_word(word, Language.english, InlineBrowser.InfoType.dictionary))

        menu_item = sub_menu_definition.addAction('german')
        menu_item.triggered.connect(lambda: self.fetch_this_word(word, Language.german, InlineBrowser.InfoType.dictionary))

        menu_item = sub_menu_image.addAction('english')
        menu_item.triggered.connect(lambda: self.fetch_this_word(word, Language.english, InlineBrowser.InfoType.image))

        menu_item = sub_menu_image.addAction('german')
        menu_item.triggered.connect(lambda: self.fetch_this_word(word, Language.german, InlineBrowser.InfoType.image))

        menu_item = sub_menu_definition_image.addAction('english')
        menu_item.triggered.connect(lambda: self.fetch_this_word(word, Language.english, InlineBrowser.InfoType.dictionary_image))

        menu_item = sub_menu_definition_image.addAction('german')
        menu_item.triggered.connect(lambda: self.fetch_this_word(word, Language.german, InlineBrowser.InfoType.dictionary_image))

        menu.exec_(self.mapToGlobal(event.pos()))

    #####################################################################
    def fetch_this_word(self, word, language, info_type):
        if word:
            mother = self.mother
            while mother.mother:
                mother = mother.mother
            if info_type == InlineBrowser.InfoType.dictionary or info_type == InlineBrowser.InfoType.dictionary_image:
                mother.add_dictionary_tabs(word, language)
            if info_type == InlineBrowser.InfoType.image or info_type == InlineBrowser.InfoType.dictionary_image:
                mother.add_image_tabs(word, language)


#####################################################################
class Browser(Widget):
    signal_started = QtCore.SIGNAL("Browser.started")
    signal_progress = QtCore.SIGNAL("Browser.progress")
    signal_finished = QtCore.SIGNAL("Browser.finished")
    #####################################################################
    def __init__(self, mother):
        super(Browser, self).__init__(mother)
        self.add_layout()
        self.inline_browser.loadStarted.connect(self.started)
        self.inline_browser.loadProgress.connect(self.progress)
        self.inline_browser.loadFinished.connect(self.finished)
        self.inline_browser.page().networkAccessManager().finished.connect(self.url_discovered)

    #####################################################################
    def add_layout(self):
        header_layout = QtGui.QHBoxLayout()

        button = QtGui.QPushButton(u"◀")
        button.setFixedSize(35, 30)
        button.setStyleSheet("font-size:18px;")
        header_layout.addWidget(button)
        button.clicked.connect(self.backward)

        button = QtGui.QPushButton(u"▶")
        button.setFixedSize(35, 30)
        button.setStyleSheet("font-size:18px;")
        header_layout.addWidget(button)
        button.clicked.connect(self.forward)

        button = QtGui.QPushButton(u'✘')
        button.setFixedSize(35, 30)
        button.setStyleSheet("font-size:18px;")
        header_layout.addWidget(button)
        button.clicked.connect(self.stop)

        button = QtGui.QPushButton(u"↻")
        button.setFixedSize(35, 30)
        button.setStyleSheet("font-size:18px;")
        header_layout.addWidget(button)
        button.clicked.connect(self.reload)

        self.address_line = QtGui.QLineEdit()
        header_layout.addWidget(self.address_line)

        button = QtGui.QPushButton(u'✔')
        button.setFixedSize(35, 30)
        button.setStyleSheet("font-size:18px;")
        header_layout.addWidget(button)
        button.clicked.connect(self.go)

        layout = QtGui.QVBoxLayout()
        layout.addLayout(header_layout)

        self.inline_browser = InlineBrowser(self)
        self.inline_browser.urlChanged.connect(self.update_address_line)

        layout.addWidget(self.inline_browser)

        self.audio_list = AudioListWidget()
        layout.addWidget(self.audio_list)

        self.setLayout(layout)

    #####################################################################
    def started(self):
        self.emit(Browser.signal_started)

    #####################################################################
    def progress(self, progress):
        self.emit(Browser.signal_progress, progress)

    #####################################################################
    def finished(self, ok):
        self.emit(Browser.signal_finished, ok)

    #####################################################################
    def stop(self):
        self.inline_browser.stop()

    #####################################################################
    def forward(self):
        self.inline_browser.forward()

    #####################################################################
    def backward(self):
        self.inline_browser.back()

    #####################################################################
    def reload(self):
        self.inline_browser.reload()

    #####################################################################
    def update_address_line(self, url):
        self.address_line.setText(url.toString())

    #####################################################################
    def go(self, url = None):
        if url:
            self.address_line.setText(url)
        url = QtCore.QUrl(self.address_line.text())
        self.inline_browser.load(url)

    #####################################################################
    def url_discovered(self, reply):

        url = reply.url().toString()
        if url.endsWith('mp3'):
            self.audio_list.add(url)
        else:
            headers = reply.rawHeaderPairs()
            for header in headers:
                if header[1].contains('audio'):
                    self.audio_list.add(url)

    #####################################################################
    def quit(self):
        self.inline_browser.stop()
        print 'removing temp files ...'
        for audio_file in self.audio_list.audio_files:
            if os.path.exists(audio_file):
                os.remove(audio_file)
                print audio_file, 'removed.'


#####################################################################
class DictionaryTab(Widget, OperationResult):
    dictionaries = dict()
    dictionaries[Language.english] = [('google translate', 'https://translate.google.com/#en/fa/'),
                                      ('vocabulary.com', 'https://www.vocabulary.com/dictionary/'),
                                      ('webster', 'https://www.merriam-webster.com/dictionary/'),
                                      ('oxford', 'https://en.oxforddictionaries.com/definition/us/'),
                                      ('forvo', 'https://forvo.com/search/')]
    dictionaries[Language.german] = [('google translate', 'https://translate.google.com/#de/fa/'),
                                     ('dict.cc', 'http://www.dict.cc/?s='),
                                     ('leo.org', 'http://dict.leo.org/german-english/'),
                                     ('collins', 'https://www.collinsdictionary.com/dictionary/german-english/'),
                                     ('duden', 'http://www.duden.de/suchen/dudenonline/'),
                                     ('forvo', 'https://forvo.com/search/')]

    #####################################################################
    def __init__(self, address_pair, mother, parent=None):
        Widget.__init__(self, mother, parent)
        OperationResult.__init__(self)
        self.name = address_pair[0]
        self.web_address = address_pair[1]
        self.word = None
        self.browser = Browser(self)
        self.connect(self.browser, Browser.signal_started, lambda: self.update_status(InlineBrowser.SignalType.started))
        self.connect(self.browser, Browser.signal_progress, lambda progress: self.update_status(InlineBrowser.SignalType.progress, progress))
        self.connect(self.browser, Browser.signal_finished, lambda ok: self.update_status(InlineBrowser.SignalType.finished, ok))
        self.vertical_layout = QtGui.QVBoxLayout(self)
        self.vertical_layout.addWidget(self.browser)

    #####################################################################
    def browse(self, word):
        self.word = word
        word = word.split()
        word = '+'.join(word)
        url = self.web_address + word
        self.browser.go(url)

    #####################################################################
    def update_status(self, singal_type, param=None):
        name = self.name
        tab_dictionaries = self.mother
        index = tab_dictionaries.indexOf(self)
        tab_bar = tab_dictionaries.tabBar()
        if singal_type == InlineBrowser.SignalType.started:
            self.progress = 0
            tab_bar.setTabTextColor(index, OperationResult.started_color)
            tab_dictionaries.update_progress()
        if singal_type == InlineBrowser.SignalType.progress:
            progress = param
            self.in_progress = True
            self.progress = progress
            tab_bar.setTabText(index, name + ' ' + str(progress) + '%')
            tab_bar.setTabTextColor(index, OperationResult.in_progress_color)
            tab_dictionaries.update_progress()
        if singal_type == InlineBrowser.SignalType.finished:
            ok = param
            tab_bar.setTabText(index, name)
            if ok:
                self.progress = 100
                self.succeeded = True
                tab_bar.setTabTextColor(index, OperationResult.succeeded_color)
            else:
                self.failed = True
                tab_bar.setTabTextColor(index, OperationResult.failed_color)
            tab_dictionaries.update_progress()

    #####################################################################
    def quit(self):
        self.browser.quit()
        print('dictionary {} quited.'.format(self.name))


#####################################################################
class ImageTab(Widget, OperationResult):
    SignalType = enum(urls_fetched=1, urls_fetching_started=2, image_fetched=3, image_ignored=4)
    NUMBER_OF_IMAGES_IN_EACH_RAW = 5
    NUMBER_OF_IMAGE_FETCHING_THREADS_PER_URL = 5

    #####################################################################
    def __init__(self, word, language, image_type, mother, parent=None):
        Widget.__init__(self, mother, parent)
        OperationResult.__init__(self)
        self.quit_request = False
        self.n_urls = 0
        self.n_fetched = 0
        self.n_ignored = 0
        self.word = word
        self.language = language
        self.image_type = image_type
        self.add_layout()
        self.threads_fetch_image = []
        self.thread_fetch_image_urls = ThreadFetchImageUrls(self.word, self.language, self.image_type)
        self.connect(self.thread_fetch_image_urls, ThreadFetchImageUrls.signal_urls_fetched, self.fetch_images)
        self.connect(self.thread_fetch_image_urls, ThreadFetchImageUrls.signal_urls_fetched,
                     lambda urls: self.update_status(ImageTab.SignalType.urls_fetched, urls))
        self.connect(self.thread_fetch_image_urls, ThreadFetchImageUrls.signal_urls_fetching_started,
                     lambda : self.update_status(ImageTab.SignalType.urls_fetching_started))

    ###########################################################
    def add_layout(self):
        # scroll area
        self.scroll_area = QtGui.QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area_widget_contents = Widget(mother=self, parent=self.scroll_area)
        self.scroll_area_widget_contents.setGeometry(QtCore.QRect(0, 0, 50, 100))
        self.scroll_area.setWidget(self.scroll_area_widget_contents)

        # layouts
        # base vertical layout
        self.vertical_layout = QtGui.QVBoxLayout(self)

        self.vertical_layout.addWidget(self.scroll_area)
        # scrollable vertical layout
        self.vertical_layout_scroll = QtGui.QVBoxLayout(self.scroll_area_widget_contents)
        # horizontal layouts
        self.horizontal_layouts = []
        # first row of images
        self.horizontal_layouts.append(QtGui.QHBoxLayout())
        self.vertical_layout_scroll.addLayout(self.horizontal_layouts[-1])

    ###########################################################
    def fetch_images(self, image_urls):
        if self.quit_request or len(image_urls) == 0:
            return
        lock = threading.Lock()
        # threads
        for i in range(ImageTab.NUMBER_OF_IMAGE_FETCHING_THREADS_PER_URL):
            self.threads_fetch_image.append(ThreadFetchImage(image_urls, lock))
            self.connect(self.threads_fetch_image[-1], ThreadFetchImage.signal_image_fetched, self.add_fetched_image)
            self.connect(self.threads_fetch_image[-1], ThreadFetchImage.signal_image_fetched,
                         lambda image_number, image: self.update_status(ImageTab.SignalType.image_fetched, image_number))
            self.connect(self.threads_fetch_image[-1], ThreadFetchImage.signal_image_ignored,
                         lambda image_number: self.update_status(ImageTab.SignalType.image_ignored, image_number))
            self.threads_fetch_image[-1].start()

    ###########################################################
    def add_fetched_image(self, image_number, image):
        if self.quit_request:
            return
        view = GraphicsView(1, image.size[0], image.size[1], self)
        view.image = image
        view.setMinimumHeight(image.size[1] / 2)
        view.display_image(image_number, image)
        view.image_number = image_number
        view.fit()
        done = False
        for horizontal_layout in self.horizontal_layouts:
            if horizontal_layout.count() >= ImageTab.NUMBER_OF_IMAGES_IN_EACH_RAW:
                continue
            horizontal_layout.addWidget(view)
            done = True
        if not done:
            horizontal_layout = QtGui.QHBoxLayout()
            self.horizontal_layouts.append(horizontal_layout)
            self.vertical_layout_scroll.addLayout(self.horizontal_layouts[-1])
            horizontal_layout.addWidget(view)

    #####################################################################
    def update_status(self, signal_type, param=None):
        tab_images = self.mother
        index = tab_images.indexOf(self)
        tab_bar = tab_images.tabBar()

        if signal_type == ImageTab.SignalType.urls_fetching_started:
            self.started = True
            self.n_urls = 0
            self.n_fetched = 0
            self.n_ignored = 0
            self.progress = 0
            tab_bar.setTabText(index, ImageType.names[self.image_type])
            tab_bar.setTabTextColor(index, OperationResult.started_color)

        if signal_type == ImageTab.SignalType.urls_fetched:
            urls = param
            self.n_urls = len(urls)
            if self.n_urls == 0:
                self.failed = True
                tab_bar.setTabText(index, ImageType.names[self.image_type])
                tab_bar.setTabTextColor(index, OperationResult.failed_color)
            else:
                self.in_progress = True
                tab_bar.setTabText(index, ImageType.names[self.image_type] + ' ' + str(self.progress) + '%')
                tab_bar.setTabTextColor(index, OperationResult.in_progress_color)

        if signal_type == ImageTab.SignalType.image_fetched:
            self.n_fetched += 1
            self.progress = (self.n_fetched + self.n_ignored) * 100 / self.n_urls
            if self.progress < 100:
                tab_bar.setTabText(index, ImageType.names[self.image_type] + ' ' + str(self.progress) + '%')
                tab_bar.setTabTextColor(index, OperationResult.in_progress_color)
            else:
                tab_bar.setTabText(index, ImageType.names[self.image_type])
                tab_bar.setTabTextColor(index, OperationResult.succeeded_color)

        if signal_type == ImageTab.SignalType.image_ignored:
            self.n_ignored += 1
            self.progress = (self.n_fetched + self.n_ignored) * 100 / self.n_urls
            if self.progress < 100:
                tab_bar.setTabText(index, ImageType.names[self.image_type] + ' ' + str(self.progress) + '%')
                tab_bar.setTabTextColor(index, OperationResult.in_progress_color)
            else:
                tab_bar.setTabText(index, ImageType.names[self.image_type])
                tab_bar.setTabTextColor(index, OperationResult.succeeded_color)

        tab_images.update_progress()

    ###########################################################
    def quit(self):
        self.quit_request = True
        self.thread_fetch_image_urls.quit()
        for thread in self.threads_fetch_image:
            thread.quit()
        print('image tab {} {} quitted'.format(self.word, self.image_type))

    ###########################################################
    def terminate(self):
        self.quit_request = True
        self.thread_fetch_image_urls.terminate()
        for thread in self.threads_fetch_image:
            thread.terminate()
        print('image tab {} {} terminated'.format(self.word, self.image_type))

    ###########################################################
    def start_fetching(self):
        self.thread_fetch_image_urls.start()
        self.started = True


