# -*- coding: utf-8 -*-

from PyQt4 import QtGui, QtCore, QtWebKit
import threading
from PIL.ImageQt import ImageQt
from general_tools import enum, Result, ImageType, Language
from thread_tools import ThreadFetchImage, ThreadFetchImages, ThreadFetchImageUrls
from widget_tools import *
from browser_tools import Browser, InlineBrowser


class ImageTab(Widget, Result):

    # ===========================================================================
    def __init__(self, extended_note, language, image_type, mother, parent=None):
        Widget.__init__(self, mother, parent)
        Result.__init__(self)

        self.extended_note = extended_note
        self.language = language
        self.image_type = image_type

        self.browsing_started = False

        if self.language == Language.german:
            self.web_address = 'https://www.google.de/search?tbm=isch&q='
        else:
            self.web_address = 'https://www.google.com/search?tbm=isch&q='

        self.browser = Browser(self.web_address, mother=self)
        self.connect(self.browser, Browser.signal_started,
                     lambda: self.update_status(InlineBrowser.SignalType.started))
        self.connect(self.browser, Browser.signal_progress,
                     lambda progress: self.update_status(InlineBrowser.SignalType.progress, progress))
        self.connect(self.browser, Browser.signal_finished,
                     lambda ok: self.update_status(InlineBrowser.SignalType.finished, ok))
        self.add_widget(self.browser)

    # ===========================================================================
    def create_url(self, word):
        word = word.split()
        if self.image_type == ImageType.clipart:
            word.append('clipart')
        if self.image_type == ImageType.line_drawing:
            word.append('line drawing')
        word = '+'.join(word)
        return self.web_address + word

    # ===========================================================================
    def update_status(self, singal_type, param=None):
        name = 'images' #self.name
        tab_images = self.mother
        index = tab_images.indexOf(self)
        tab_bar = tab_images.tabBar()
        if singal_type == InlineBrowser.SignalType.started:
            self.progress = 0
            tab_bar.setTabTextColor(index, Result.started_color)
            tab_images.update_progress()
        if singal_type == InlineBrowser.SignalType.progress:
            progress = param
            self.in_progress = True
            self.progress = progress
            tab_bar.setTabText(index, name + ' ' + str(progress) + '%')
            tab_bar.setTabTextColor(index, Result.in_progress_color)
            tab_images.update_progress()
        if singal_type == InlineBrowser.SignalType.finished:
            ok = param
            tab_bar.setTabText(index, name)
            if ok:
                self.progress = 100
                self.succeeded = True
                tab_bar.setTabTextColor(index, Result.succeeded_color)
            else:
                self.failed = True
                tab_bar.setTabTextColor(index, Result.failed_color)
            tab_images.update_progress()

    # ===========================================================================
    def quit(self):
        self.browser.quit()

    # ===========================================================================
    def terminate(self):
        self.browser.terminate()

    # ===========================================================================
    def start(self, word=None):
        if not self.browsing_started:
            self.browsing_started = True
            if word == None:
                word = self.extended_note.main_word()
            self.browser.go(self.create_url(word))

    # ===========================================================================
    def stop(self):
        self.browsing_started = False
        self.browser.stop()


