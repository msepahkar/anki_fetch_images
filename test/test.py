from PyQt4 import QtCore
from copy import deepcopy

a=['hi', 'bye']


class B(QtCore.QObject):
    def say(self, msg):
        print msg

class C(QtCore.QObject):
    signal = QtCore.SIGNAL('hi')

    def __init__(self):
        super(C, self).__init__()
        self.b = [B(), B()]
        for i, msg in enumerate(a):
            self.connect(self, C.signal, lambda x=i: self.b[x].say(a[x]))

    def go(self):
        self.emit(self.signal)


C().go()


