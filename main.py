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


def enum(**enums):
    return type('Enum', (), enums)
Language = enum(english=1, german=2)

NUMBER_OF_IMAGES_IN_EACH_RAW = 5

processed_queue_lock = threading.Lock()
processed_queue = []
signal_image_fetched = "add_image_to_dialog(QString, PyQt_PyObject, PyQt_PyObject)"
signal_image_urls_fetched = "fetch_images(PyQt_PyObject, PyQt_PyObject)"
threads_fetch_image = []


#####################################################################
class InlineBrowser(QtWebKit.QWebView):
    #####################################################################
    def __init__(self, image_dialog, parent=None):
        super(InlineBrowser, self).__init__(parent)
        self.image_dialog = image_dialog

    #####################################################################
    def contextMenuEvent(self, event):
        menu = QtGui.QMenu(self)

        Action = menu.addAction('fetch: ' + self.selectedText())
        Action.triggered.connect(self.fetch_this_word)

        menu.exec_(self.mapToGlobal(event.pos()))

    #####################################################################
    def fetch_this_word(self):
        text = str(self.selectedText())
        if text:
            self.image_dialog.add_dictionary_tabs(text)
            self.image_dialog.add_image_tabs(text)


# def get_soup(url,header):
#     return BeautifulSoup(urllib2.urlopen(urllib2.Request(url,headers=header)),'html.parser')

#####################################################################
class TabDictionary(QtGui.QWidget):
    #####################################################################
    def __init__(self, name, web_address, image_dialog, parent=None):
        super(TabDictionary, self).__init__(parent)
        self.name = name
        self.web_address =web_address
        self.browser = InlineBrowser(image_dialog)
        self.vertical_layout = QtGui.QVBoxLayout(self)
        self.vertical_layout.addWidget(self.browser)

    #####################################################################
    def browse(self, word):
        word = word.split()
        word = '+'.join(word)
        url = self.web_address + word
        self.browser.load(QtCore.QUrl(url))


#####################################################################
def is_german(word):
    return True


