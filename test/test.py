# ===========================================================================
def enum(**enums):
    items = [value for key, value in enums.iteritems()]
    enums['names'] = dict((value, key) for key, value in enums.iteritems())
    enums['items'] = items
    return type('Enum', (), enums)


# ===========================================================================
Language = enum(english=1, german=2)

l = Language.english
print(Language)