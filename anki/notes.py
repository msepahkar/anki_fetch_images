from aqt import mw
from fetch_image_tools.dictionary_tab import Language

class Note:
    def __init__(self, col, model, id=None):
        self.id = id
        self._model = model
        self.col = col
        self.tags = []
        self.values = dict()

    def set_values(self, values):
        for i, field in enumerate(self._model['flds']):
            self.values[field['name']] = values[i]

    def __setitem__(self, key, value):
        self.values[key] = value

    def __getitem__(self, item):
        return self.values[item]

    def flush(self):
        pass

    def addTag(self, tag):
        self.tags.append(tag)

    def model(self):
        return self._model

