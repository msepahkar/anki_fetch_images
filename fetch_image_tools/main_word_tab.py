# -*- coding: utf-8 -*-

from PyQt4 import QtGui, QtCore
import threading
import magic
from PIL.ImageQt import ImageQt
from shutil import *
from general_tools import *
from thread_tools import ThreadFetchImage, ThreadFetchImageUrls
from widget_tools import *
from fetch_image_note_tools import *
from aqt import mw


# ===========================================================================
class MainWordTab(Widget):
    word_changed_signal = QtCore.SIGNAL('MainWordTab.word_changed')

    # ===========================================================================
    def __init__(self, note, parent=None):
        super(MainWordTab, self).__init__(parent)

        self.note = note

        self.models_combo = Combo(mw.col.models.allNames(), parent=self)
        self.models_combo.setCurrentIndex(mw.col.models.allNames().index(self.note.model()['name']))
        self.models_combo.currentIndexChanged.connect(self.model_changed)

        self.decks_combo = Combo(mw.col.decks.allNames(), parent=self)
        self.decks_combo.setCurrentIndex(mw.col.decks.allNames().index(mw.col.decks.name(self.note.model()['did'])))
        self.decks_combo.currentIndexChanged.connect(self.deck_changed)

        self.scroll_area = self.add_scroll_area()
        self.scroll_area.add_row_widgets(self.models_combo, self.decks_combo)

        # fields
        self.text_edits = dict()
        self.text_edits_with_labels = dict()
        self.add_text_edits()

        # tags
        self.tags_line_edit = LineEdit(' '.join(self.note.tags), self.tags_changed)
        self.scroll_area.addWidget(self.tags_line_edit)

    # ===========================================================================
    def model_changed(self, model_name):
        deck_id = self.note.model()["did"]
        model = mw.col.models.byName(model_name)

        # create the note and add it to the deck
        previous_model = self.note.model()
        model["did"] = deck_id
        note = notes.Note(mw.col, model)
        note.did = deck_id
        mw.col.addNote(note)

        # initialize current values
        for i in range(min(len(previous_model['flds']), len(model['flds']))):
            note[model['flds'][i]] = self.note[previous_model['flds'][i]]

        # remove previous note
        mw.col.remNotes([self.note.id])

        self.scroll_area.removeWidget(self.tags_line_edit)
        for field in self.text_edits_with_labels:
            self.scroll_area.removeItem(self.text_edits_with_labels[field])
        self.text_edits_with_labels.clear()
        self.text_edits.clear()
        self.add_text_edits()
        self.scroll_area.addWidget(self.tags_line_edit)

    # ===========================================================================
    def deck_changed(self, deck_name):
        deck_id = mw.col.decks.id(deck_name)
        self.note.did = deck_id

    # ===========================================================================
    def tags_changed(self):
        self.note.tags = self.tags_line_edit.text().split(' ')

    # ===========================================================================
    def text_edit_changed(self, field_name):
        self.note[field_name] = self.text_edits[field_name].document().toPlainText()

    # ===========================================================================
    def add_text_edits(self):

        fields = []
        values = []
        for field in self.note.model()['flds']:
            fname = field['name']
            fields.append(fname)
            values.append(self.note[fname])

        for i, field in enumerate(fields):
            self.text_edits[field] = TextEdit(values[i], lambda:self.text_edit_changed(field), parent=self)
            self.text_edits_with_labels[field] = self.scroll_area.add_widget_with_label(field, self.text_edits[field])
        self.scroll_area.addStretch()

    # ===========================================================================
    def set_image(self, image):
        media_dir = self.note.col.media.dir()

        name = get_main_word(self.note)
        ext = 'jpg'
        full_file_name = find_unique_file_name(media_dir, name, ext)
        image.save(full_file_name)
        image_field = get_image_field(self.note)
        current_text = self.text_edits[image_field].document().toPlainText()
        # note[image_field] = re.sub(note[image_field], '<img.*/>', '')
        self.text_edits[image_field].document().setPlainText(current_text + u'<img src="{}" />'.format(os.path.basename(full_file_name)))

    # ===========================================================================
    def set_audio(self, audio_file):
        media_dir = self.note.col.media.dir()

        sound_field = get_sound_field(self.note)
        name = get_main_word(self.note)
        m = magic.open(magic.MAGIC_MIME)
        m.load()
        ext = ''
        mime = m.file(audio_file)
        if '/mpeg' in mime:
            ext = 'mp3'
        elif '/x-wav' in mime:
            ext = 'wav'
        full_file_name = find_unique_file_name(media_dir, name, ext)
        copyfile(audio_file, full_file_name)
        self.text_edits[sound_field].document().setPlainText(u'[sound:{}]'.format(os.path.basename(full_file_name)))

