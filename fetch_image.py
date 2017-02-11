# -*- coding: utf-8 -*-

import pygame
import sys
from PyQt4 import QtGui

from fetch_image_tools.general_tools import Language, ImageType
from fetch_image_tools.widget_tools import Dialog, TabWidgetProgress, Widget
from fetch_image_tools.dictionary_tools import DictionaryTab
from fetch_image_tools.image_tools import ImageTab
from fetch_image_note_tools import get_fields, get_model, get_language, get_main_word, get_meida_dir


#####################################################################
class MainDialog(Dialog):
    # *************************
    def __init__(self, notes, parent=None):
        super(MainDialog, self).__init__(parent)

        pygame.init()

        self.notes = notes
        self.words = dict()
        self.languages = dict()
        self.full_image_file_names = dict()
        self.selected_images = dict()
        self.main_tab_widgets = dict()
        if len(notes) > 0:
            self.media_dir = get_meida_dir(notes[0])

        # window
        self.resize(1000, 1000)

        # main layout
        button_next = QtGui.QPushButton('Next')
        button_next.clicked.connect(self.next_note)
        button_previous = QtGui.QPushButton('Previous')
        button_previous.clicked.connect(self.previous_note)
        layout = QtGui.QHBoxLayout()
        layout.addWidget(button_previous)
        layout.addWidget(button_next)
        layout.addStretch()
        self.main_layout = QtGui.QVBoxLayout()
        self.setLayout(self.main_layout)
        self.main_layout.addLayout(layout)

        for note in notes:
            self.words[note] = get_main_word(note)
            self.languages[note] = get_language(note)
            self.full_image_file_names[note] = None
            self.selected_images[note] = None

            # main tab
            self.main_tab_widgets[note] = TabWidgetProgress(mother=self)

            # word fields
            self.main_tab_widgets[note].tab_word_fields = Widget(self.main_tab_widgets[note])
            self.main_tab_widgets[note].addTab(self.main_tab_widgets[note].tab_word_fields, 'word')

            # main word
            self.add_word_fields(note)

            # dictionaries
            self.main_tab_widgets[note].tab_dictionaries = TabWidgetProgress(mother=self.main_tab_widgets[note])
            self.main_tab_widgets[note].addTab(self.main_tab_widgets[note].tab_dictionaries, 'dictinoaries')

            # main word dictionaries
            self.add_dictionary_tabs(note)

            # images
            self.main_tab_widgets[note].tab_images = TabWidgetProgress(mother=self.main_tab_widgets[note])
            self.main_tab_widgets[note].addTab(self.main_tab_widgets[note].tab_images, 'images')

            # main word images
            self.add_image_tabs(note)

            self.main_layout.addWidget(self.main_tab_widgets[note])
            self.main_tab_widgets[note].hide()

        self.current_note_index = 0
        self.setWindowTitle(self.words[self.notes[self.current_note_index]])
        self.show_main_tab(notes[self.current_note_index])


    ###########################################################
    def show_main_tab(self, note):
        self.setWindowTitle(get_main_word(note))
        main_tab = self.main_tab_widgets[note]
        main_tab.show()
        for dictionary_tab in main_tab.findChildren(DictionaryTab):
            if not dictionary_tab.browsing_started:
                dictionary_tab.start()
        for image_tab in main_tab.findChildren(ImageTab):
            if not image_tab.fetching_started:
                image_tab.start()


    ###########################################################
    def next_note(self):
        if self.current_note_index + 1 < len(self.main_tab_widgets):
            self.main_tab_widgets[self.notes[self.current_note_index]].hide()
            self.current_note_index += 1
            self.show_main_tab(self.notes[self.current_note_index])

    ###########################################################
    def previous_note(self):
        if self.current_note_index > 0:
            self.main_tab_widgets[self.notes[self.current_note_index]].hide()
            self.current_note_index -= 1
            self.show_main_tab(self.notes[self.current_note_index])

    ###########################################################
    def add_word_fields(self, note):
        layout = QtGui.QVBoxLayout()
        fields, values = get_fields(note)
        for i in range(len(fields)):
            label = QtGui.QLabel(fields[i])
            line = QtGui.QTextEdit(values[i])
            h_layout = QtGui.QHBoxLayout()
            h_layout.addWidget(label)
            h_layout.addWidget(line)
            layout.addLayout(h_layout)
        self.main_tab_widgets[note].tab_word_fields.setLayout(layout)

    ###########################################################
    def add_dictionary_tabs(self, note):
        # english dictionaries
        tab = TabWidgetProgress(mother=self.main_tab_widgets[note].tab_dictionaries, closable=True)
        self.main_tab_widgets[note].tab_dictionaries.addTab(tab, get_main_word(note))
        for dictionary in DictionaryTab.dictionaries[get_language(note)]:
            dictionary_tab = DictionaryTab(dictionary, get_main_word(note), mother=tab)
            tab.addTab(dictionary_tab, dictionary_tab.name)

    ###########################################################
    def add_image_tabs(self, note):
        tab = TabWidgetProgress(mother=self.main_tab_widgets[note].tab_images, closable=True)
        self.main_tab_widgets[note].tab_images.addTab(tab, get_main_word(note))

        for image_type in sorted(ImageType.items, key=lambda x:x):
            image_tab = ImageTab(get_main_word(note), get_language(note), image_type, mother=tab)
            tab.addTab(image_tab, ImageType.names[image_type])

    ###########################################################
    def closeEvent(self, QCloseEvent):
        for tab_image in self.findChildren(ImageTab):
            tab_image.quit()
        for tab_dictionary in self.findChildren(DictionaryTab):
            tab_dictionary.quit()
        for tab_image in self.findChildren(ImageTab):
            tab_image.terminate()
        for tab_dictionary in self.findChildren(DictionaryTab):
            tab_dictionary.terminate()






