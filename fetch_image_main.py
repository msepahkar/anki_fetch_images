# -*- coding: utf-8 -*-

import sys

from PyQt4 import QtGui
from fetch_image import MainDialog
from fetch_image_tools.dictionary_tools import Language
from fetch_image_note_tools import Note

n1 = Note(u'علی', Language.english, ['f1', 'f2', 'f3'], ['ali', 'v2', 'v3'])
n2 = Note('reza', Language.english, ['f1', 'f2', 'f3'], ['reza', 'v2', 'v3'])
n3 = Note('hasan', Language.english, ['f1', 'f2', 'f3'], ['hasan', 'v2', 'v3'])
# n4 = Note('hosein', Language.english, ['f1', 'f2', 'f3'], ['hosein', 'v2', 'v3'])
# n5 = Note('roghaieh', Language.english, ['f1', 'f2', 'f3'], ['roghaieh', 'v2', 'v3'])

notes = [n1, n2, n3]#, n4, n5]

app = QtGui.QApplication(sys.argv)

w = MainDialog(notes)

w.show()

app.exec_()

