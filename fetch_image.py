# -*- coding: utf-8 -*-

import pygame
import sys
from PyQt4 import QtGui

from fetch_image_tools.general_tools import Language, ImageType
from fetch_image_tools.widget_tools import *
from fetch_image_tools.dictionary_tools import DictionaryTab
from fetch_image_tools.image_tools import ImageTab
from fetch_image_note_tools import *


# ===========================================================================
class MainDialog(Dialog):
    # ===========================================================================
    def __init__(self, notes, parent=None):
        super(MainDialog, self).__init__(parent)

        pygame.init()

        self.dirty = dict()
        self.full_image_file_names = dict()
        self.selected_images = dict()
        self.main_tabs = dict()
        if len(notes) > 0:
            self.media_dir = get_meida_dir(notes[0])

        # window
        self.resize(1000, 1000)

        # main layout
        button_next = Button('Next', self.next_note)
        button_previous = Button('Previous', self.previous_note)
        button_start = Button('start', self.start)
        button_start_all = Button('start all', self.start_all)
        button_stop = Button('stop', self.stop)
        button_stop_all = Button('stop all', self.stop_all)
        button_update_all = Button('update all', self.update_all_notes)
        button_update = Button('update', self.update_note)
        button_new = Button('new', self.new_note)

        self.add_row_widgets(button_previous, button_next, button_start, button_stop, button_start_all, button_stop_all,
                             button_update_all, button_update, button_new)

        self.notes = notes
        for note in self.notes:
            self.add_note(note)

        self.current_note_index = 0
        self.setWindowTitle(get_main_word(self.notes[self.current_note_index]))
        self.show_main_tab(notes[self.current_note_index])

    # ===========================================================================
    def add_note(self, note):
        self.full_image_file_names[note] = None
        self.selected_images[note] = None
        self.dirty[note] = False

        # main tab
        self.main_tabs[note] = TabWidgetProgress(mother=self)

        # word fields
        self.main_tabs[note].tab_word_fields = Widget(self.main_tabs[note])
        self.main_tabs[note].addTab(self.main_tabs[note].tab_word_fields, 'word')

        # main word
        fields, values = get_fields(note)
        for i in range(len(fields)):
            self.main_tabs[note].tab_word_fields.add_text_edit(fields[i], values[i])

        # dictionaries
        self.main_tabs[note].tab_dictionaries = TabWidgetProgress(mother=self.main_tabs[note])
        self.main_tabs[note].addTab(self.main_tabs[note].tab_dictionaries, 'dictinoaries')

        # main word dictionaries
        self.add_dictionary_tabs(note)

        # images
        self.main_tabs[note].tab_images = TabWidgetProgress(mother=self.main_tabs[note])
        self.main_tabs[note].addTab(self.main_tabs[note].tab_images, 'images')

        # main word images
        # self.add_image_tabs(note)

        self.main_layout.addWidget(self.main_tabs[note])
        self.main_tabs[note].hide()

    # ===========================================================================
    def show_main_tab(self, note):
        self.setWindowTitle(get_main_word(note))
        main_tab = self.main_tabs[note]
        main_tab.show()

    # ===========================================================================
    def start(self, note=None):
        if note is None:
            note = self.notes[self.current_note_index]
        main_tab = self.main_tabs[note]
        for dictionary_tab in main_tab.findChildren(DictionaryTab):
            if not dictionary_tab.browsing_started:
                dictionary_tab.start()
        for image_tab in main_tab.findChildren(ImageTab):
            if not image_tab.fetching_started:
                image_tab.start()
                
    # ===========================================================================
    def stop(self, note=None):
        if note is None:
            note = self.notes[self.current_note_index]
        main_tab = self.main_tabs[note]
        for dictionary_tab in main_tab.findChildren(DictionaryTab):
            dictionary_tab.stop()
        for image_tab in main_tab.findChildren(ImageTab):
            image_tab.stop()

    # ===========================================================================
    def start_all(self):
        for note in self.notes:
            main_tab = self.main_tabs[note]
            for dictionary_tab in main_tab.findChildren(DictionaryTab):
                if not dictionary_tab.browsing_started:
                    dictionary_tab.start()
            for image_tab in main_tab.findChildren(ImageTab):
                if not image_tab.fetching_started:
                    image_tab.start()

    # ===========================================================================
    def stop_all(self):
        for note in self.notes:
            main_tab = self.main_tabs[note]
            for dictionary_tab in main_tab.findChildren(DictionaryTab):
                dictionary_tab.stop()
            for image_tab in main_tab.findChildren(ImageTab):
                image_tab.stop()

    # ===========================================================================
    def hide_main_tab(self, note):
        self.main_tabs[note].hide()

    # ===========================================================================
    def next_note(self):
        if self.current_note_index + 1 < len(self.main_tabs):
            current_note = self.notes[self.current_note_index]
            self.hide_main_tab(current_note)
            self.main_tabs[self.notes[self.current_note_index]].hide()
            self.current_note_index += 1
            self.show_main_tab(self.notes[self.current_note_index])

    # ===========================================================================
    def previous_note(self):
        if self.current_note_index > 0:
            current_note = self.notes[self.current_note_index]
            self.hide_main_tab(current_note)
            self.main_tabs[self.notes[self.current_note_index]].hide()
            self.current_note_index -= 1
            self.show_main_tab(self.notes[self.current_note_index])

    # ===========================================================================
    def update_note(self):
        note = self.notes[self.current_note_index]
        if self.dirty[note]:
            result = YesAllNoMessageBox(note.main_word + '\n is changed.', 'update it?').show()
            if result == YesAllNoMessageBox.YesAll:
                self.update_all_notes()
            elif result:
                update_note(note)

    # ===========================================================================
    def update_all_notes(self):
        result = YesNoCancelMessageBox('update all notes?', '').show()
        if not result:
            return False
        if result == YesNoCancelMessageBox.Yes:
            for note in self.notes:
                if self.dirty[note]:
                    update_note(note)
        return True

    # ===========================================================================
    def new_note(self):
        current_note = self.notes[self.current_note_index]
        self.hide_main_tab(current_note)
        note = new_note()
        self.notes.append(note)
        self.current_note_index = len(self.notes) - 1
        self.add_note(note)
        self.dirty[note] = True
        self.show_main_tab(note)

    # ===========================================================================
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
        self.main_tabs[note].tab_word_fields.setLayout(layout)

    # ===========================================================================
    def add_dictionary_tabs(self, note):
        # english dictionaries
        tab = TabWidgetProgress(mother=self.main_tabs[note].tab_dictionaries, closable=True)
        self.main_tabs[note].tab_dictionaries.addTab(tab, get_main_word(note))
        for dictionary in DictionaryTab.dictionaries[get_language(note)]:
            dictionary_tab = DictionaryTab(dictionary, get_main_word(note), mother=tab)
            tab.addTab(dictionary_tab, dictionary_tab.name)

    # ===========================================================================
    def add_image_tabs(self, note):
        tab = TabWidgetProgress(mother=self.main_tabs[note].tab_images, closable=True)
        self.main_tabs[note].tab_images.addTab(tab, get_main_word(note))

        for image_type in sorted(ImageType.items, key=lambda x:x):
            image_tab = ImageTab(get_main_word(note), get_language(note), image_type, mother=tab)
            tab.addTab(image_tab, ImageType.names[image_type])

    # ===========================================================================
    def closeEvent(self, event):
        for note in self.notes:
            if self.dirty[note]:
                if not self.update_all_notes():
                    event.ignore()
                    return
        for tab_image in self.findChildren(ImageTab):
            tab_image.quit()
        for tab_dictionary in self.findChildren(DictionaryTab):
            tab_dictionary.quit()
        for tab_image in self.findChildren(ImageTab):
            tab_image.terminate()
        for tab_dictionary in self.findChildren(DictionaryTab):
            tab_dictionary.terminate()






