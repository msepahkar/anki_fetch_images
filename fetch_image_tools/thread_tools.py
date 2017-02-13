# -*- coding: utf-8 -*-

import re
import urllib2, urllib
from StringIO import StringIO
from PyQt4 import QtCore
from PIL import Image
from general_tools import Language, ImageType

import urllib2, sys


#####################################################################
def chunk_read(response, chunk_size=8192, report_hook=None):

    total_size = -1
    try:
        total_size = int(response.info().getheader('Content-Length').strip())
    except AttributeError:
        pass  # a response doesn't always include the "Content-Length" header

    bytes_so_far = 0
    buffer_ = StringIO()

    while True:
        chunk = response.read(chunk_size)
        buffer_.write(chunk)
        bytes_so_far += len(chunk)

        if not chunk:
            break

        if report_hook:
            report_hook(bytes_so_far, chunk_size, total_size)

    return buffer_


#####################################################################
class ThreadQuitException(Exception):
    pass


#####################################################################
class ThreadFetchImage(QtCore.QThread):
    signal_image_fetched = QtCore.SIGNAL('ThreadFetchImage.image_fetched')
    signal_image_ignored = QtCore.SIGNAL('ThreadFetchImage.image_ignored')

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
        self.quit_request = False
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
                    self.emit(ThreadFetchImage.signal_image_fetched, image_number, image)
                except ThreadQuitException:
                    print 'quitting thread ...'
                except Exception as e:
                    self.emit(ThreadFetchImage.signal_image_ignored, image_number)
            else:
                print 'quitting thread ...'
                break

    # *************************
    def quit(self):
        self.quit_request = True


#####################################################################
class ThreadFetchImageUrls(QtCore.QThread):
    signal_urls_fetched = QtCore.SIGNAL('ThreadFetchImageUrls.image_urls_fetched')
    signal_urls_fetching_started = QtCore.SIGNAL('ThreadFetchImageUrls.image_urls_fetching_started')

    # *************************
    def __init__(self, word, language, image_type):
        super(ThreadFetchImageUrls, self).__init__(None)
        self.word = word
        self.language = language
        self.image_type = image_type
        self.url = None

    # *************************
    def create_url(self):
        query = self.word
        if self.image_type == ImageType.clipart:
            query += ' clipart'
        elif self.image_type == ImageType.line_drawing:
            query += ' line drawing'
        query = query.split()
        query = '+'.join(query)
        if self.language == Language.english:
            self.url = "https://www.google.com/search?q=" + query + "&source=lnms&tbm=isch"
        elif self.language == Language.german:
            self.url = "https://www.google.de/search?q=" + query + "&source=lnms&tbm=isch"
        else:
            print 'unknown language'
        self.quit_request = False

    # *************************
    def run(self):
        self.quit_request = False
        self.create_url()
        header = {
            'User-Agent': "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2357.134 Safari/537.36"
        }

        if not self.quit_request:
            self.emit(ThreadFetchImageUrls.signal_urls_fetching_started)
            opened_url = urllib2.urlopen(urllib2.Request(self.url, headers=header))

            page = StringIO(opened_url.read())

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

            if not self.quit_request:
                self.emit(ThreadFetchImageUrls.signal_urls_fetched, image_urls)

    # *************************
    def quit(self):
        self.quit_request = True


#####################################################################
class ThreadFetchAudio(QtCore.QThread):
    signal_audio_fetched = QtCore.SIGNAL("ThreadFetchAudio.audio_fetched")
    signal_audio_fetching_progress = QtCore.SIGNAL("ThreadFetchAudio.audio_fetching_progress")

    # *************************
    def __init__(self, url, f_name):
        super(ThreadFetchAudio, self).__init__(None)
        self.url = url
        self.f_name = f_name
        self.quit_request = False

    # *************************
    def report(self, bytes_so_far, chunk_size, total_size):
        if self.quit_request:
            raise ThreadQuitException
        self.emit(self.signal_audio_fetching_progress, bytes_so_far, total_size)

    # *************************
    def run(self):
        self.quit_request = False
        header = {
            'User-Agent': "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2357.134 Safari/537.36"
        }

        try:
            response = urllib2.urlopen(urllib2.Request(str(self.url), headers=header))
            buffer_ = chunk_read(response, report_hook=self.report)
        except ThreadQuitException:
            return

        with open(self.f_name, 'wb') as f:
            f.write(buffer_.getvalue())

        self.emit(ThreadFetchAudio.signal_audio_fetched, True)

    # *************************
    def quit(self):
        self.quit_request = True


