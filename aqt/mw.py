class Media:
    def dir(self):
        return '/home/mehdi/temp'

class Field:
    def __init__(self, name):
        self.name = name
    def __getitem__(self, item):
        if item == 'name':
            return self.name
    def __setitem__(self, key, value):
        pass

class Model:
    def __init__(self, name, fields):
        self.name = name
        self.fields = fields
        self.did = 0
    def __getitem__(self, item):
        if item == 'name':
            return 'English'
        if item == 'flds':
            return self.fields
    def __setitem__(self, key, value):
        if key == 'name':
            self.name = value
        if key == "did":
            self.did = value


class Models:
    def __init__(self):
        self.models = []
    def add_model(self, model):
        self.models.append(model)
    def byName(self, name):
        for model in self.models:
            if model['name'] == name:
                return model
        return None

    def allNames(self):
        names = []
        for model in self.models:
            names.append(model['name'])
        return names

class Decks:
    def __init__(self):
        self.decks = []
    def id(self, name):
        return 0
    def add_deck(self, deck):
        self.decks.append(deck)
    def name(self, id):
        return 'English deck'
    def allNames(self):
        return['English deck', 'German deck']

class Col:
    def __init__(self, models, decks):
        self.media = Media()
        self.models = models
        self.decks = decks
    def addNote(self, note):
        pass
    def remNotes(self, ids):
        pass

english_model = Model('English', [Field('Word'), Field('Definition'), Field('Pronunciation')])
german_model = Model('German', [Field('Word'), Field('Definition'), Field('Pronunciation')])
models = Models()
models.add_model(english_model)
models.add_model(german_model)
col = Col(models, Decks())


# model = col.models.byName(model_name)
#
# # create the note and add it to the deck
# did = col.decks.id(deck_name)
# model["did"] = did
# note = notes.Note(col, model)
# note["Word"] = 'test'
# note.did = did
# col.addNote(note)
#
