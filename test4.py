from PyQt4 import QtCore, QtGui
import sys
from PyQt4.phonon import Phonon
import time

app = QtGui.QApplication(sys.argv)
output = Phonon.AudioOutput(Phonon.MusicCategory)
m_media = Phonon.MediaObject()
Phonon.createPath(m_media, output)
f_name = '/home/mehdi/temp/test.mp3'
m_media.setCurrentSource(Phonon.MediaSource(f_name))
m_media.play()
print 'played'

# from PyQt4 import QtGui
#
# print QtGui.QSound.isAvailable()
# f_name = '/home/mehdi/temp/test.mp3'
time.sleep(1)
# player = QtGui.QSound(f_name)
# QtGui.QSound.play(f_name)