# ===========================================================================
class ImageTabOld(Widget, Result):
    SignalType = enum(urls_fetched=1, urls_fetching_started=2, image_fetched=3, image_ignored=4, urls_fetching_stopped=5,
                      image_fetching_stopped=6)
    NUMBER_OF_IMAGES_IN_EACH_RAW = 5
    NUMBER_OF_IMAGE_FETCHING_THREADS_PER_URL = 5

    # ===========================================================================
    def __init__(self, extended_note, language, image_type, mother, parent=None):
        Widget.__init__(self, mother, parent)
        Result.__init__(self)
        self.fetching_started = False
        self.words=[]
        self.extended_note = extended_note
        word = extended_note.main_word()
        self.words.append(word)
        self.current_word_index = 0
        self.n_urls = 0
        self.n_fetched = 0
        self.n_ignored = 0
        self.language = language
        self.image_type = image_type
        self.selected_image = None

        size = QtCore.QSize(35, 30)
        style = "font-size:18px;"

        self.button_previous = Button(u"◀", self.previous_word, size, style, enabled=False)
        self.button_next = Button(u"▶", self.next_word, size, style, enabled=False)
        self.button_stop = Button(u'✘', self.stop, size, style, enabled=False)
        self.button_reload = Button(u"↻", self.restart, size, style)
        self.word_line = QtGui.QLineEdit(self.words[0])
        self.button_go = Button(u'✔', self.go, size, style)

        self.add_row_widgets(self.button_previous, self.button_next, self.button_stop, self.button_reload,
                             self.word_line, self.button_go)

        self.vertical_layout_scroll = self.add_scroll_area()
        # horizontal layouts
        self.horizontal_layouts = []
        # first row of images
        self.horizontal_layouts.append(QtGui.QHBoxLayout())
        self.vertical_layout_scroll.addLayout(self.horizontal_layouts[-1])

        self.threads_fetch_image = []
        self.thread_fetch_image_urls = ThreadFetchImageUrls(self.words[0], self.language, self.image_type)
        self.connect(self.thread_fetch_image_urls, ThreadFetchImageUrls.signal_urls_fetched, self.fetch_images)
        self.connect(self.thread_fetch_image_urls, ThreadFetchImageUrls.signal_urls_fetched,
                     lambda urls: self.update_status(ImageTab.SignalType.urls_fetched, urls))
        self.connect(self.thread_fetch_image_urls, ThreadFetchImageUrls.signal_urls_fetching_started,
                     lambda : self.update_status(ImageTab.SignalType.urls_fetching_started))

    # ===========================================================================
    def update_word(self):
        word = self.extended_note.main_word()
        if not self.words or word != self.words[0]:
            self.words=[word]
            self.word_line.setText(self.words[self.current_word_index])
            self.thread_fetch_image_urls.update_word(word)

    # ===========================================================================
    def update_url_thread_word(self, word):
        self.thread_fetch_image_urls.word = word

    # ===========================================================================
    def next_word(self):
        if self.current_word_index + 1 < len(self.words):
            self.current_word_index += 1
            self.button_previous.setEnabled(True)
            self.restart()
        if self.current_word_index + 1 == len(self.words):
            self.button_next.setEnabled(False)

    # ===========================================================================
    def previous_word(self):
        if self.current_word_index > 0:
            self.current_word_index -= 1
            self.button_next.setEnabled(True)
            self.restart()
        if self.current_word_index == 0:
            self.button_previous.setEnabled(False)

    # ===========================================================================
    def remove_images(self):
        for horizontal_layout in self.horizontal_layouts:
            for i in range(horizontal_layout.count()):
                horizontal_layout.itemAt(i).widget().close()

    # ===========================================================================
    def fetch_images(self, image_urls):
        if len(image_urls) == 0:
            return
        lock = threading.Lock()
        # threads
        for i in range(ImageTab.NUMBER_OF_IMAGE_FETCHING_THREADS_PER_URL):
            self.threads_fetch_image.append(ThreadFetchImages(image_urls, lock))
            self.connect(self.threads_fetch_image[-1], ThreadFetchImages.signal_image_fetched, self.add_fetched_image)
            self.connect(self.threads_fetch_image[-1], ThreadFetchImages.signal_image_fetched,
                         lambda image_number, image: self.update_status(ImageTab.SignalType.image_fetched, image_number))
            self.connect(self.threads_fetch_image[-1], ThreadFetchImages.signal_image_ignored,
                         lambda image_number: self.update_status(ImageTab.SignalType.image_ignored, image_number))
            self.threads_fetch_image[-1].start()

    # ===========================================================================
    def add_fetched_image(self, image_number, image):
        view = ImageGraphicsView(1, image.size[0], image.size[1], self)
        self.connect(view, ImageGraphicsView.set_image_signal, self.set_image)
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

    # ===========================================================================
    def set_image(self, image):
        self.emit(ImageGraphicsView.set_image_signal, image)

    # ===========================================================================
    def update_status(self, signal_type, param=None):
        tab_images = self.mother
        index = tab_images.indexOf(self)
        tab_bar = tab_images.tabBar()

        if signal_type == ImageTab.SignalType.urls_fetching_stopped or \
                signal_type == ImageTab.SignalType.image_fetching_stopped:
            self.failed = True
            tab_bar.setTabText(index, ImageType.names[self.image_type])
            tab_bar.setTabTextColor(index, Result.failed_color)

        if signal_type == ImageTab.SignalType.urls_fetching_started:
            self.started = True
            self.n_urls = 0
            self.n_fetched = 0
            self.n_ignored = 0
            self.progress = 0
            tab_bar.setTabText(index, ImageType.names[self.image_type])
            tab_bar.setTabTextColor(index, Result.started_color)

        if signal_type == ImageTab.SignalType.urls_fetched:
            urls = param
            self.n_urls = len(urls)
            if self.n_urls == 0:
                self.failed = True
                tab_bar.setTabText(index, ImageType.names[self.image_type])
                tab_bar.setTabTextColor(index, Result.failed_color)
            else:
                self.in_progress = True
                tab_bar.setTabText(index, ImageType.names[self.image_type] + ' ' + str(self.progress) + '%')
                tab_bar.setTabTextColor(index, Result.in_progress_color)

        if signal_type == ImageTab.SignalType.image_fetched:
            self.n_fetched += 1
            self.progress = (self.n_fetched + self.n_ignored) * 100 / self.n_urls
            if self.progress < 100:
                tab_bar.setTabText(index, ImageType.names[self.image_type] + ' ' + str(self.progress) + '%')
                tab_bar.setTabTextColor(index, Result.in_progress_color)
            else:
                tab_bar.setTabText(index, ImageType.names[self.image_type])
                tab_bar.setTabTextColor(index, Result.succeeded_color)

        if signal_type == ImageTab.SignalType.image_ignored:
            self.n_ignored += 1
            if self.n_urls > 0:
                self.progress = (self.n_fetched + self.n_ignored) * 100 / self.n_urls
            else:
                self.progress = 0
            if self.progress < 100:
                tab_bar.setTabText(index, ImageType.names[self.image_type] + ' ' + str(self.progress) + '%')
                tab_bar.setTabTextColor(index, Result.in_progress_color)
            else:
                tab_bar.setTabText(index, ImageType.names[self.image_type])
                tab_bar.setTabTextColor(index, Result.succeeded_color)

        tab_images.update_progress()

    # ===========================================================================
    def quit(self):
        if self.thread_fetch_image_urls.isRunning():
            self.thread_fetch_image_urls.quit()
            self.update_status(ImageTab.SignalType.urls_fetching_stopped)
        is_running = False
        for thread in self.threads_fetch_image:
            if thread.isRunning():
                thread.quit()
                is_running = True
        if is_running:
            self.update_status(ImageTab.SignalType.image_fetching_stopped)

    # ===========================================================================
    def terminate(self):
        if self.thread_fetch_image_urls.isRunning():
            self.thread_fetch_image_urls.terminate()
            self.update_status(ImageTab.SignalType.urls_fetching_stopped)
        is_running = False
        for thread in self.threads_fetch_image:
            if thread.isRunning():
                thread.terminate()
                is_running = True
        if is_running:
            self.update_status(ImageTab.SignalType.image_fetching_stopped)
        self.threads_fetch_image = []

    # ===========================================================================
    def go(self):
        if self.fetching_started:
            self.stop()
            self.remove_images()
        word = unicode(self.word_line.text())
        if word != self.words[self.current_word_index]:
            for i in range(len(self.words) - 1, self.current_word_index, -1):
                del self.words[i]
            self.words.append(word)
            self.current_word_index += 1
            self.button_previous.setEnabled(True)
        self.update_url_thread_word(self.words[self.current_word_index])
        self.start()

    # ===========================================================================
    def start(self):
        if not self.fetching_started:
            self.update_word()
            self.remove_images()
            self.fetching_started = True
            self.thread_fetch_image_urls.start()
            self.button_stop.setEnabled(True)
            self.button_reload.setEnabled(True)

    # ===========================================================================
    def restart(self):
        self.stop()
        self.word_line.setText(self.words[self.current_word_index])
        self.update_url_thread_word(self.words[self.current_word_index])
        self.start()

    # ===========================================================================
    def stop(self):
        if self.fetching_started:
            self.quit()
            self.terminate()
            self.fetching_started = False
            self.button_stop.setEnabled(False)


