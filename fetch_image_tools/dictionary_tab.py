# -*- coding: utf-8 -*-

import tempfile
import pygame
import os
import math
from PyQt4 import QtGui, QtCore
from PyQt4 import QtWebKit
from general_tools import enum, Result, Language, find_unique_file_name
from thread_tools import ThreadFetchAudio, ThreadFetchImage
from widget_tools import *
from browser_tools import Browser, InlineBrowser


# ===========================================================================
class DictionaryTab(Widget, Result):
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

    # ===========================================================================
    def __init__(self, address_pair, mother, parent=None):
        Widget.__init__(self, mother, parent)
        Result.__init__(self)
        
        self.browsing_started = False
        self.name = address_pair[0]
        self.web_address = address_pair[1]

        self.browser = Browser(self.web_address, mother=self)
        self.connect(self.browser, Browser.signal_started, lambda: self.update_status(InlineBrowser.SignalType.started))
        self.connect(self.browser, Browser.signal_progress, lambda progress: self.update_status(InlineBrowser.SignalType.progress, progress))
        self.connect(self.browser, Browser.signal_finished, lambda ok: self.update_status(InlineBrowser.SignalType.finished, ok))
        self.add_widget(self.browser)

    # ===========================================================================
    def create_url(self, word):
        word = word.split()
        word = '+'.join(word)
        return self.web_address + word

    # ===========================================================================
    def update_status(self, singal_type, param=None):
        name = self.name
        tab_dictionaries = self.mother
        index = tab_dictionaries.indexOf(self)
        tab_bar = tab_dictionaries.tabBar()
        if singal_type == InlineBrowser.SignalType.started:
            self.progress = 0
            tab_bar.setTabTextColor(index, Result.started_color)
            tab_dictionaries.update_progress()
        if singal_type == InlineBrowser.SignalType.progress:
            progress = param
            self.in_progress = True
            self.progress = progress
            tab_bar.setTabText(index, name + ' ' + str(progress) + '%')
            tab_bar.setTabTextColor(index, Result.in_progress_color)
            tab_dictionaries.update_progress()
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
            tab_dictionaries.update_progress()

    # ===========================================================================
    def quit(self):
        self.browser.quit()

    # ===========================================================================
    def terminate(self):
        self.browser.terminate()

    # ===========================================================================
    def start(self, word):
        if not self.browsing_started:
            self.browsing_started = True
            self.browser.go(self.create_url(word))

    # ===========================================================================
    def stop(self):
        self.browsing_started = False
        self.browser.stop()


