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

def enum(**enums):
    return type('Enum', (), enums)
Language = enum(english=1, german=2)

NUMBER_OF_IMAGES_IN_EACH_RAW = 5

processed_queue_lock = threading.Lock()
processed_queue = []
signal_image_fetched = "add_image_to_dialog(QString, PyQt_PyObject, PyQt_PyObject)"
signal_image_urls_fetched = "fetch_images(PyQt_PyObject, PyQt_PyObject)"
threads_fetch_image = []


# def get_soup(url,header):
#     return BeautifulSoup(urllib2.urlopen(urllib2.Request(url,headers=header)),'html.parser')


#####################################################################
class ImagesDialog(QtGui.QTabWidget):
    # *************************
    def __init__(self, parent=None):
        super(ImagesDialog, self).__init__(parent)

        # window
        self.setWindowTitle("Images")
        self.resize(1000, 1000)
        
        # tabs
        self.tab_normal_images = QtGui.QWidget()
        self.tab_clip_arts = QtGui.QWidget()
        self.tab_line_drawings = QtGui.QWidget()

        self.addTab(self.tab_normal_images, "normal images")
        self.addTab(self.tab_clip_arts, "cliparts")
        self.addTab(self.tab_line_drawings, "line drawings")

        self.add_layouts(self.tab_normal_images)
        self.add_layouts(self.tab_clip_arts)
        self.add_layouts(self.tab_line_drawings)

        self.thread_fetch_normal_image_urls = ThreadFetchImageUrls('cat', Language.english, None, self.tab_normal_images)
        self.connect(self.thread_fetch_normal_image_urls, QtCore.SIGNAL(signal_image_urls_fetched), self.fetch_images)
        self.thread_fetch_normal_image_urls.start()

        self.thread_fetch_clipart_image_urls = ThreadFetchImageUrls('cat', Language.english, 'clipart', self.tab_clip_arts)
        self.connect(self.thread_fetch_clipart_image_urls, QtCore.SIGNAL(signal_image_urls_fetched), self.fetch_images)
        self.thread_fetch_clipart_image_urls.start()

        self.thread_fetch_linedrawing_image_urls = ThreadFetchImageUrls('cat', Language.english, 'line drawing', self.tab_line_drawings)
        self.connect(self.thread_fetch_linedrawing_image_urls, QtCore.SIGNAL(signal_image_urls_fetched), self.fetch_images)
        self.thread_fetch_linedrawing_image_urls.start()

        # delay for first showing the dialog
        # QtCore.QTimer.singleShot(100, self.fetch_images)

    ###########################################################
    def fetch_images(self, image_urls, tab):
        lock = threading.Lock()
        # threads
        for i in range(0, 10):
            threads_fetch_image.append(ThreadFetchImage(image_urls, lock, tab))
            self.connect(threads_fetch_image[i], QtCore.SIGNAL(signal_image_fetched), self.add_image_to_dialog)
            threads_fetch_image[i].start()

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
        view.display_image(image)
        view.fit()
        image_number = int(image_number)
        while image_number >= len(tab.horizontal_layouts) * NUMBER_OF_IMAGES_IN_EACH_RAW:
            tab.horizontal_layouts.append(QtGui.QHBoxLayout())
            tab.vertical_layout_scroll.addLayout(tab.horizontal_layouts[-1])
        tab.horizontal_layouts[image_number // NUMBER_OF_IMAGES_IN_EACH_RAW].addWidget(view)


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
        self.scene.setBackgroundBrush(QtCore.Qt.white)
        self.setScene(self.scene)
        self.setSceneRect(0, 0, w, h)
        self.update_pan_status()
        self.number = number
        self.resize(w, h)

    # def mouseReleaseEvent(self, event):
    #     print('mouseReleaseEvent', QtGui.QCursor.pos())
    #     return QtGui.QGraphicsView.mouseReleaseEvent(self, event)

    #####################################################################
    def mousePressEvent(self, event):
        if event.buttons() == QtCore.Qt.LeftButton:
            pos = self.mapToScene(event.pos())
            # print('left:', pos.x(), pos.y())
            # previousAnchor = self.transformationAnchor()
            # # have to set this for self.translate() to work.
            # self.setTransformationAnchor(QtGui.QGraphicsView.NoAnchor)
            # self.translate(-1000, -1000)
            # # have to reset the anchor or scaling (zoom) stops working:
            # self.setTransformationAnchor(previousAnchor)
            # # self.scale(0.5,0.5)
        if event.buttons() == QtCore.Qt.RightButton:
            pos = self.mapToScene(event.pos())
            self.fit()
            print(self.viewport().geometry())
            print(self.mapToScene(self.viewport().geometry().bottomRight()))
            print(self.scene.sceneRect())
            # print('right:', pos.x(), pos.y())
            # previousAnchor = self.transformationAnchor()
            # # have to set this for self.translate() to work.
            # self.setTransformationAnchor(QtGui.QGraphicsView.NoAnchor)
            # self.translate(1000, 1000)
            # # have to reset the anchor or scaling (zoom) stops working:
            # self.setTransformationAnchor(previousAnchor)
            # # self.scale(2,2)
        # print('mousePressEvent', QtGui.QCursor.pos())
        return QtGui.QGraphicsView.mousePressEvent(self, event)

    #####################################################################
    def mouseMoveEvent(self, event):
        pos = self.mapToScene(event.pos())
        # print('move:', pos.x(), pos.y())
        return QtGui.QGraphicsView.mouseMoveEvent(self, event)

    #####################################################################
    def wheelEvent(self, event):
        if self.scene is not None:
            if event.delta() > 0:
                factor = 1.25
            else:
                factor = 0.8
            self.scale(factor, factor)
            self.update_pan_status()
        return QtGui.QGraphicsView.wheelEvent(self, event)

    #####################################################################
    def resizeEvent(self, QResizeEvent):
        pass
        self.update_pan_status()

        return QtGui.QGraphicsView.resizeEvent(self, QResizeEvent)

    #####################################################################
    def update_pan_status(self):
        rect = QtCore.QRectF(self.sceneRect())
        view_rect = self.viewport().rect()
        scene_rect = self.transform().mapRect(rect)
        if scene_rect.bottom() > view_rect.bottom() or \
            scene_rect.right() > view_rect.right():
            self.setDragMode(QtGui.QGraphicsView.ScrollHandDrag)
        else:
            self.setDragMode(QtGui.QGraphicsView.NoDrag)

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
    #####################################################################
    def display_image(self, image):
        self.scene.clear()
        # w, h = image.size
        self.imgQ = ImageQt.ImageQt(image)  # we need to hold reference to imgQ, or it will crash
        pixMap = QtGui.QPixmap.fromImage(self.imgQ)
        self.scene.addPixmap(pixMap)
        # self.fitInView(QtCore.QRectF(0, 0, w, h), QtCore.Qt.KeepAspectRatio)
        self.scene.update()


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

        print self.url
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

w = ImagesDialog()

w.show()

sys.exit(app.exec_())





