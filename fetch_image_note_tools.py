from fetch_image_tools.dictionary_tab import Language
from anki import notes


# ===========================================================================
def get_main_word(note):
    return note.main_word


# ===========================================================================
def get_language(note):
    return note.language


# ===========================================================================
def get_image_field(note):
    return 'Definition'


# ===========================================================================
def get_sound_field(note):
    return 'Pronunciation'


