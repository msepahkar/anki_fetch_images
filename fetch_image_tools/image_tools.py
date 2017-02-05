# -*- coding: utf-8 -*-

from PyQt4 import QtGui, QtCore
import ImageQt
import threading
from PIL.ImageQt import ImageQt
from general_tools import enum, OperationResult, ImageType
from thread_tools import ThreadFetchImage, ThreadFetchImageUrls
from widget_tools import Widget


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

    ###########################################################
    def terminate(self):
        self.quit_request = True
        self.thread_fetch_image_urls.terminate()
        for thread in self.threads_fetch_image:
            thread.terminate()

    ###########################################################
    def start_fetching(self):
        self.thread_fetch_image_urls.start()
        self.started = True


