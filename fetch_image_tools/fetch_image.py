# -*- coding: utf-8 -*-

import pygame
import sys
from PyQt4 import QtGui
from aqt import mw
from anki import notes

from general_tools import Language, ImageType
from widget_tools import *
from dictionary_tab import DictionaryTab, AudioListWidget
from image_tab import ImageTab, InlineBrowser
from main_word_tab import MainWordTab, ExtendedNote


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
        dict_buttons = VerticalLayout([Button('Dict go', self.start_dictionaries), Button('Dict no', self.stop_dictionaries)])
        image_buttons = VerticalLayout([Button('Image go', self.start_images), Button('Image no', self.stop_images)])
        dict_and_image_buttons = VerticalLayout([Button('Dict Image go', self.start_dictionaries_and_images), Button('Dict Image no', self.stop_dictionaries_and_images)])
        update_buttons = VerticalLayout([Button('update', lambda:self.update_note(self.extended_notes[self.current_note_index])), Button('update all', self.update_all_notes)])

        button_new = Button('new', self.new_note)
        button_stop_all = Button('stop all', self.stop_all)

        self.add_row_widgets(word_buttons, button_new, UiDesign.stretch, dict_buttons, image_buttons,
                             dict_and_image_buttons, button_stop_all, UiDesign.stretch, update_buttons)

        self.extended_notes = []
        for note in notes:
            self.extended_notes.append(ExtendedNote(note))
            self.add_note(self.extended_notes[-1])

        self.current_note_index = 0
        self.show_main_tab(self.extended_notes[self.current_note_index])

    # ===========================================================================
    def add_note(self, extended_note):
        self.dirty[extended_note] = False

        # main tab
        self.main_tabs[extended_note] = TabWidgetProgress(mother=self)
        self.connect(self.main_tabs[extended_note], TabWidgetProgress.signal_update, self.update_progress)

        # main word
        self.main_tabs[extended_note].tab_main_word = MainWordTab(extended_note, parent=self.main_tabs[extended_note])
        self.connect(self.main_tabs[extended_note].tab_main_word, MainWordTab.word_changed_signal, lambda: self.set_dirty(extended_note))
        self.main_tabs[extended_note].addTab(self.main_tabs[extended_note].tab_main_word, 'word')

        # dictionaries
        self.main_tabs[extended_note].tab_dictionaries = TabWidgetProgress(mother=self.main_tabs[extended_note], closable=True, action=lambda: self.stop_dictionaries(extended_note))
        self.main_tabs[extended_note].addTab(self.main_tabs[extended_note].tab_dictionaries, 'dictionaries')

        # main word dictionaries
        self.add_dictionary_tabs(extended_note)

        # images
        self.main_tabs[extended_note].tab_images = TabWidgetProgress(mother=self.main_tabs[extended_note], closable=True, action=lambda: self.stop_images(extended_note))
        self.main_tabs[extended_note].addTab(self.main_tabs[extended_note].tab_images, 'images')

        # main word images
        self.add_image_tabs(extended_note)

        # main tab for this word
        self.main_layout.addWidget(self.main_tabs[extended_note])
        self.main_tabs[extended_note].hide()

    # ===========================================================================
    def show_main_tab(self, extended_note):
        self.setWindowTitle(extended_note.main_word())
        main_tab = self.main_tabs[extended_note]
        main_tab.show()

    # ===========================================================================
    def start_dictionaries(self, extended_note=None):
        if extended_note is None:
            extended_note = self.extended_notes[self.current_note_index]
        main_tab = self.main_tabs[extended_note]
        for dictionary_tab in main_tab.findChildren(DictionaryTab):
            if not dictionary_tab.browsing_started:
                dictionary_tab.start(extended_note.main_word())

    # ===========================================================================
    def stop_dictionaries(self, extended_note=None):
        if extended_note is None:
            extended_note = self.extended_notes[self.current_note_index]
        main_tab = self.main_tabs[extended_note]
        for dictionary_tab in main_tab.findChildren(DictionaryTab):
            dictionary_tab.stop()

    # ===========================================================================
    def start_images(self, extended_note=None):
        if extended_note is None:
            extended_note = self.extended_notes[self.current_note_index]
        main_tab = self.main_tabs[extended_note]
        for image_tab in main_tab.findChildren(ImageTab):
            if not image_tab.browsing_started:
                image_tab.start()

    # ===========================================================================
    def stop_images(self, extended_note=None):
        if extended_note is None:
            extended_note = self.extended_notes[self.current_note_index]
        main_tab = self.main_tabs[extended_note]
        for image_tab in main_tab.findChildren(ImageTab):
            image_tab.stop()

    # ===========================================================================
    def start_dictionaries_and_images(self, extended_note=None):
        self.start_dictionaries(extended_note)
        self.start_images(extended_note)
    
    # ===========================================================================
    def stop_dictionaries_and_images(self, extended_note=None):
        self.stop_dictionaries(extended_note)
        self.stop_images(extended_note)
    
    # ===========================================================================
    def stop_all(self):
        for note in self.extended_notes:
            main_tab = self.main_tabs[note]
            for dictionary_tab in main_tab.findChildren(DictionaryTab):
                dictionary_tab.stop()
            for image_tab in main_tab.findChildren(ImageTab):
                image_tab.stop()

    # ===========================================================================
    def hide_main_tab(self, extended_note):
        self.main_tabs[extended_note].hide()

    # ===========================================================================
    def next_note(self):
        if self.current_note_index + 1 < len(self.main_tabs):
            current_note = self.extended_notes[self.current_note_index]
            self.hide_main_tab(current_note)
            self.main_tabs[self.extended_notes[self.current_note_index]].hide()
            self.current_note_index += 1
            self.show_main_tab(self.extended_notes[self.current_note_index])

    # ===========================================================================
    def previous_note(self):
        if self.current_note_index > 0:
            current_note = self.extended_notes[self.current_note_index]
            self.hide_main_tab(current_note)
            self.main_tabs[self.extended_notes[self.current_note_index]].hide()
            self.current_note_index -= 1
            self.show_main_tab(self.extended_notes[self.current_note_index])

    # ===========================================================================
    def update_note(self, extended_note):
        extended_note.flush()
        extended_note.flush()
        self.dirty[extended_note] = False

    # ===========================================================================
    def update_all_notes(self):
        result = YesNoCancelMessageBox('update all notes?', '').show()
        if not result:
            return False
        if result == YesNoCancelMessageBox.Yes:
            for note in self.extended_notes:
                if self.dirty[note]:
                    self.update_note(note)
        return True

    # ===========================================================================
    def new_note(self):
        current_note = self.extended_notes[self.current_note_index]
        self.hide_main_tab(current_note)

        model = mw.col.models.byName(current_note.model()['name'])
        model["did"] = current_note.model()['did']

        note = notes.Note(mw.col, model)
        note[model['flds'][0]['name']]='new'
        mw.col.addNote(note)
        for tag in current_note.tags:
            note.addTag(tag)

        self.extended_notes.append(ExtendedNote(note))
        self.current_note_index = len(self.extended_notes) - 1
        self.add_note(self.extended_notes[-1])
        self.dirty[self.extended_notes[-1]] = True
        self.show_main_tab(self.extended_notes[-1])

    # ===========================================================================
    def add_dictionary_tabs(self, extended_note):
        # english dictionaries
        tab = TabWidgetProgress(mother=self.main_tabs[extended_note].tab_dictionaries, closable=True, action=lambda index: self.stop_dictionary(tab, index))
        self.main_tabs[extended_note].tab_dictionaries.addTab(tab, extended_note.main_word())
        for dictionary in DictionaryTab.dictionaries[extended_note.language()]:
            dictionary_tab = DictionaryTab(dictionary, mother=tab)
            self.connect(dictionary_tab.browser.audio_window, AudioListWidget.set_audio_signal, self.main_tabs[extended_note].tab_main_word.set_audio)
            self.connect(dictionary_tab.browser.audio_window, AudioListWidget.set_audio_signal, lambda x: self.set_dirty(extended_note))
            tab.addTab(dictionary_tab, dictionary_tab.name)

    # ===========================================================================
    def stop_dictionary(self, tab, index):
        tab.widget(index).stop()

    # ===========================================================================
    def add_image_tabs(self, extended_note):
        tab = TabWidgetProgress(mother=self.main_tabs[extended_note].tab_images, closable=True, action=lambda index: self.stop_image(tab, index))
        self.main_tabs[extended_note].tab_images.addTab(tab, extended_note.main_word())

        for image_type in sorted(ImageType.items, key=lambda x:x):
            # image_tab = ImageTabOld(extended_note, extended_note.language(), image_type, mother=tab)
            image_tab = ImageTab(extended_note, extended_note.language(), image_type, mother=tab)
            # self.connect(self.main_tabs[extended_note].tab_main_word, MainWordTab.word_changed_signal, image_tab.update_word)
            image_tab.browser.inline_browser.set_image_signal.connect(self.main_tabs[extended_note].tab_main_word.set_image)
            image_tab.browser.inline_browser.set_image_signal.connect(lambda x: self.set_dirty(extended_note))
            tab.addTab(image_tab, ImageType.names[image_type])

    # ===========================================================================
    def stop_image(self, tab, index):
        tab.widget(index).stop()

    # ===========================================================================
    def set_dirty(self, extended_note):
        self.dirty[extended_note] = True

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
            
        current_word = self.extended_notes[self.current_note_index].main_word()

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
        for note in self.extended_notes:
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






