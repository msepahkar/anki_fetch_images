# -*- coding: utf-8 -*-

import pygame
import sys
from PyQt4 import QtGui

from fetch_image_tools.general_tools import Language, ImageType
from fetch_image_tools.widget_tools import *
from fetch_image_tools.dictionary_tools import DictionaryTab
from fetch_image_tools.image_tools import ImageTab, ImageGraphicsView
from fetch_image_note_tools import *


# ===========================================================================
class MainDialog(Dialog, Result):
    # ===========================================================================
    def __init__(self, notes, parent=None):
        Dialog.__init__(self, parent)
        Result.__init__(self)

        pygame.init()

        self.dirty = dict()
        self.main_tabs = dict()

        # window
        self.resize(1000, 1000)

        # main layout
        word_buttons = VerticalLayout([Button('Word +', self.next_note), Button('Word -', self.previous_note)])
        dict_buttons = VerticalLayout([Button('Dict go', self.start_dictionaries), Button('Dict no', self.stop_dictionarires)])
        image_buttons = VerticalLayout([Button('Image go', self.start_images), Button('Image no', self.stop_images)])
        dict_all_buttons = VerticalLayout([Button('Dict all go', self.start_all_dictionaries), Button('Dict all no', self.stop_all_dictionaries)])
        image_all_buttons = VerticalLayout([Button('Image all go', self.start_all_images), Button('Image all no', self.stop_all_images)])
        update_buttons = VerticalLayout([Button('update', self.update_note), Button('update all', self.update_all_notes)])

        button_new = Button('new', self.new_note)

        self.add_row_widgets(word_buttons, button_new, UiDesign.stretch, dict_buttons, image_buttons,
                             dict_all_buttons, image_all_buttons, UiDesign.stretch, update_buttons)

        self.notes = notes
        for note in self.notes:
            self.add_note(note)

        self.current_note_index = 0
        self.show_main_tab(notes[self.current_note_index])

    # ===========================================================================
    def add_note(self, note):
        self.dirty[note] = False

        # main tab
        self.main_tabs[note] = TabWidgetProgress(mother=self)
        self.connect(self.main_tabs[note], TabWidgetProgress.signal_update, self.update_progress)

        # word fields
        self.main_tabs[note].tab_word_fields = Widget(self.main_tabs[note])
        self.main_tabs[note].addTab(self.main_tabs[note].tab_word_fields, 'word')

        # main word
        fields, values = get_fields(note)
        for i in range(len(fields)):
            self.main_tabs[note].tab_word_fields.add_text_edit(fields[i], values[i])

        # dictionaries
        self.main_tabs[note].tab_dictionaries = TabWidgetProgress(mother=self.main_tabs[note], closable=True, action=lambda: self.stop_dictionarires(note))
        self.main_tabs[note].addTab(self.main_tabs[note].tab_dictionaries, 'dictinoaries')

        # main word dictionaries
        self.add_dictionary_tabs(note)

        # images
        self.main_tabs[note].tab_images = TabWidgetProgress(mother=self.main_tabs[note], closable=True, action=lambda: self.stop_images(note))
        self.main_tabs[note].addTab(self.main_tabs[note].tab_images, 'images')

        # main word images
        self.add_image_tabs(note)

        self.main_layout.addWidget(self.main_tabs[note])
        self.main_tabs[note].hide()

    # ===========================================================================
    def show_main_tab(self, note):
        self.setWindowTitle(get_main_word(note))
        main_tab = self.main_tabs[note]
        main_tab.show()

    # ===========================================================================
    def stop_dictionary(self, tab, index):
        tab.widget(index).stop()

    # ===========================================================================
    def stop_image(self, tab, index):
        tab.widget(index).stop()

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
    def start_dictionaries(self, note=None):
        if note is None:
            note = self.notes[self.current_note_index]
        main_tab = self.main_tabs[note]
        for dictionary_tab in main_tab.findChildren(DictionaryTab):
            if not dictionary_tab.browsing_started:
                dictionary_tab.start()

    # ===========================================================================
    def stop_dictionarires(self, note=None):
        if note is None:
            note = self.notes[self.current_note_index]
        main_tab = self.main_tabs[note]
        for dictionary_tab in main_tab.findChildren(DictionaryTab):
            dictionary_tab.stop()

    # ===========================================================================
    def start_images(self, note=None):
        if note is None:
            note = self.notes[self.current_note_index]
        main_tab = self.main_tabs[note]
        for image_tab in main_tab.findChildren(ImageTab):
            if not image_tab.fetching_started:
                image_tab.start()

    # ===========================================================================
    def stop_images(self, note=None):
        if note is None:
            note = self.notes[self.current_note_index]
        main_tab = self.main_tabs[note]
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
    def start_all_dictionaries(self):
        for note in self.notes:
            main_tab = self.main_tabs[note]
            for dictionary_tab in main_tab.findChildren(DictionaryTab):
                if not dictionary_tab.browsing_started:
                    dictionary_tab.start()

    # ===========================================================================
    def stop_all_dictionaries(self):
        for note in self.notes:
            main_tab = self.main_tabs[note]
            for dictionary_tab in main_tab.findChildren(DictionaryTab):
                dictionary_tab.stop()

    # ===========================================================================
    def start_all_images(self):
        for note in self.notes:
            main_tab = self.main_tabs[note]
            for image_tab in main_tab.findChildren(ImageTab):
                if not image_tab.fetching_started:
                    image_tab.start()

    # ===========================================================================
    def stop_all_images(self):
        for note in self.notes:
            main_tab = self.main_tabs[note]
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
        tab = TabWidgetProgress(mother=self.main_tabs[note].tab_dictionaries, closable=True, action=lambda index: self.stop_dictionary(tab, index))
        self.main_tabs[note].tab_dictionaries.addTab(tab, get_main_word(note))
        for dictionary in DictionaryTab.dictionaries[get_language(note)]:
            dictionary_tab = DictionaryTab(dictionary, note, mother=tab)
            tab.addTab(dictionary_tab, dictionary_tab.name)

    # ===========================================================================
    def add_image_tabs(self, note):
        tab = TabWidgetProgress(mother=self.main_tabs[note].tab_images, closable=True, action=lambda index: self.stop_image(tab, index))
        self.main_tabs[note].tab_images.addTab(tab, get_main_word(note))

        for image_type in sorted(ImageType.items, key=lambda x:x):
            image_tab = ImageTab(note, get_language(note), image_type, mother=tab)
            self.connect(image_tab, ImageGraphicsView.set_image_signal, self.set_image)
            tab.addTab(image_tab, ImageType.names[image_type])

    # ===========================================================================
    def set_image(self, note, image):
        set_image(note, image)
        self.dirty[note] = True

    # ===========================================================================
    def update_progress(self):
        self.reset_progress()
        
        total_started = 0
        total_failed = 0
        total_succeeded = 0
        total_in_progress = 0

        for note in self.main_tabs:
            main_tab = self.main_tabs[note]
            if main_tab.started:
                total_started += 1
            if main_tab.failed:
                total_failed += 1
            if main_tab.succeeded:
                total_succeeded += 1
                self.progress += 100
            if main_tab.in_progress:
                total_in_progress += 1
                self.progress += main_tab.progress

        if total_in_progress + total_succeeded > 0:
            self.progress /= (total_in_progress + total_succeeded)
            
        current_word = get_main_word(self.notes[self.current_note_index])

        # all started
        if total_started == len(self.main_tabs):
            self.started = True
            
            self.setWindowTitle(current_word)
            # tab_bar.setTabTextColor(index, Result.started_color)
        # all failed
        elif total_failed == len(self.main_tabs):
            self.failed = True
            self.setWindowTitle(current_word)
            # tab_bar.setTabTextColor(index, Result.failed_color)
        # all succeeded
        elif total_succeeded == len(self.main_tabs):
            self.succeeded = True
            self.setWindowTitle(current_word)
            # tab_bar.setTabTextColor(index, Result.succeeded_color)
        # all in progress
        elif total_in_progress == len(self.main_tabs):
            self.in_progress = True
            self.setWindowTitle(current_word + ' ' + str(self.progress) + '%')
            # tab_bar.setTabTextColor(index, Result.in_progress_color)
        # at least one in progress
        elif total_in_progress > 0:
            self.in_progress = True
            self.setWindowTitle(current_word + ' ' + str(self.progress) + '%')
            # any failed or any started?
            # if total_failed > 0 or total_started > 0:
                # tab_bar.setTabTextColor(index, Result.weak_in_progress_color)
            # no fail and no started
            # else:
            #     tab_bar.setTabTextColor(index, Result.in_progress_color)
        # nothing in progress, but at least one started
        elif total_started > 0:
            self.started = True
            self.setWindowTitle(current_word)
            # tab_bar.setTabTextColor(index, Result.started_color)
        # nothing in progress and nothing started, but at least one succeeded
        elif total_succeeded > 0:
            self.succeeded = True
            # any failed?
            if total_failed > 0:
                self.setWindowTitle(current_word)
                # tab_bar.setTabTextColor(index, Result.weak_succeeded_color)
            # no fail
            else:
                self.setWindowTitle(current_word)
                # tab_bar.setTabTextColor(index, Result.succeeded_color)

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






