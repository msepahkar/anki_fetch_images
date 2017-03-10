# -*- coding: utf-8 -*-

import pygame
import sys
from PyQt4 import QtGui
from aqt import mw

from fetch_image_tools.general_tools import Language, ImageType
from fetch_image_tools.widget_tools import *
from fetch_image_tools.dictionary_tab import DictionaryTab, AudioListWidget
from fetch_image_tools.image_tab import ImageTab, ImageGraphicsView
from fetch_image_tools.main_word_tab import MainWordTab, Note
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
        dict_buttons = VerticalLayout([Button('Dict go', self.start_dictionaries), Button('Dict no', self.stop_dictionaries)])
        image_buttons = VerticalLayout([Button('Image go', self.start_images), Button('Image no', self.stop_images)])
        dict_and_image_buttons = VerticalLayout([Button('Dict Image go', self.start_dictionaries_and_images), Button('Dict Image no', self.stop_dictionaries_and_images)])
        update_buttons = VerticalLayout([Button('update', lambda:self.update_note(self.notes[self.current_note_index])), Button('update all', self.update_all_notes)])

        button_new = Button('new', self.new_note)
        button_stop_all = Button('stop all', self.stop_all)

        self.add_row_widgets(word_buttons, button_new, UiDesign.stretch, dict_buttons, image_buttons,
                             dict_and_image_buttons, button_stop_all, UiDesign.stretch, update_buttons)

        self.notes = []
        for note in notes:
            self.notes.append(Note(note))
            self.add_note(self.notes[-1])

        self.current_note_index = 0
        self.show_main_tab(self.notes[self.current_note_index])

    # ===========================================================================
    def add_note(self, note):
        self.dirty[note] = False

        # main tab
        self.main_tabs[note] = TabWidgetProgress(mother=self)
        self.connect(self.main_tabs[note], TabWidgetProgress.signal_update, self.update_progress)

        # main word
        self.main_tabs[note].tab_main_word = MainWordTab(note, parent=self.main_tabs[note])
        self.main_tabs[note].addTab(self.main_tabs[note].tab_main_word, 'word')

        # dictionaries
        self.main_tabs[note].tab_dictionaries = TabWidgetProgress(mother=self.main_tabs[note], closable=True, action=lambda: self.stop_dictionaries(note))
        self.main_tabs[note].addTab(self.main_tabs[note].tab_dictionaries, 'dictionaries')

        # main word dictionaries
        self.add_dictionary_tabs(note)

        # images
        self.main_tabs[note].tab_images = TabWidgetProgress(mother=self.main_tabs[note], closable=True, action=lambda: self.stop_images(note))
        self.main_tabs[note].addTab(self.main_tabs[note].tab_images, 'images')

        # main word images
        self.add_image_tabs(note)

        # main tab for this word
        self.main_layout.addWidget(self.main_tabs[note])
        self.main_tabs[note].hide()

    # ===========================================================================
    def show_main_tab(self, note):
        self.setWindowTitle(note.main_word())
        main_tab = self.main_tabs[note]
        main_tab.show()

    # # ===========================================================================
    # def start(self, note=None):
    #     if note is None:
    #         note = self.notes[self.current_note_index]
    #     main_tab = self.main_tabs[note]
    #     for dictionary_tab in main_tab.findChildren(DictionaryTab):
    #         if not dictionary_tab.browsing_started:
    #             dictionary_tab.start(get_main_word(note))
    #     for image_tab in main_tab.findChildren(ImageTab):
    #         if not image_tab.fetching_started:
    #             image_tab.start()
    #
    # # ===========================================================================
    # def stop(self, note=None):
    #     if note is None:
    #         note = self.notes[self.current_note_index]
    #     main_tab = self.main_tabs[note]
    #     for dictionary_tab in main_tab.findChildren(DictionaryTab):
    #         dictionary_tab.stop()
    #     for image_tab in main_tab.findChildren(ImageTab):
    #         image_tab.stop()
    #
    # ===========================================================================
    def start_dictionaries(self, note=None):
        if note is None:
            note = self.notes[self.current_note_index]
        main_tab = self.main_tabs[note]
        for dictionary_tab in main_tab.findChildren(DictionaryTab):
            if not dictionary_tab.browsing_started:
                dictionary_tab.start(get_main_word(note))

    # ===========================================================================
    def stop_dictionaries(self, note=None):
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
    def start_dictionaries_and_images(self, note=None):
        self.start_dictionaries(note)
        self.start_images(note)
    
    # ===========================================================================
    def stop_dictionaries_and_images(self, note=None):
        self.stop_dictionaries(note)
        self.stop_images(note)
    
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
    def update_note(self, note):
        # tab = self.main_tabs[note].tab_main_word
        # for i, field in enumerate(tab.fields):
        #     note[field] = tab.text_edits[i].toPlainText()
        note.flush()
        note.flush()
        self.dirty[note] = False

    # ===========================================================================
    def update_all_notes(self):
        result = YesNoCancelMessageBox('update all notes?', '').show()
        if not result:
            return False
        if result == YesNoCancelMessageBox.Yes:
            for note in self.notes:
                if self.dirty[note]:
                    self.update_note(note)
        return True

    # ===========================================================================
    def new_note(self):
        current_note = self.notes[self.current_note_index]
        self.hide_main_tab(current_note)

        model = mw.col.models.byName(current_note.model()['name'])
        model["did"] = current_note.model()['did']

        note = notes.Note(mw.col, model)
        note[model['flds'][0]['name']]='new'
        mw.col.addNote(note)

        self.notes.append(note)
        self.current_note_index = len(self.notes) - 1
        self.add_note(note)
        self.dirty[note] = True
        self.show_main_tab(note)

    # ===========================================================================
    def add_dictionary_tabs(self, note):
        # english dictionaries
        tab = TabWidgetProgress(mother=self.main_tabs[note].tab_dictionaries, closable=True, action=lambda index: self.stop_dictionary(tab, index))
        self.main_tabs[note].tab_dictionaries.addTab(tab, note.main_word())
        for dictionary in DictionaryTab.dictionaries[note.language()]:
            dictionary_tab = DictionaryTab(dictionary, mother=tab)
            self.connect(dictionary_tab.browser.audio_window, AudioListWidget.set_audio_signal, self.main_tabs[note].tab_main_word.set_audio)
            self.connect(dictionary_tab.browser.audio_window, AudioListWidget.set_audio_signal, lambda x: self.set_dirty(note))
            tab.addTab(dictionary_tab, dictionary_tab.name)

    # ===========================================================================
    def stop_dictionary(self, tab, index):
        tab.widget(index).stop()

    # ===========================================================================
    def add_image_tabs(self, note):
        tab = TabWidgetProgress(mother=self.main_tabs[note].tab_images, closable=True, action=lambda index: self.stop_image(tab, index))
        self.main_tabs[note].tab_images.addTab(tab, note.main_word())

        for image_type in sorted(ImageType.items, key=lambda x:x):
            image_tab = ImageTab(note, note.language(), image_type, mother=tab)
            self.connect(image_tab, ImageGraphicsView.set_image_signal, self.main_tabs[note].tab_main_word.set_image)
            self.connect(image_tab, ImageGraphicsView.set_image_signal, lambda x: self.set_dirty(note))
            tab.addTab(image_tab, ImageType.names[image_type])

    # ===========================================================================
    def stop_image(self, tab, index):
        tab.widget(index).stop()

    # ===========================================================================
    def set_dirty(self, note):
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






