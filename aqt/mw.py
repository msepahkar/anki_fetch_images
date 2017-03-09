class Media:
    def dir(self):
        return '/home/mehdi/temp'

class Model:
    def __init__(self, name):
        self.name = name
    def __getitem__(self, item):
        return self.name
    def __setitem__(self, key, value):
        self.name = value


class Models:
    def byName(self, name):
        return Model(name)
    def allNames(self):
        return ['English', 'German']

class Decks:
    def id(self, name):
        return 0
    def name(self, id):
        return 'English deck'
    def allNames(self):
        return['English deck', 'German deck']

class Col:
    def __init__(self):
        self.media = Media()
        self.models = Models()
        self.decks = Decks()
    def addNote(self, note):
        pass
    def remNotes(self, ids):
        pass

col = Col()


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
