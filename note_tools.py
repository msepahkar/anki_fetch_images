###########################################################
def get_model(note):
    model = ''
    if note is not None:
        model = note.model()['name']
    return model


###########################################################
def get_fields(note):
    fields = ['hi','bye', 'how are you']
    values = ['ok', 'never mind', 'bye']
    return fields, values