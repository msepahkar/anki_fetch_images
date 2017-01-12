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


def enum(**enums):
    return type('Enum', (), enums)
Language = enum(english=1, german=2)
InfoType = enum(dictionary=1, image=2, dictionary_image=3)

NUMBER_OF_IMAGES_IN_EACH_RAW = 5
NUMBER_OF_IMAGE_FETCHING_THREADS_PER_URL = 14

processed_queue_lock = threading.Lock()
processed_queue = []
signal_image_fetched = "add_image_to_dialog(int, PyQt_PyObject, PyQt_PyObject)"
signal_image_urls_fetched = "fetch_images(PyQt_PyObject, PyQt_PyObject, PyQt_PyObject)"


#####################################################################
class InlineBrowser(QtWebKit.QWebView):
    #####################################################################
    def __init__(self, image_dialog, parent=None):
        super(InlineBrowser, self).__init__(parent)
        self.image_dialog = image_dialog

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
        menu_item.triggered.connect(lambda: self.fetch_this_word(word, Language.english, InfoType.dictionary))

        menu_item = sub_menu_definition.addAction('german')
        menu_item.triggered.connect(lambda: self.fetch_this_word(word, Language.german, InfoType.dictionary))

        menu_item = sub_menu_image.addAction('english')
        menu_item.triggered.connect(lambda: self.fetch_this_word(word, Language.english, InfoType.image))

        menu_item = sub_menu_image.addAction('german')
        menu_item.triggered.connect(lambda: self.fetch_this_word(word, Language.german, InfoType.image))

        menu_item = sub_menu_definition_image.addAction('english')
        menu_item.triggered.connect(lambda: self.fetch_this_word(word, Language.english, InfoType.dictionary_image))

        menu_item = sub_menu_definition_image.addAction('german')
        menu_item.triggered.connect(lambda: self.fetch_this_word(word, Language.german, InfoType.dictionary_image))

        menu.exec_(self.mapToGlobal(event.pos()))

    #####################################################################
    def fetch_this_word(self, word, language, info_type):
        if word:
            if info_type == InfoType.dictionary or info_type == InfoType.dictionary_image:
                self.image_dialog.add_dictionary_tabs(word, language)
            if info_type == InfoType.image or info_type == InfoType.dictionary_image:
                self.image_dialog.add_image_tabs(word, language)


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
        full_base_name = os.path.join(self.main_dialog.media_dir, self.main_dialog.word)
        full_f_name = full_base_name + ".png"
        if os.path.exists(full_f_name):
            i = 0
            while os.path.exists(full_f_name):
                i += 1
                full_f_name = full_base_name + '_' + str(i) + '.png'
        self.main_dialog.full_image_file_name = full_f_name
        self.main_dialog.selected_image = self.image
        self.image.save(full_f_name)


#####################################################################
class ThreadQuitException(Exception):
    pass


#####################################################################
class ThreadFetchImage(QtCore.QThread):
    # *************************
    def __init__(self, image_urls, lock, tab):
        super(ThreadFetchImage, self).__init__(None)
        self.image_urls = image_urls
        self.lock = lock
        self.tab = tab
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
                    self.emit(QtCore.SIGNAL(signal_image_fetched), (image_number), image, self.tab)
                    print image_number, 'ok'
                except ThreadQuitException:
                    print 'quitting thread ...'
                except Exception as e:
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
    def __init__(self, word, language, image_type, tab):
        super(ThreadFetchImageUrls, self).__init__(None)
        if image_type is None:
            self.image_priority = QtCore.QThread.HighPriority
        elif image_type == "clipart":
            self.image_priority = QtCore.QThread.NormalPriority
        else:
            self.image_priority = QtCore.QThread.LowPriority
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
                self.emit(QtCore.SIGNAL(signal_image_urls_fetched), image_urls, self.image_priority, self.tab)
            else:
                print 'quitting url fetching thread ...'
        else:
            print 'quitting url fetching thread ...'

    # *************************
    def quit(self):
        self.quit_request = True


