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


images_queue_lock = threading.Lock()
processed_queue_lock = threading.Lock()
images_queue = []
processed_queue = []
processing_tag = "processing"
word_field = "Word"
update_signal = "update_results(QString, QString)"


def get_soup(url,header):
    return BeautifulSoup(urllib2.urlopen(urllib2.Request(url,headers=header)),'html.parser')


class ImagesDialog(QtGui.QDialog):
    # *************************
    def __init__(self, parent=None):
        super(ImagesDialog, self).__init__(parent)

        self.setWindowTitle("Images")

        self.resize(300, 300)
        self.move(300, 300)

        self.scrollArea = QtGui.QScrollArea(self)
        self.scrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents = QtGui.QWidget(self.scrollArea)
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 1000, 1000))
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)

        self.verticalLayout = QtGui.QVBoxLayout(self)
        self.verticalLayout.addWidget(self.scrollArea)

        layout = QtGui.QVBoxLayout(self.scrollAreaWidgetContents)
        self.setLayout(layout)

        self.threads = []
        for i in range(0, 10):
            self.threads.append(FetchingThread())
            self.connect(self.threads[i], QtCore.SIGNAL(update_signal), self.update_results)

        self.layouts_h = []
        for i in range(10):
            self.layouts_h.append(QtGui.QHBoxLayout())
            layout.addLayout(self.layouts_h[-1])

        query = 'cat'  # raw_input("query image")# you can change the query for the image  here
        image_type = "ActiOn"
        query = query.split()
        query = '+'.join(query)
        url = "https://www.google.com/search?q=" + query + "&source=lnms&tbm=isch"
        print url
        self.fetch_images(url)
        for thread in self.threads:
            thread.start()

    ###########################################################
    def fetch_images(self, url):
        header = {
            'User-Agent': "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2357.134 Safari/537.36"
        }
        image_type = "ActiOn"
        openned_url = urllib2.urlopen(urllib2.Request(url, headers=header))

        page = StringIO(openned_url.read())

        # find the directory the pronunciation
        pattern = re.compile('<img.*?>')
        img_tags = pattern.findall(page.getvalue())

        pattern = re.compile('src=".*?"')
        cntr = 1
        images = []
        sizes = []
        for img_tag in img_tags:
            image_urls = pattern.findall(img_tag)
            if len(image_urls) > 0:
                image_url = image_urls[0].replace('src="', '').replace('"', '')
                # print(image_url)
                with images_queue_lock:
                    images_queue.append((cntr, image_url))
                cntr += 1

    # *************************
    def start(self):
        # initialization should be done only once
        if not self.started:
            # consider initializations done
            self.started = True
            # add notes to the queue
            for noteId in self.noteIds:
                noteQueue.append(mw.col.getNote(noteId))
            for thread in self.threads:
                thread.start()

    # *************************
    def update_results(self, image_number, image):
        view = GraphicsView(1, 50, 50)
        # view.display_image(image)
        # view.fit()
        self.layouts_h[int(image_number) // 10].addWidget(view)


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
            print 'hello from: ' + str(self.number)
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
        print 'current size:', self.size()
        print 'old size:', event.oldSize()
        self.fit()

    #####################################################################
    def fit(self):
        if self.scene is not None:
            rect = QtCore.QRectF(self.sceneRect())
            if not rect.isNull():
                unity = self.transform().mapRect(QtCore.QRectF(0, 0, 1, 1))
                self.scale(1 / unity.width(), 1 / unity.height())
                # viewrect = self.viewport().rect()
                scenerect = self.transform().mapRect(rect)
                print self.size()
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


class FetchingThread(QtCore.QThread):
    # *************************
    def __init__(self):
        super(FetchingThread, self).__init__(None)

    # *************************
    def run(self):
        while len(images_queue) > 0:
            with images_queue_lock:
                # check if any note is left
                if len(images_queue) <= 0:
                    return
                # retrieve one note
                image_number, image_url = images_queue[0]
                print 'hi', image_number, image_url
                del images_queue[0]
            try:
                # image = Image.open(StringIO(urllib.urlopen(image_url).read()))
                image = 'hello'
                self.emit(QtCore.SIGNAL(update_signal), str(image_number), image)
                print image_number, 'ok'
                # break
            except Exception as e:
                print image_number, 'bad image', e


app = QtGui.QApplication(sys.argv)

w = ImagesDialog()

w.show()

sys.exit(app.exec_())





