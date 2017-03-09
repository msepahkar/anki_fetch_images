from aqt import mw

class Note:
    def __init__(self, col, model=None, id=None):
        self.id = id
        self._model = mw.Model('English')
        self.col = col
        self.tags = []
        self.did = None

    def set_fields(self, main_word, language, fields, values):
        self.main_word = main_word
        self.language = language
        self.fields = fields
        self.values = values

    def __setitem__(self, key, value):
        pass

    def __getitem__(self, item):
        return '??'

    def flush(self):
        pass

    def addTag(self, tag):
        self.tags.append(tag)

    def model(self):
        return self._model

