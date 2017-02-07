# -*- coding: utf-8 -*-

import tempfile
import pygame
import os
import math
from PyQt4 import QtGui, QtCore
from PyQt4 import QtWebKit
from fetch_image_tools.general_tools import enum, OperationResult, Language
from fetch_image_tools.thread_tools import ThreadFetchAudio
from fetch_image_tools.widget_tools import Widget


class ProgressCircle:
    ####################################################################
    def __init__(self, option, index):
        radius = option.rect.height() / 2
        center_x = option.rect.width() - radius
        center_y = option.rect.height() * index.row() + option.rect.height() / 2
        rect_x = center_x - radius
        rect_y = center_y - radius
        rect_width = radius * 2
        rect_height = radius * 2
        self.rect = QtCore.QRect(rect_x, rect_y, rect_width, rect_height)
        x1 = center_x - float(radius) / math.sqrt(2)
        y1 = center_y - float(radius) / math.sqrt(2)
        x2 = center_x + float(radius) / math.sqrt(2)
        y2 = center_y + float(radius) / math.sqrt(2)
        line1 = QtCore.QLine(x1, y1, x2, y2)
        line2 = QtCore.QLine(x2, y1, x1, y2)
        self.lines = [line1, line2]
        self.start_angle = 0
        self.span_angle = 0

    ####################################################################
    def update_progress(self, progress):
        angle = 180 - progress * 180 / 100
        self.start_angle = angle * 16
        self.span_angle = (180 - angle) * 2 * 16

    ####################################################################
    def is_inside(self, pos):
        if self.rect.x() <= pos.x() <= self.rect.x() + self.rect.width():
            if self.rect.y() <= pos.y() <= self.rect.y() + self.rect.height():
                return True
        return False


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

        item.progress_circle = ProgressCircle(option, index)

        if item.status == AudioListWidget.Status.discovered:
            painter.setBrush(QtGui.QBrush(QtCore.Qt.gray))
            painter.drawEllipse(item.progress_circle.rect)

        elif item.status == AudioListWidget.Status.fetching:
            painter.setPen(QtGui.QPen(QtCore.Qt.black))
            painter.setBrush(QtGui.QBrush(QtCore.Qt.yellow))
            painter.drawEllipse(item.progress_circle.rect)

            painter.setBrush(QtGui.QBrush(QtCore.Qt.green))
            item.progress_circle.update_progress(item.progress)
            painter.drawChord(item.progress_circle.rect,
                              item.progress_circle.start_angle,
                              item.progress_circle.span_angle)

            painter.setPen(QtGui.QPen(QtCore.Qt.black))
            painter.drawLines(item.progress_circle.lines)

        elif item.status == AudioListWidget.Status.fetched:
            painter.setBrush(QtGui.QBrush(QtCore.Qt.green))
            painter.drawEllipse(item.progress_circle.rect)

        elif item.status == AudioListWidget.Status.failed:
            painter.setBrush(QtGui.QBrush(QtCore.Qt.red))
            painter.drawEllipse(item.progress_circle.rect)

        # set text color
        painter.setPen(QtGui.QPen(QtCore.Qt.black))
        painter.drawText(option.rect, QtCore.Qt.AlignLeft, item.url)

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
        self._status = AudioListWidget.Status.discovered
        self.setText(AudioListWidget.Status.names[self._status])
        self.progress = 0
        self.progress_circle = None
        self.thread = ThreadFetchAudio(url, f.name)
        QtCore.QObject.connect(self.thread, ThreadFetchAudio.signal_audio_fetched, self.audio_fetched)
        QtCore.QObject.connect(self.thread, ThreadFetchAudio.signal_audio_fetching_progress, self.update_progress)

    #####################################################################
    @property
    def status(self):
        return self._status

    #####################################################################
    def audio_fetched(self, ok):
        if ok:
            self.update_status(AudioListWidget.Status.fetched)
            self.play_audio()
        else:
            self.update_status(AudioListWidget.Status.failed)

    #####################################################################
    def update_status(self, status):
        self._status = status
        self.setText(AudioListWidget.Status.names[self._status])

    #####################################################################
    def update_progress(self, current_bytes, total_bytes):
        self.progress = current_bytes * 100 / total_bytes
        self.setText(str(self.progress))

    #####################################################################
    def load_audio(self):
        if self._status == AudioListWidget.Status.failed:
            return
        if self.thread.isRunning():
            return
        if self._status == AudioListWidget.Status.fetched:
            self.play_audio()
            return
        self.update_status(AudioListWidget.Status.fetching)
        self.thread.start()

    #####################################################################
    def reload_audio(self):
        if self.thread.isRunning():
            return
        if self._status == AudioListWidget.Status.fetched:
            self.play_audio()
            return
        self.update_status(AudioListWidget.Status.fetching)
        self.thread.start()

    #####################################################################
    def stop_loading_audio(self):
        if self._status == AudioListWidget.Status.fetching:
            self.thread.quit()
            self.thread.stop()
            self.update_status(AudioListWidget.Status.failed)

    #####################################################################
    def play_audio(self):
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
            item = self.itemAt(event.pos())
            if item and item.progress_circle and item.progress_circle.is_inside(event.pos()):
                if item.status == AudioListWidget.Status.fetching:
                    item.stop_loading_audio()
                else:
                    item.reload_audio()
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
        for i in range(self.audio_list.count()):
            item = self.audio_list.item(i)
            item.thread.quit()
            if os.path.exists(item.audio_file):
                os.remove(item.audio_file)

    #####################################################################
    def terminate(self):
        for i in range(self.audio_list.count()):
            item = self.audio_list.item(i)
            item.thread.terminate()


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

    #####################################################################
    def terminate(self):
        self.browser.terminate()