#####################################################################
class ImagesDialog(QtGui.QTabWidget):
    # *************************
    def __init__(self, word, parent=None):
        super(ImagesDialog, self).__init__(parent)

        # window
        self.setWindowTitle("Images")
        self.resize(1000, 1000)

        # dictionaries
        self.tab_dictionaries = QtGui.QTabWidget()
        self.addTab(self.tab_dictionaries, 'dictinoaries')

        # main word dictionaries
        self.add_dictionary_tabs(word)

        # images
        self.tab_images = QtGui.QTabWidget()
        self.addTab(self.tab_images, 'images')

        # main word images
        self.add_image_tabs(word)

    ###########################################################
    def add_dictionary_tabs(self, word):
        tab = QtGui.QTabWidget()
        self.tab_dictionaries.addTab(tab, word)
        # english dictionaries
        tab.tab_dictionaries = [TabDictionary('google translate', 'https://translate.google.com/#en/fa/', self),
                                                      TabDictionary('vocabulary.com', 'https://www.vocabulary.com/dictionary/', self),
                                                      TabDictionary('webster', 'https://www.merriam-webster.com/dictionary/', self),
                                                      TabDictionary('oxford', 'https://en.oxforddictionaries.com/definition/us/', self)]
        for tab_dictionary in tab.tab_dictionaries:
            tab.addTab(tab_dictionary, tab_dictionary.name)
            tab_dictionary.browse(word)

        # german dictionaries
        if is_german(word):
            tab_german = QtGui.QTabWidget()
            self.tab_dictionaries.addTab(tab_german, word + '-german')
            tab_german.tab_dictionaries = [TabDictionary('google translate', 'https://translate.google.com/#de/fa/', self),
                                                          TabDictionary('dict.cc', 'http://www.dict.cc/?s=', self),
                                                          TabDictionary('leo.org', 'http://dict.leo.org/german-english/', self),
                                                          TabDictionary('collins', 'https://www.collinsdictionary.com/dictionary/german-english/', self),
                                                          TabDictionary('duden', 'http://www.duden.de/suchen/dudenonline/', self)]
            for tab_dictionary in tab_german.tab_dictionaries:
                tab_german.addTab(tab_dictionary, tab_dictionary.name)
                tab_dictionary.browse(word)

    ###########################################################
    def add_image_tabs(self, word):
        print 'adding image tabs for: ' + word
        tab = QtGui.QTabWidget()
        self.tab_images.addTab(tab, word)

        tab.tab_normal_images = QtGui.QWidget()
        tab.tab_clip_arts = QtGui.QWidget()
        tab.tab_line_drawings = QtGui.QWidget()

        tab.addTab(tab.tab_normal_images, "normal images")
        tab.addTab(tab.tab_clip_arts, "cliparts")
        tab.addTab(tab.tab_line_drawings, "line drawings")
        
        self.add_layouts(tab.tab_normal_images)
        self.add_layouts(tab.tab_clip_arts)
        self.add_layouts(tab.tab_line_drawings)

        self.thread_fetch_normal_image_urls = ThreadFetchImageUrls(word, Language.english, None, tab.tab_normal_images)
        self.connect(self.thread_fetch_normal_image_urls, QtCore.SIGNAL(signal_image_urls_fetched), self.fetch_images)
        self.thread_fetch_normal_image_urls.start()

        self.thread_fetch_clipart_image_urls = ThreadFetchImageUrls(word, Language.english, 'clipart', tab.tab_clip_arts)
        self.connect(self.thread_fetch_clipart_image_urls, QtCore.SIGNAL(signal_image_urls_fetched), self.fetch_images)
        self.thread_fetch_clipart_image_urls.start()

        self.thread_fetch_linedrawing_image_urls = ThreadFetchImageUrls(word, Language.english, 'line drawing', tab.tab_line_drawings)
        self.connect(self.thread_fetch_linedrawing_image_urls, QtCore.SIGNAL(signal_image_urls_fetched), self.fetch_images)
        self.thread_fetch_linedrawing_image_urls.start()

        if is_german(word):
            tab_german = QtGui.QTabWidget()
            self.tab_images.addTab(tab_german, word + '-german')

            tab_german.tab_normal_images = QtGui.QWidget()
            tab_german.tab_clip_arts = QtGui.QWidget()
            tab_german.tab_line_drawings = QtGui.QWidget()

            tab_german.addTab(tab_german.tab_normal_images, "normal images")
            tab_german.addTab(tab_german.tab_clip_arts, "cliparts")
            tab_german.addTab(tab_german.tab_line_drawings, "line drawings")

            self.add_layouts(tab_german.tab_normal_images)
            self.add_layouts(tab_german.tab_clip_arts)
            self.add_layouts(tab_german.tab_line_drawings)
    
            self.thread_fetch_normal_image_urls = ThreadFetchImageUrls(word, Language.german, None, tab_german.tab_normal_images)
            self.connect(self.thread_fetch_normal_image_urls, QtCore.SIGNAL(signal_image_urls_fetched), self.fetch_images)
            self.thread_fetch_normal_image_urls.start()

            self.thread_fetch_clipart_image_urls = ThreadFetchImageUrls(word, Language.german, 'clipart', tab_german.tab_clip_arts)
            self.connect(self.thread_fetch_clipart_image_urls, QtCore.SIGNAL(signal_image_urls_fetched), self.fetch_images)
            self.thread_fetch_clipart_image_urls.start()

            self.thread_fetch_linedrawing_image_urls = ThreadFetchImageUrls(word, Language.german, 'line drawing', tab_german.tab_line_drawings)
            self.connect(self.thread_fetch_linedrawing_image_urls, QtCore.SIGNAL(signal_image_urls_fetched), self.fetch_images)
            self.thread_fetch_linedrawing_image_urls.start()

    ###########################################################
    def fetch_images(self, image_urls, tab):
        lock = threading.Lock()
        # threads
        for i in range(0, 10):
            threads_fetch_image.append(ThreadFetchImage(image_urls, lock, tab))
            self.connect(threads_fetch_image[-1], QtCore.SIGNAL(signal_image_fetched), self.add_image_to_dialog)
            threads_fetch_image[-1].start()

    ###########################################################
    def add_layouts(self, tab):
        # scroll area
        tab.scroll_area = QtGui.QScrollArea(tab)
        tab.scroll_area.setWidgetResizable(True)
        tab.scroll_area_widget_contents = QtGui.QWidget(tab.scroll_area)
        tab.scroll_area_widget_contents.setGeometry(QtCore.QRect(0, 0, 50, 100))
        tab.scroll_area.setWidget(tab.scroll_area_widget_contents)

        # layouts
        # base vertical layout
        tab.vertical_layout = QtGui.QVBoxLayout(tab)

        tab.vertical_layout.addWidget(tab.scroll_area)
        # scrollable vertical layout
        tab.vertical_layout_scroll = QtGui.QVBoxLayout(tab.scroll_area_widget_contents)
        # horizontal layouts
        tab.horizontal_layouts = []
        # first row of images
        tab.horizontal_layouts.append(QtGui.QHBoxLayout())
        tab.vertical_layout_scroll.addLayout(tab.horizontal_layouts[-1])

    # *************************
    def add_image_to_dialog(self, image_number, image, tab):
        view = GraphicsView(1, image.size[0], image.size[1])
        view.setMinimumHeight(image.size[1] / 2)
        view.display_image(image)
        view.fit()
        image_number = int(image_number)
        while image_number >= len(tab.horizontal_layouts) * NUMBER_OF_IMAGES_IN_EACH_RAW:
            horizontal_layout = QtGui.QHBoxLayout()
            tab.horizontal_layouts.append(horizontal_layout)
            tab.vertical_layout_scroll.addLayout(tab.horizontal_layouts[-1])
        tab.horizontal_layouts[image_number // NUMBER_OF_IMAGES_IN_EACH_RAW].addWidget(view)

    ###########################################################
    def closeEvent(self, QCloseEvent):
        for thread in threads_fetch_image:
            thread.terminate()


#####################################################################
class GraphicsView(QtGui.QGraphicsView):
    #####################################################################
    def __init__(self, number, w, h, parent=None):
        super(GraphicsView, self).__init__(parent)
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
    def display_image(self, image):
        self.scene.clear()
        # w, h = image.size
        self.imgQ = ImageQt.ImageQt(image)  # we need to hold reference to imgQ, or it will crash
        self.pixMap = QtGui.QPixmap.fromImage(self.imgQ)
        self.scene.addPixmap(self.pixMap)
        # self.fitInView(QtCore.QRectF(0, 0, w, h), QtCore.Qt.KeepAspectRatio)
        self.scene.update()

    #####################################################################
    def contextMenuEvent(self, QContextMenuEvent):
        menu = QtGui.QMenu(self)

        Action = menu.addAction("set this image")
        Action.triggered.connect(self.save_image)

        menu.exec_(self.mapToGlobal(QContextMenuEvent.pos()))

    #####################################################################
    def save_image(self):
        print 'saving ...'
        self.pixMap.save('/home/mehdi/Desktop/image.jpg')


#####################################################################
class ThreadFetchImage(QtCore.QThread):
    # *************************
    def __init__(self, image_urls, lock, tab):
        super(ThreadFetchImage, self).__init__(None)
        self.image_urls = image_urls
        self.lock = lock
        self.tab = tab

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
            try:
                image = Image.open(StringIO(urllib.urlopen(image_url).read()))
                self.emit(QtCore.SIGNAL(signal_image_fetched), str(image_number), image, self.tab)
                print image_number, 'ok'
                # break
            except Exception as e:
                print image_number, 'bad image', e


#####################################################################
class ThreadFetchImageUrls(QtCore.QThread):
    # *************************
    def __init__(self, word, language, image_type, tab):
        super(ThreadFetchImageUrls, self).__init__(None)
        query = word + ((' ' + image_type) if image_type is not None else '')
        query = query.split()
        query = '+'.join(query)
        if language == Language.english:
            self.url = "https://www.google.com/search?q=" + query + "&source=lnms&tbm=isch"
        elif language == Language.german:
            self.url = "https://www.google.de/search?q=" + query + "&source=lnms&tbm=isch"
        else:
            print 'unknown language'
        self.tab = tab

    # *************************
    def run(self):
        print 'fetching image addresses ...'

        header = {
            'User-Agent': "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2357.134 Safari/537.36"
        }

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

        print 'image urls fetched.'
        print len(image_urls)
        self.emit(QtCore.SIGNAL(signal_image_urls_fetched), image_urls, self.tab)

app = QtGui.QApplication(sys.argv)

w = ImagesDialog('hello')

w.show()

sys.exit(app.exec_())