#####################################################################
class ImagesDialog(QtGui.QWidget):
    # *************************
    def __init__(self, word, language, media_dir, parent=None):
        super(ImagesDialog, self).__init__(parent)

        self.quit_request = False
        self.word = word
        self.media_dir = media_dir
        self.full_image_file_name = None
        self.selected_image = None
        self.threads_fetch_normal_image_urls = []
        self.threads_fetch_clipart_image_urls = []
        self.threads_fetch_linedrawing_image_urls = []
        self.threads_fetch_image = []

        # window
        self.setWindowTitle("Images")
        self.resize(1000, 1000)

        self.layout = QtGui.QVBoxLayout()
        self.setLayout(self.layout)
        self.tab_widget = QtGui.QTabWidget()
        self.layout.addWidget(self.tab_widget)
        self.status_line = QtGui.QLabel(word)
        self.layout.addWidget(self.status_line)

        # dictionaries
        self.tab_widget.tab_dictionaries = QtGui.QTabWidget()
        self.tab_widget.addTab(self.tab_widget.tab_dictionaries, 'dictinoaries')

        # main word dictionaries
        self.add_dictionary_tabs(word, language)

        # images
        self.tab_widget.tab_images = QtGui.QTabWidget()
        self.tab_widget.addTab(self.tab_widget.tab_images, 'images')

        # main word images
        self.add_image_tabs(word, language)

    ###########################################################
    def add_dictionary_tabs(self, word, language):
        # english dictionaries
        if language == Language.english:
            tab_english = QtGui.QTabWidget()
            self.tab_widget.tab_dictionaries.addTab(tab_english, word)
            # english dictionaries
            tab_english.tab_dictionaries = [
                TabDictionary('google translate', 'https://translate.google.com/#en/fa/', self),
                TabDictionary('vocabulary.com', 'https://www.vocabulary.com/dictionary/', self),
                TabDictionary('webster', 'https://www.merriam-webster.com/dictionary/', self),
                TabDictionary('oxford', 'https://en.oxforddictionaries.com/definition/us/', self)]
            for tab_dictionary in tab_english.tab_dictionaries:
                tab_english.addTab(tab_dictionary, tab_dictionary.name)
                tab_dictionary.browse(word)

        # german dictionaries
        elif language == Language.german:
            tab_german = QtGui.QTabWidget()
            self.tab_widget.tab_dictionaries.addTab(tab_german, word + '-german')
            tab_german.tab_dictionaries = [
                TabDictionary('google translate', 'https://translate.google.com/#de/fa/', self),
                TabDictionary('dict.cc', 'http://www.dict.cc/?s=', self),
                TabDictionary('leo.org', 'http://dict.leo.org/german-english/', self),
                TabDictionary('collins', 'https://www.collinsdictionary.com/dictionary/german-english/', self),
                TabDictionary('duden', 'http://www.duden.de/suchen/dudenonline/', self)]
            for tab_dictionary in tab_german.tab_dictionaries:
                tab_german.addTab(tab_dictionary, tab_dictionary.name)
                tab_dictionary.browse(word)

    ###########################################################
    def add_image_tabs(self, word, language):
        # english images
        if language == Language.english:
            tab_english = QtGui.QTabWidget()
            self.tab_widget.tab_images.addTab(tab_english, word)

            tab_english.tab_normal_images = QtGui.QWidget()
            tab_english.tab_clip_arts = QtGui.QWidget()
            tab_english.tab_line_drawings = QtGui.QWidget()

            tab_english.addTab(tab_english.tab_normal_images, "normal images")
            tab_english.addTab(tab_english.tab_clip_arts, "cliparts")
            tab_english.addTab(tab_english.tab_line_drawings, "line drawings")

            self.add_layouts(tab_english.tab_normal_images)
            self.add_layouts(tab_english.tab_clip_arts)
            self.add_layouts(tab_english.tab_line_drawings)

            self.threads_fetch_normal_image_urls.append(ThreadFetchImageUrls(word, Language.english, None,
                                                                        tab_english.tab_normal_images))
            self.connect(self.threads_fetch_normal_image_urls[-1], QtCore.SIGNAL(signal_image_urls_fetched),
                         self.fetch_images)
            self.threads_fetch_normal_image_urls[-1].start(QtCore.QThread.HighestPriority)

            self.threads_fetch_clipart_image_urls.append(ThreadFetchImageUrls(word, Language.english, 'clipart',
                                                                         tab_english.tab_clip_arts))
            self.connect(self.threads_fetch_clipart_image_urls[-1], QtCore.SIGNAL(signal_image_urls_fetched),
                         self.fetch_images)
            self.threads_fetch_clipart_image_urls[-1].start(QtCore.QThread.HighPriority)

            self.threads_fetch_linedrawing_image_urls.append(ThreadFetchImageUrls(word, Language.english, 'line drawing',
                                                                             tab_english.tab_line_drawings))
            self.connect(self.threads_fetch_linedrawing_image_urls[-1], QtCore.SIGNAL(signal_image_urls_fetched),
                         self.fetch_images)
            self.threads_fetch_linedrawing_image_urls[-1].start(QtCore.QThread.NormalPriority)
        # german images
        elif language == Language.german:
            tab_german = QtGui.QTabWidget()
            self.tab_widget.tab_images.addTab(tab_german, word + '-german')

            tab_german.tab_normal_images = QtGui.QWidget()
            tab_german.tab_clip_arts = QtGui.QWidget()
            tab_german.tab_line_drawings = QtGui.QWidget()

            tab_german.addTab(tab_german.tab_normal_images, "normal images")
            tab_german.addTab(tab_german.tab_clip_arts, "cliparts")
            tab_german.addTab(tab_german.tab_line_drawings, "line drawings")

            self.add_layouts(tab_german.tab_normal_images)
            self.add_layouts(tab_german.tab_clip_arts)
            self.add_layouts(tab_german.tab_line_drawings)

            self.threads_fetch_normal_image_urls.append(ThreadFetchImageUrls(word, Language.german, None,
                                                                        tab_german.tab_normal_images))
            self.connect(self.threads_fetch_normal_image_urls[-1], QtCore.SIGNAL(signal_image_urls_fetched),
                         self.fetch_images)
            self.threads_fetch_normal_image_urls[-1].start(QtCore.QThread.HighestPriority)

            self.threads_fetch_clipart_image_urls.append(ThreadFetchImageUrls(word, Language.german, 'clipart',
                                                                         tab_german.tab_clip_arts))
            self.connect(self.threads_fetch_clipart_image_urls[1], QtCore.SIGNAL(signal_image_urls_fetched),
                         self.fetch_images)
            self.threads_fetch_clipart_image_urls[-1].start(QtCore.QThread.HighPriority)

            self.threads_fetch_linedrawing_image_urls.append(ThreadFetchImageUrls(word, Language.german, 'line drawing',
                                                                                  tab_german.tab_line_drawings))
            self.connect(self.threads_fetch_linedrawing_image_urls[-1], QtCore.SIGNAL(signal_image_urls_fetched),
                         self.fetch_images)
            self.threads_fetch_linedrawing_image_urls[-1].start(QtCore.QThread.NormalPriority)

    ###########################################################
    def fetch_images(self, image_urls, priority, tab):
        if self.quit_request:
            return
        lock = threading.Lock()
        # threads
        print 'creatoing ', NUMBER_OF_IMAGE_FETCHING_THREADS_PER_URL, ' threads'
        for i in range(NUMBER_OF_IMAGE_FETCHING_THREADS_PER_URL):
            self.threads_fetch_image.append(ThreadFetchImage(image_urls, lock, tab))
            self.connect(self.threads_fetch_image[-1], QtCore.SIGNAL(signal_image_fetched), self.add_fetched_image)
            self.threads_fetch_image[-1].start(priority)

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

    ###########################################################
    def add_fetched_image(self, image_number, image, tab):
        if self.quit_request:
            return
        view = GraphicsView(1, image.size[0], image.size[1], self)
        view.image = image
        view.setMinimumHeight(image.size[1] / 2)
        view.display_image(image_number, image)
        view.image_number = image_number
        view.fit()
        image_number = int(image_number)
        done = False
        for horizontal_layout in tab.horizontal_layouts:
            if horizontal_layout.count() >= NUMBER_OF_IMAGES_IN_EACH_RAW:
                continue
            horizontal_layout.addWidget(view)
            done = True
        if not done:
            horizontal_layout = QtGui.QHBoxLayout()
            tab.horizontal_layouts.append(horizontal_layout)
            tab.vertical_layout_scroll.addLayout(tab.horizontal_layouts[-1])
            horizontal_layout.addWidget(view)

    ###########################################################
    def quit_threads(self):
        for thread in self.threads_fetch_normal_image_urls:
            if thread.isRunning():
                thread.quit()
        for thread in self.threads_fetch_clipart_image_urls:
            if thread.isRunning():
                thread.quit()
        for thread in self.threads_fetch_linedrawing_image_urls:
            if thread.isRunning():
                thread.quit()
        for thread in self.threads_fetch_image:
            if thread.isRunning():
                thread.quit()

    ###########################################################
    def terminate_threads(self):
        for thread in self.threads_fetch_normal_image_urls:
            if thread.isRunning():
                thread.terminate()
        for thread in self.threads_fetch_clipart_image_urls:
            if thread.isRunning():
                thread.terminate()
        for thread in self.threads_fetch_linedrawing_image_urls:
            if thread.isRunning():
                thread.terminate()
        for thread in self.threads_fetch_image:
            if thread.isRunning():
                thread.terminate()

    ###########################################################
    def update_status(self, ):

    ###########################################################
    def stop_dictionaries(self):
        for i in range(self.tab_widget.tab_dictionaries.count()):
            for j in range(self.tab_widget.tab_dictionaries.widget(i).count()):
                print 'stopping dictionary ...'
                self.tab_widget.tab_dictionaries.widget(i).widget(j).browser.stop()

    ###########################################################
    def wait_for_threads(self):
        for thread in self.threads_fetch_normal_image_urls:
            thread.wait()
        for thread in self.threads_fetch_clipart_image_urls:
            thread.wait()
        for thread in self.threads_fetch_linedrawing_image_urls:
            thread.wait()
        for thread in self.threads_fetch_image:
            thread.wait()

    ###########################################################
    def closeEvent(self, QCloseEvent):
        self.quit_request = True
        self.stop_dictionaries()
        self.quit_threads()
        self.terminate_threads()




app = QtGui.QApplication(sys.argv)

w = ImagesDialog('hello', Language.english, '/home/mehdi')

w.show()

app.exec_()

if w.full_image_file_name is not None:
    print w.full_image_file_name





