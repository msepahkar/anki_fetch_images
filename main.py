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
ImageType = enum(normal=1, clipart=2, line_drawing=3)

NUMBER_OF_IMAGES_IN_EACH_RAW = 5
NUMBER_OF_IMAGE_FETCHING_THREADS_PER_URL = 1

processed_queue_lock = threading.Lock()
processed_queue = []
signal_image_fetched = QtCore.SIGNAL('global.image_fetched')
signal_image_urls_fetched = QtCore.SIGNAL('global.image_urls_fetched')


#####################################################################
class Widget(QtGui.QWidget):
    #####################################################################
    def __init__(self, mother, parent=None):
        super(Widget, self).__init__(parent)
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
    def update_progress(self):
        mother = self.mother
        if type(mother) is not TabWidget:
            return
        index = mother.indexOf(self)
        tab_bar = mother.tabBar()
        tab_dictionaries = self.findChildren(TabDictionary)
        progress = 0
        for tab_dictionary in tab_dictionaries:
            progress += tab_dictionary.progress
        if len(tab_dictionaries) > 0:
            progress /= len(tab_dictionaries)
        if progress < 100:
            tab_bar.setTabTextColor(index, QtCore.Qt.darkYellow)
            tab_bar.setTabText(index, self.label + ' ' + str(progress) + '%')
        else:
            tab_bar.setTabText(index, self.label)
            tab_bar.setTabTextColor(index, QtCore.Qt.darkGreen)
        mother.update_progress()


#####################################################################
class InlineBrowser(QtWebKit.QWebView):
    SignalTypes = enum(started=1, progress=2, finished=3)

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
class TabDictionary(Widget):
    #####################################################################
    def __init__(self, name, web_address, mother, parent=None):
        super(TabDictionary, self).__init__(mother, parent)
        self.name = name
        self.web_address = web_address
        self.word = None
        self.browser = InlineBrowser(self)
        self.browser.loadStarted.connect(lambda: self.update_status(InlineBrowser.SignalTypes.started))
        self.browser.loadProgress.connect(lambda progress: self.update_status(InlineBrowser.SignalTypes.progress, progress))
        self.browser.loadFinished.connect(lambda ok: self.update_status(InlineBrowser.SignalTypes.finished, ok))
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
    def update_status(self, signal, param=None):
        name = self.name
        tab_dictionaries = self.mother
        index = tab_dictionaries.indexOf(self)
        tab_bar = tab_dictionaries.tabBar()
        if signal == InlineBrowser.SignalTypes.started:
            self.progress = 0
            tab_bar.setTabTextColor(index, QtCore.Qt.darkYellow)
            tab_dictionaries.update_progress()
        if signal == InlineBrowser.SignalTypes.progress:
            progress = param
            self.progress = progress
            tab_bar.setTabText(index, name + ' ' + str(progress) + '%')
            tab_dictionaries.update_progress()
        if signal == InlineBrowser.SignalTypes.finished:
            ok = param
            self.progress = 100
            tab_bar.setTabText(index, name)
            if ok:
                tab_bar.setTabTextColor(index, QtCore.Qt.darkGreen)
            else:
                tab_bar.setTabTextColor(index, QtCore.Qt.darkRed)
            tab_dictionaries.update_progress()


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
                    self.emit(signal_image_fetched, (image_number), image, self.tab)
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
        query = word
        if image_type == ImageType.clipart:
            query += ' clipart'
        elif image_type == ImageType.line_drawing:
            query += ' line drawing'
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
                self.emit(signal_image_urls_fetched, image_urls, self.tab)
            else:
                print 'quitting url fetching thread ...'
        else:
            print 'quitting url fetching thread ...'

    # *************************
    def quit(self):
        self.quit_request = True


