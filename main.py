import time
import math
from bs4 import BeautifulSoup
import requests
import re
import urllib2, urllib
import os
import cookielib
import json
from StringIO import StringIO
from PyQt4 import QtGui, QtCore
import sys
import ImageQt
import Image
import threading
from PyQt4 import QtWebKit
from PIL.ImageQt import ImageQt
import PIL


#####################################################################
def enum(**enums):
    return type('Enum', (), enums)

#####################################################################
Language = enum(english=1, german=2)


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
class ThreadQuitException(Exception):
    pass


#####################################################################
class ThreadFetchImage(QtCore.QThread):
    # *************************
    def __init__(self, image_urls, lock):
        super(ThreadFetchImage, self).__init__(None)
        self.image_urls = image_urls
        self.lock = lock
        self.quit_request = False

    # *************************
    def url_retrieve_report(self, count, buffer_size, total_size):
        if self.quit_request:
            raise ThreadQuitException

    # *************************
    def run(self):
        while len(self.image_urls) > 0:
            with self.lock:
                # check if any note is left
                if len(self.image_urls) <= 0:
                    return
                # retrieve one note
                image_number, image_url = self.image_urls[0]
                del self.image_urls[0]
            if not self.quit_request:
                try:
                    f_name, header = urllib.urlretrieve(image_url, reporthook=self.url_retrieve_report)
                    image = Image.open(f_name).convert("RGB")
                    self.emit(TabImage.signal_image_fetched, (image_number), image)
                    print image_number, 'ok'
                except ThreadQuitException:
                    print 'quitting thread ...'
                except Exception as e:
                    self.emit(TabImage.signal_image_ignored, (image_number))
                    print image_number, 'bad image', e
            else:
                print 'quitting thread ...'
                break

    # *************************
    def quit(self):
        self.quit_request = True


#####################################################################
class ThreadFetchImageUrls(QtCore.QThread):
    # *************************
    def __init__(self, word, language, image_type):
        super(ThreadFetchImageUrls, self).__init__(None)
        query = word
        if image_type == TabImage.ImageType.clipart:
            query += ' clipart'
        elif image_type == TabImage.ImageType.line_drawing:
            query += ' line drawing'
        query = query.split()
        query = '+'.join(query)
        if language == Language.english:
            self.url = "https://www.google.com/search?q=" + query + "&source=lnms&tbm=isch"
        elif language == Language.german:
            self.url = "https://www.google.de/search?q=" + query + "&source=lnms&tbm=isch"
        else:
            print 'unknown language'
        self.quit_request = False

    # *************************
    def run(self):
        print 'fetching image addresses ...'

        header = {
            'User-Agent': "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2357.134 Safari/537.36"
        }

        if not self.quit_request:
            openned_url = urllib2.urlopen(urllib2.Request(self.url, headers=header))

            page = StringIO(openned_url.read())

            # find the directory the pronunciation
            pattern = re.compile('<img.*?>')
            img_tags = pattern.findall(page.getvalue())

            pattern = re.compile('src=".*?"')
            cntr = 1
            image_urls = []
            for img_tag in img_tags:
                urls = pattern.findall(img_tag)
                if len(urls) > 0:
                    url = urls[0].replace('src="', '').replace('"', '')
                    image_urls.append((cntr, url))
                    cntr += 1

            print len(image_urls), 'image urls fetched.'
            if not self.quit_request:
                self.emit(TabImage.signal_urls_fetched, image_urls)
            else:
                print 'quitting url fetching thread ...'
        else:
            print 'quitting url fetching thread ...'

    # *************************
    def quit(self):
        self.quit_request = True


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
class TabWidgetProgress(TabWidget):
    #####################################################################
    def __init__(self, mother, closable=False, parent=None):
        super(TabWidgetProgress, self).__init__(mother, closable, parent)
        self.progress = 0

    #####################################################################
    def update_progress(self):
        mother = self.mother
        if type(mother) is not TabWidgetProgress:
            return
        index = mother.indexOf(self)
        tab_bar = mother.tabBar()
        tabs = self.findChildren(Widget)
        progress = 0
        if self.count() > 0:
            for i in range(self.count()):
                progress += self.widget(i).progress
            progress /= self.count()
        if progress < 100:
            tab_bar.setTabTextColor(index, QtCore.Qt.darkYellow)
            tab_bar.setTabText(index, self.label + ' ' + str(progress) + '%')
        else:
            tab_bar.setTabText(index, self.label)
            tab_bar.setTabTextColor(index, QtCore.Qt.darkGreen)
        self.progress = progress
        mother.update_progress()


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
class TabDictionary(Widget):
    #####################################################################
    def __init__(self, name, web_address, mother, parent=None):
        super(TabDictionary, self).__init__(mother, parent)
        self.name = name
        self.web_address = web_address
        self.word = None
        self.browser = InlineBrowser(self)
        self.browser.loadStarted.connect(lambda: self.update_status(InlineBrowser.SignalType.started))
        self.browser.loadProgress.connect(lambda progress: self.update_status(InlineBrowser.SignalType.progress, progress))
        self.browser.loadFinished.connect(lambda ok: self.update_status(InlineBrowser.SignalType.finished, ok))
        self.vertical_layout = QtGui.QVBoxLayout(self)
        self.vertical_layout.addWidget(self.browser)

    #####################################################################
    def browse(self, word):
        self.word = word
        word = word.split()
        word = '+'.join(word)
        url = self.web_address + word
        self.total_frames = 0
        self.browser.load(QtCore.QUrl(url))

    #####################################################################
    def update_status(self, singal_type, param=None):
        name = self.name
        tab_dictionaries = self.mother
        index = tab_dictionaries.indexOf(self)
        tab_bar = tab_dictionaries.tabBar()
        if singal_type == InlineBrowser.SignalType.started:
            self.progress = 0
            tab_bar.setTabTextColor(index, QtCore.Qt.darkYellow)
            tab_dictionaries.update_progress()
        if singal_type == InlineBrowser.SignalType.progress:
            progress = param
            self.progress = progress
            tab_bar.setTabText(index, name + ' ' + str(progress) + '%')
            tab_dictionaries.update_progress()
        if singal_type == InlineBrowser.SignalType.finished:
            ok = param
            self.progress = 100
            tab_bar.setTabText(index, name)
            if ok:
                tab_bar.setTabTextColor(index, QtCore.Qt.darkGreen)
            else:
                tab_bar.setTabTextColor(index, QtCore.Qt.darkRed)
            tab_dictionaries.update_progress()

    #####################################################################
    def stop(self):
        self.browser.stop()
        print('dictionary {} stopped.'.format(self.name))


