import copy

#####################################################################
def enum(**enums):
    items = [value for key, value in enums.iteritems()]
    enums['names'] = dict((value, key) for key, value in enums.iteritems())
    enums['items'] = items
    return type('Enum', (), enums)

e=enum(hi=0, bye=1)

print e.items
print e.names
for item in e.items:
    print e.names[item]

print e.hi
print e.bye

