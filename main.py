import sys

from PyQt4 import QtGui
from fetch_image import MainDialog
from fetch_image_tools.dictionary_tools import Language

app = QtGui.QApplication(sys.argv)

w = MainDialog('hello', Language.english, 'hi', '/home/mehdi')

w.show()

app.exec_()

