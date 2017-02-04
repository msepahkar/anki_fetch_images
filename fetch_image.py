# -*- coding: utf-8 -*-

import pygame
import sys
from PyQt4 import QtGui

from fetch_image_tools.general_tools import Language, ImageType
from fetch_image_tools.widget_tools import Dialog, TabWidgetProgress, Widget
from fetch_image_tools.dictionary_tools import DictionaryTab
from fetch_image_tools.image_tools import ImageTab


#####################################################################
class MainDialog(Dialog):
    # *************************
    def __init__(self, word, language, media_dir, parent=None):
        super(MainDialog, self).__init__(parent)

        pygame.init()

        self.word = word
        self.media_dir = media_dir
        self.full_image_file_name = None
        self.selected_image = None

        # window
        self.setWindowTitle(word)
        self.resize(1000, 1000)

        # layout
        self.add_layout()

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
        # self.add_image_tabs(word, language)

    ###########################################################
    def add_layout(self):
        self.layout = QtGui.QVBoxLayout()
        self.setLayout(self.layout)
        self.button_next = QtGui.QPushButton('Next')
        self.button_previous = QtGui.QPushButton('Previous')
        layout = QtGui.QHBoxLayout()
        layout.addWidget(self.button_previous)
        layout.addWidget(self.button_next)
        layout.addStretch()
        self.layout.addLayout(layout)
        self.main_tab_widget = TabWidgetProgress(mother=self)
        self.layout.addWidget(self.main_tab_widget)
        self.status_line = QtGui.QLabel('no status')
        self.layout.addWidget(self.status_line)

    ###########################################################
    def add_dictionary_tabs(self, word, language):
        # english dictionaries
        tab = TabWidgetProgress(mother=self.main_tab_widget.tab_dictionaries, closable=True)
        self.main_tab_widget.tab_dictionaries.addTab(tab, word)
        for dictionary in DictionaryTab.dictionaries[language]:
            dictionary_tab = DictionaryTab(dictionary, mother=tab)
            tab.addTab(dictionary_tab, dictionary_tab.name)
            dictionary_tab.browse(word)

    ###########################################################
    def add_image_tabs(self, word, language):
        tab = TabWidgetProgress(mother=self.main_tab_widget.tab_images, closable=True)
        self.main_tab_widget.tab_images.addTab(tab, word)

        for image_type in ImageType.items:
            image_tab = ImageTab(word, language, image_type, mother=tab)
            tab.addTab(image_tab, ImageType.names[image_type])
            image_tab.start_fetching()

    ###########################################################
    def closeEvent(self, QCloseEvent):
        for tab_image in self.findChildren(ImageTab):
            tab_image.quit()
        for tab_dictionary in self.findChildren(DictionaryTab):
            tab_dictionary.quit()
        for tab_image in self.findChildren(ImageTab):
            tab_image.terminate()


app = QtGui.QApplication(sys.argv)

w = MainDialog('hello', Language.english, '/home/mehdi')

w.show()

app.exec_()

# if w.full_image_file_name is not None:
#     print w.full_image_file_name





