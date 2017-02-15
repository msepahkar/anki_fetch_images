# -*- coding: utf-8 -*-

from PyQt4 import QtGui
from general_tools import Result


# ===========================================================================
class Button(QtGui.QPushButton):
    # ===========================================================================
    def __init__(self, text, action, size=None, style=None, enabled=True):
        super(Button, self).__init__(text)
        self.clicked.connect(action)
        self.setEnabled(enabled)
        if size is not None:
            self.setFixedSize(size)
        if style is not None:
            self.setStyleSheet(style)


# ===========================================================================
class UiDesign:
    # ===========================================================================
    def __init__(self):
        self.main_layout = QtGui.QVBoxLayout()
        self.setLayout(self.main_layout)

    # ===========================================================================
    def add_row_widgets(self, *widgets):
        h_layout = QtGui.QHBoxLayout()
        for widget in widgets:
            h_layout.addWidget(widget)
        self.main_layout.addLayout(h_layout)

    # ===========================================================================
    def add_widget(self, widget):
        self.main_layout.addWidget(widget)

    # ===========================================================================
    def add_line_edit(self, name):
        # create label and line edit
        label = QtGui.QLabel(name)
        line_edit = QtGui.QLineEdit()
        # add them to a horizontal layout
        self.add_row_widgets(label, line_edit)

    # ===========================================================================
    def add_text_edit(self, name, value=''):
        # create label and line edit
        label = QtGui.QLabel(name)
        text_edit = QtGui.QTextEdit(value)
        # add them to a horizontal layout
        self.add_row_widgets(label, text_edit)

    # ===========================================================================
    def add_combo(self, name, items):
        # create label and combo
        label = QtGui.QLabel(name)
        combo = QtGui.QComboBox()
        for item in items:
            combo.addItem(item)
        # add them to the horizontal layout
        self.add_row_widgets(label, combo)


# ===========================================================================
class YesNoMessageBox(QtGui.QMessageBox):
    # ===========================================================================
    def __init__(self, message1, message2):
        super(YesNoMessageBox, self).__init__()
        self.setText(message1)
        self.setInformativeText(message2)
        self.setStandardButtons(YesNoMessageBox.Yes | YesNoMessageBox.No)
        self.setDefaultButton(YesNoMessageBox.No)

    # ===========================================================================
    def show(self):
        if self.exec_() == YesNoMessageBox.Yes:
            return True
        return False


# ===========================================================================
class YesNoCancelMessageBox(QtGui.QMessageBox):
    # ===========================================================================
    def __init__(self, message1, message2):
        super(YesNoCancelMessageBox, self).__init__()
        self.setText(message1)
        self.setInformativeText(message2)
        self.setStandardButtons(YesNoMessageBox.Yes | YesNoMessageBox.No | YesNoCancelMessageBox.Cancel)
        self.setDefaultButton(YesNoMessageBox.Cancel)

    # ===========================================================================
    def show(self):
        result = self.exec_()
        if result == YesNoCancelMessageBox.Cancel:
            return False
        return result


# ===========================================================================
class YesAllNoMessageBox(QtGui.QMessageBox):
    # ===========================================================================
    def __init__(self, message1, message2):
        super(YesAllNoMessageBox, self).__init__()
        self.setText(message1)
        self.setInformativeText(message2)
        self.setStandardButtons(YesNoMessageBox.Yes | YesAllNoMessageBox.YesAll | YesNoMessageBox.No)
        self.setDefaultButton(YesNoMessageBox.No)

    # ===========================================================================
    def show(self):
        result = self.exec_()
        if result == YesAllNoMessageBox.No:
            return False
        return result


# ===========================================================================
class Widget(QtGui.QWidget, UiDesign):
    # ===========================================================================
    def __init__(self, mother, parent=None):
        QtGui.QWidget.__init__(self)
        UiDesign.__init__(self)
        self.mother = mother


# ===========================================================================
class Dialog(QtGui.QDialog, UiDesign):
    # ===========================================================================
    def __init__(self, mother, parent=None):
        QtGui.QDialog.__init__(self)
        UiDesign.__init__(self)
        self.mother = mother


# ===========================================================================
class TabWidget(QtGui.QTabWidget):
    # ===========================================================================
    def __init__(self, mother, closable=False, parent=None):
        super(TabWidget, self).__init__(parent)
        self.mother = mother
        self.tabBar().setTabsClosable(closable)
        self.label = ''

    # ===========================================================================
    def addTab(self, QWidget, label):
        super(TabWidget, self).addTab(QWidget, label)
        QWidget.label = label


# ===========================================================================
class TabWidgetProgress(TabWidget, Result):
    # ===========================================================================
    def __init__(self, mother, closable=False, parent=None):
        TabWidget.__init__(self, mother, closable, parent)
        Result.__init__(self)

    # ===========================================================================
    def update_progress(self):
        mother = self.mother
        if type(mother) is not TabWidgetProgress:
            return
        index = mother.indexOf(self)
        tab_bar = mother.tabBar()

        self.failed = False
        self.succeeded = False
        self.in_progress = False
        self.progress = 0

        total_started = 0
        total_failed = 0
        total_succeeded = 0
        total_in_progress = 0

        for i in range(self.count()):
            if self.widget(i).started:
                total_started += 1
            if self.widget(i).failed:
                total_failed += 1
            if self.widget(i).succeeded:
                total_succeeded += 1
                self.progress += 100
            if self.widget(i).in_progress:
                total_in_progress += 1
                self.progress += self.widget(i).progress

        if total_in_progress + total_succeeded > 0:
            self.progress /= (total_in_progress + total_succeeded)

        # all started
        if total_started == self.count():
            self.started = True
            tab_bar.setTabText(index, self.label)
            tab_bar.setTabTextColor(index, Result.started_color)
        # all failed
        elif total_failed == self.count():
            self.failed = True
            tab_bar.setTabText(index, self.label)
            tab_bar.setTabTextColor(index, Result.failed_color)
        # all succeeded
        elif total_succeeded == self.count():
            self.succeeded = True
            tab_bar.setTabText(index, self.label)
            tab_bar.setTabTextColor(index, Result.succeeded_color)
        # all in progress
        elif total_in_progress == self.count():
            self.in_progress = True
            tab_bar.setTabText(index, self.label + ' ' + str(self.progress) + '%')
            tab_bar.setTabTextColor(index, Result.in_progress_color)
        # at least one in progress
        elif total_in_progress > 0:
            self.in_progress = True
            tab_bar.setTabText(index, self.label + ' ' + str(self.progress) + '%')
            # any failed or any started?
            if total_failed > 0 or total_started > 0:
                tab_bar.setTabTextColor(index, Result.weak_in_progress_color)
            # no fail and no started
            else:
                tab_bar.setTabTextColor(index, Result.in_progress_color)
        # nothing in progress, but at least one started
        elif total_started > 0:
            self.started = True
            tab_bar.setTabText(index, self.label)
            tab_bar.setTabTextColor(index, Result.started_color)
        # nothing in progress and nothing started, but at least one succeeded
        elif total_succeeded > 0:
            self.succeeded = True
            # any failed?
            if total_failed > 0:
                tab_bar.setTabText(index, self.label)
                tab_bar.setTabTextColor(index, Result.weak_succeeded_color)
            # no fail
            else:
                tab_bar.setTabText(index, self.label)
                tab_bar.setTabTextColor(index, Result.succeeded_color)

        mother.update_progress()


