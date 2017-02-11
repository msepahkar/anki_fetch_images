from PyQt4 import QtCore

#####################################################################
def enum(**enums):
    items = [value for key, value in enums.iteritems()]
    enums['names'] = dict((value, key) for key, value in enums.iteritems())
    enums['items'] = items
    return type('Enum', (), enums)


#####################################################################
Language = enum(english=1, german=2)

#####################################################################
ImageType = enum(normal=1, clipart=2, line_drawing=3)


#####################################################################
class OperationResult:
    started_color = QtCore.Qt.yellow
    weak_in_progress_color = QtCore.Qt.yellow
    in_progress_color = QtCore.Qt.darkYellow
    weak_succeeded_color = QtCore.Qt.green
    succeeded_color = QtCore.Qt.darkGreen
    failed_color = QtCore.Qt.darkRed
    #####################################################################
    def __init__(self):
        self._started = False
        self._in_progress = False
        self._succeeded = False
        self._failed = False
        self._progress = 0

    #####################################################################
    @property
    def started(self):
        return self._started

    #####################################################################
    @started.setter
    def started(self, value):
        if value:
            self._started = True
            self._in_progress = False
            self._succeeded = False
            self._failed = False
        else:
            self._started = False

    #####################################################################
    @property
    def in_progress(self):
        return self._in_progress

    #####################################################################
    @in_progress.setter
    def in_progress(self, value):
        if value:
            self._started = False
            self._in_progress = True
            self._succeeded = False
            self._failed = False
        else:
            self._in_progress = False

    #####################################################################
    @property
    def progress(self):
        return self._progress

    #####################################################################
    @progress.setter
    def progress(self, value):
        self._progress = value
        if value == 100:
            self.succeeded = True

    #####################################################################
    @property
    def succeeded(self):
        return self._succeeded

    #####################################################################
    @succeeded.setter
    def succeeded(self, value):
        if value:
            self._started = False
            self._in_progress = False
            self._succeeded = True
            self._failed = False
        else:
            self._succeeded = False

    #####################################################################
    @property
    def failed(self):
        return self._failed

    #####################################################################
    @failed.setter
    def failed(self, value):
        if value:
            self._started = False
            self._in_progress = False
            self._succeeded = False
            self._failed = True
        else:
            self._failed = False