#####################################################################
class ImagesDialog(Widget):
    # *************************
    def __init__(self, word, language, media_dir, parent=None):
        super(ImagesDialog, self).__init__(None, parent)

        self.quit_request = False
        self.word = word
        self.media_dir = media_dir
        self.full_image_file_name = None
        self.selected_image = None
        self.threads_fetch_image_urls = dict()
        self.threads_fetch_image_urls[ImageType.normal] = []
        self.threads_fetch_image_urls[ImageType.clipart] = []
        self.threads_fetch_image_urls[ImageType.line_drawing] = []
        self.threads_fetch_image = []

        # window
        self.setWindowTitle("Images")
        self.resize(1000, 1000)

        self.layout = QtGui.QVBoxLayout()
        self.setLayout(self.layout)
        self.main_tab_widget = TabWidget(mother=self)
        self.layout.addWidget(self.main_tab_widget)
        self.status_line = QtGui.QLabel(word)
        self.layout.addWidget(self.status_line)

        # dictionaries
        self.main_tab_widget.tab_dictionaries = TabWidget(mother=self.main_tab_widget)
        self.main_tab_widget.addTab(self.main_tab_widget.tab_dictionaries, 'dictinoaries')

        # main word dictionaries
        self.add_dictionary_tabs(word, language)

        # images
        self.main_tab_widget.tab_images = TabWidget(mother=self.main_tab_widget)
        self.main_tab_widget.addTab(self.main_tab_widget.tab_images, 'images')

        # main word images
        self.add_image_tabs(word, language)

    ###########################################################
    def add_dictionary_tabs(self, word, language):
        # english dictionaries
        if language == Language.english:
            tab_english = TabWidget(mother=self.main_tab_widget.tab_dictionaries, closable=True)
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
            tab_german = TabWidget(mother=self.main_tab_widget.tab_dictionaries, closable=True)
            self.main_tab_widget.tab_dictionaries.addTab(tab_german, word + '-german')
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
        # english images
        if language == Language.english:
            tab_english = TabWidget(mother=self.main_tab_widget.tab_images, closable=True)
            self.main_tab_widget.tab_images.addTab(tab_english, word)

            tab_english.tab_normal_images = Widget(mother=tab_english)
            tab_english.tab_clip_arts = Widget(mother=tab_english)
            tab_english.tab_line_drawings = Widget(mother=tab_english)

            tab_english.addTab(tab_english.tab_normal_images, 'normal')
            tab_english.addTab(tab_english.tab_clip_arts, 'clipart')
            tab_english.addTab(tab_english.tab_line_drawings, 'line drawing')

            self.add_layouts_and_threads(tab_english.tab_normal_images, word, Language.english, ImageType.normal)
            self.add_layouts_and_threads(tab_english.tab_clip_arts, word, Language.english, ImageType.clipart)
            self.add_layouts_and_threads(tab_english.tab_line_drawings, word, Language.english, ImageType.line_drawing)

        # german images
        elif language == Language.german:
            tab_german = TabWidget(mother=self.main_tab_widget.tab_images, closable=True)
            self.main_tab_widget.tab_images.addTab(tab_german, word + '-german')

            tab_german.tab_normal_images = Widget(mother=tab_german)
            tab_german.tab_clip_arts = Widget(mother=tab_german)
            tab_german.tab_line_drawings = Widget(mother=tab_german)

            tab_german.addTab(tab_german.tab_normal_images, "normal")
            tab_german.addTab(tab_german.tab_clip_arts, "cliparts")
            tab_german.addTab(tab_german.tab_line_drawings, "line drawings")

            self.add_layouts_and_threads(tab_german.tab_normal_images, word, Language.german, ImageType.normal)
            self.add_layouts_and_threads(tab_german.tab_clip_arts, word, Language.german, ImageType.clipart)
            self.add_layouts_and_threads(tab_german.tab_line_drawings, word, Language.german, ImageType.line_drawing)

    ###########################################################
    def fetch_images(self, image_urls, tab):
        if self.quit_request:
            return
        lock = threading.Lock()
        # threads
        print 'creatoing ', NUMBER_OF_IMAGE_FETCHING_THREADS_PER_URL, ' threads'
        for i in range(NUMBER_OF_IMAGE_FETCHING_THREADS_PER_URL):
            self.threads_fetch_image.append(ThreadFetchImage(image_urls, lock, tab))
            self.connect(self.threads_fetch_image[-1], signal_image_fetched, self.add_fetched_image)
            self.threads_fetch_image[-1].start()

    ###########################################################
    def add_layouts_and_threads(self, tab, word, language, image_type):
        # scroll area
        tab.scroll_area = QtGui.QScrollArea(tab)
        tab.scroll_area.setWidgetResizable(True)
        tab.scroll_area_widget_contents = Widget(mother=tab, parent=tab.scroll_area)
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

        self.threads_fetch_image_urls[image_type].append(ThreadFetchImageUrls(word, language, image_type, tab))
        self.connect(self.threads_fetch_image_urls[image_type][-1], signal_image_urls_fetched, self.fetch_images)
        self.threads_fetch_image_urls[image_type][-1].start()

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
        for category in self.threads_fetch_image_urls:
            for thread in self.threads_fetch_image_urls[category]:
                thread.quit()
        for thread in self.threads_fetch_image:
            thread.quit()

    ###########################################################
    def terminate_threads(self):
        for category in self.threads_fetch_image_urls:
            for thread in self.threads_fetch_image_urls[category]:
                thread.terminate()
        for thread in self.threads_fetch_image:
            thread.terminate()

    ###########################################################
    def update_status(self, caller, *params):
        pass
        # # dictionaries
        # if type(caller) is InlineBrowser:
        #     tab_dictionary = caller.mother
        #     name = tab_dictionary.name
        #     tab_dictionaries = tab_dictionary.mother
        #     index = tab_dictionaries.indexOf(tab_dictionary)
        #     tab_bar = tab_dictionaries.tabBar()
        #     signal = params[0]
        #     if signal == InlineBrowser.Signals.started:
        #         tab_bar.setTabTextColor(index, QtCore.Qt.darkYellow)
        #     if signal == InlineBrowser.Signals.progress:
        #         progress = params[1]
        #         tab_bar.setTabText(index, name + ' ' + str(progress) + '%')
        #     if signal == InlineBrowser.Signals.finished:
        #         ok = params[1]
        #         tab_bar.setTabText(index, name)
        #         if ok:
        #             tab_bar.setTabTextColor(index, QtCore.Qt.darkGreen)
        #         else:
        #             tab_bar.setTabTextColor(index, QtCore.Qt.darkRed)

    ###########################################################
    def stop_dictionaries(self):
        for i in range(self.main_tab_widget.tab_dictionaries.count()):
            for j in range(self.main_tab_widget.tab_dictionaries.widget(i).count()):
                print 'stopping dictionary ...'
                self.main_tab_widget.tab_dictionaries.widget(i).widget(j).browser.stop()

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





