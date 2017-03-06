from fetch_image_tools.dictionary_tools import Language


class Note:
    def __init__(self, main_word, language, fields, values):
        self.main_word = main_word
        self.language = language
        self.fields = fields
        self.values = values
        self.model = ''


# ===========================================================================
def get_fields(note):
    return note.fields, note.values


# ===========================================================================
def get_main_word(note):
    return note.main_word


# ===========================================================================
def get_language(note):
    return note.language

# ===========================================================================
def update_note(note):
    return

# ===========================================================================
def set_image(note, image):
    print('image set for note: {}'.format(unicode(note.main_word)))
    return

# ===========================================================================
def set_audio(note, audio_file):
    print(u'audio set for note: {}'.format(unicode(note.main_word)))
    return

# ===========================================================================
def new_note():
    return Note('new word', Language.english, ['f1', 'f2', 'f3'], ['', '', ''])
