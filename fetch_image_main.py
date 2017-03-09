# -*- coding: utf-8 -*-

import sys

from PyQt4 import QtGui
from fetch_image import MainDialog
from fetch_image_tools.dictionary_tab import Language
from anki import notes
from aqt import mw

import sys
import os
# sys.path.append('/home/mehdi/working_laptop/anki_fetch_images')
# sys.path.append(os.path.join(os.getcwd(), 'Anki/addons/sepahkar'))

n1 = notes.Note(mw.Model('hi'))
n1.set_fields(u'علی', Language.english, ['Word', 'Definition', 'Pronunciation'], ['ali', 'v2', 'v3'])
n2 = notes.Note(mw.Model('bye'))
n2.set_fields('reza', Language.english, ['Word', 'Definition', 'Pronunciation'], ['reza', 'v2', 'v3'])
# n3 = notes.Note('hasan', Language.english, ['Word', 'Definition', 'Pronunciation'], ['hasan', 'v2', 'v3'])
# n4 = Note('hosein', Language.english, ['f1', 'f2', 'f3'], ['hosein', 'v2', 'v3'])
# n5 = Note('roghaieh', Language.english, ['f1', 'f2', 'f3'], ['roghaieh', 'v2', 'v3'])

notes2 = [n1, n2]

app = QtGui.QApplication(sys.argv)

w = MainDialog(notes2)

w.show()

app.exec_()

