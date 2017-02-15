# -*- coding: utf-8 -*-

from PyQt4 import QtGui
from general_tools import OperationResult


# ===========================================================================
class Widget(QtGui.QWidget):
    # ===========================================================================
    def __init__(self, mother, parent=None):
        super(Widget, self).__init__(parent)
        self.mother = mother


# ===========================================================================
class Dialog(QtGui.QDialog):
    # ===========================================================================
    def __init__(self, mother, parent=None):
        super(Dialog, self).__init__(parent)
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
class TabWidgetProgress(TabWidget, OperationResult):
    # ===========================================================================
    def __init__(self, mother, closable=False, parent=None):
        TabWidget.__init__(self, mother, closable, parent)
        OperationResult.__init__(self)

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
            tab_bar.setTabTextColor(index, OperationResult.started_color)
        # all failed
        elif total_failed == self.count():
            self.failed = True
            tab_bar.setTabText(index, self.label)
            tab_bar.setTabTextColor(index, OperationResult.failed_color)
        # all succeeded
        elif total_succeeded == self.count():
            self.succeeded = True
            tab_bar.setTabText(index, self.label)
            tab_bar.setTabTextColor(index, OperationResult.succeeded_color)
        # all in progress
        elif total_in_progress == self.count():
            self.in_progress = True
            tab_bar.setTabText(index, self.label + ' ' + str(self.progress) + '%')
            tab_bar.setTabTextColor(index, OperationResult.in_progress_color)
        # at least one in progress
        elif total_in_progress > 0:
            self.in_progress = True
            tab_bar.setTabText(index, self.label + ' ' + str(self.progress) + '%')
            # any failed or any started?
            if total_failed > 0 or total_started > 0:
                tab_bar.setTabTextColor(index, OperationResult.weak_in_progress_color)
            # no fail and no started
            else:
                tab_bar.setTabTextColor(index, OperationResult.in_progress_color)
        # nothing in progress, but at least one started
        elif total_started > 0:
            self.started = True
            tab_bar.setTabText(index, self.label)
            tab_bar.setTabTextColor(index, OperationResult.started_color)
        # nothing in progress and nothing started, but at least one succeeded
        elif total_succeeded > 0:
            self.succeeded = True
            # any failed?
            if total_failed > 0:
                tab_bar.setTabText(index, self.label)
                tab_bar.setTabTextColor(index, OperationResult.weak_succeeded_color)
            # no fail
            else:
                tab_bar.setTabText(index, self.label)
                tab_bar.setTabTextColor(index, OperationResult.succeeded_color)

        mother.update_progress()