#####################################################################
class TabImage(Widget):
    signal_image_fetched = QtCore.SIGNAL('TabImage.image_fetched')
    signal_image_ignored = QtCore.SIGNAL('TabImage.image_ignored')
    signal_urls_fetched = QtCore.SIGNAL('TabImage.image_urls_fetched')
    SignalType = enum(urls_fetched=1, image_fetched=2, image_ignored=3)
    ImageType = enum(normal=1, clipart=2, line_drawing=3)
    NUMBER_OF_IMAGES_IN_EACH_RAW = 5
    NUMBER_OF_IMAGE_FETCHING_THREADS_PER_URL = 1

    #####################################################################
    def __init__(self, word, language, image_type, mother, parent=None):
        super(TabImage, self).__init__(mother, parent)
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
        self.connect(self.thread_fetch_image_urls, TabImage.signal_urls_fetched, self.fetch_images)
        self.connect(self.thread_fetch_image_urls, TabImage.signal_urls_fetched,
                     lambda urls: self.update_status(TabImage.SignalType.urls_fetched, urls))
        self.thread_fetch_image_urls.start()

    ###########################################################
    @property
    def progress(self):
        if self.n_urls == 0:
            return 0
        progress = (self.n_fetched + self.n_ignored) * 100 / self.n_urls
        return progress

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
        if self.quit_request:
            return
        lock = threading.Lock()
        # threads
        for i in range(TabImage.NUMBER_OF_IMAGE_FETCHING_THREADS_PER_URL):
            self.threads_fetch_image.append(ThreadFetchImage(image_urls, lock))
            self.connect(self.threads_fetch_image[-1], TabImage.signal_image_fetched, self.add_fetched_image)
            self.connect(self.threads_fetch_image[-1], TabImage.signal_image_fetched,
                         lambda image_number, image: self.update_status(TabImage.SignalType.image_fetched, image_number))
            self.connect(self.threads_fetch_image[-1], TabImage.signal_image_ignored,
                         lambda image_number: self.update_status(TabImage.SignalType.image_ignored, image_number))
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
            if horizontal_layout.count() >= TabImage.NUMBER_OF_IMAGES_IN_EACH_RAW:
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
        if signal_type == TabImage.SignalType.urls_fetched:
            urls = param
            self.n_urls = len(urls)
            self.n_fetched = 0
            self.n_ignored = 0
            tab_bar.setTabText(index, self.word + ' ' + str(self.progress) + '%')
            tab_bar.setTabTextColor(index, QtCore.Qt.darkYellow)
            tab_images.update_progress()
        if signal_type == TabImage.SignalType.image_fetched:
            self.n_fetched += 1
            if self.progress < 100:
                tab_bar.setTabText(index, self.word + ' ' + str(self.progress) + '%')
                tab_bar.setTabTextColor(index, QtCore.Qt.darkYellow)
            else:
                tab_bar.setTabText(index, self.word)
                tab_bar.setTabTextColor(index, QtCore.Qt.darkGreen)

            tab_images.update_progress()
        if signal_type == TabImage.SignalType.image_ignored:
            self.n_ignored += 1
            tab_bar.setTabText(index, self.word + ' ' + str(self.progress) + '%')
            tab_images.update_progress()
        # if signal_type == InlineBrowser.SignalTypes.finished:
        #     ok = param
        #     self.progress = 100
        #     tab_bar.setTabText(index, name)
        #     if ok:
        #         tab_bar.setTabTextColor(index, QtCore.Qt.darkGreen)
        #     else:
        #         tab_bar.setTabTextColor(index, QtCore.Qt.darkRed)
        #     tab_images.update_progress()

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


#####################################################################
class MainDialog(Dialog):
    # *************************
    def __init__(self, word, language, media_dir, parent=None):
        super(MainDialog, self).__init__(parent)

        self.word = word
        self.media_dir = media_dir
        self.full_image_file_name = None
        self.selected_image = None

        # window
        self.setWindowTitle(word)
        self.resize(1000, 1000)

        self.layout = QtGui.QVBoxLayout()
        self.setLayout(self.layout)
        self.button_next = QtGui.QPushButton()
        self.button_previous = QtGui.QPushButton()
        self.layout.addWidget(self.button_next)
        self.layout.addWidget(self.button_previous)
        self.main_tab_widget = TabWidgetProgress(mother=self)
        self.layout.addWidget(self.main_tab_widget)
        self.status_line = QtGui.QLabel(word)
        self.layout.addWidget(self.status_line)

        # word fields
        self.main_tab_widget.tab_word_fields = Widget(self.main_tab_widget)
        self.main_tab_widget.addTab(self.main_tab_widget.tab_word_fields, 'word')

        # dictionaries
        self.main_tab_widget.tab_dictionaries = TabWidgetProgress(mother=self.main_tab_widget)
        self.main_tab_widget.addTab(self.main_tab_widget.tab_dictionaries, 'dictinoaries')

        # main word dictionaries
        self.add_dictionary_tabs(word, language)

        # images
        self.main_tab_widget.tab_images = TabWidgetProgress(mother=self.main_tab_widget)
        self.main_tab_widget.addTab(self.main_tab_widget.tab_images, 'images')

        # main word images
        self.add_image_tabs(word, language)

    ###########################################################
    def add_dictionary_tabs(self, word, language):
        # english dictionaries
        if language == Language.english:
            tab_english = TabWidgetProgress(mother=self.main_tab_widget.tab_dictionaries, closable=True)
            self.main_tab_widget.tab_dictionaries.addTab(tab_english, word)
            # english dictionaries
            tab_dictionaries = [
                TabDictionary('google translate', 'https://translate.google.com/#en/fa/', mother=tab_english),
                TabDictionary('vocabulary.com', 'https://www.vocabulary.com/dictionary/', mother=tab_english),
                TabDictionary('webster', 'https://www.merriam-webster.com/dictionary/', mother=tab_english),
                TabDictionary('oxford', 'https://en.oxforddictionaries.com/definition/us/', mother=tab_english)]
            for tab_dictionary in tab_dictionaries:
                tab_english.addTab(tab_dictionary, tab_dictionary.name)
                tab_dictionary.browse(word)

        # german dictionaries
        elif language == Language.german:
            tab_german = TabWidgetProgress(mother=self.main_tab_widget.tab_dictionaries, closable=True)
            self.main_tab_widget.tab_dictionaries.addTab(tab_german, word)
            tab_dictionaries = [
                TabDictionary('google translate', 'https://translate.google.com/#de/fa/', mother=tab_german),
                TabDictionary('dict.cc', 'http://www.dict.cc/?s=', mother=tab_german),
                TabDictionary('leo.org', 'http://dict.leo.org/german-english/', mother=tab_german),
                TabDictionary('collins', 'https://www.collinsdictionary.com/dictionary/german-english/', mother=tab_german),
                TabDictionary('duden', 'http://www.duden.de/suchen/dudenonline/', mother=tab_german)]
            for tab_dictionary in tab_dictionaries:
                tab_german.addTab(tab_dictionary, tab_dictionary.name)
                tab_dictionary.browse(word)

    ###########################################################
    def add_image_tabs(self, word, language):
        tab = TabWidgetProgress(mother=self.main_tab_widget.tab_images, closable=True)
        self.main_tab_widget.tab_images.addTab(tab, word)

        tab_normal_images = TabImage(word, language, TabImage.ImageType.normal, mother=tab)
        tab_clip_arts = TabImage(word, language, TabImage.ImageType.clipart, mother=tab)
        tab_line_drawings = TabImage(word, language, TabImage.ImageType.line_drawing, mother=tab)

        tab.addTab(tab_normal_images, 'normal')
        tab.addTab(tab_clip_arts, 'clipart')
        tab.addTab(tab_line_drawings, 'line drawing')

    ###########################################################
    def closeEvent(self, QCloseEvent):
        for tab_image in self.findChildren(TabImage):
            tab_image.quit()
        for tab_dictionary in self.findChildren(TabDictionary):
            tab_dictionary.stop()
        for tab_image in self.findChildren(TabImage):
            tab_image.terminate()


app = QtGui.QApplication(sys.argv)

w = MainDialog('hello', Language.english, '/home/mehdi')

w.show()

app.exec_()

if w.full_image_file_name is not None:
    print w.full_image_file_name





