# -*- coding: utf-8 -*-

from PyQt4 import QtGui, QtCore
from general_tools import Result


# ===========================================================================
class Layout:
    # ===========================================================================
    def __init__(self, widget_list=None):
        if widget_list:
            self.add_widgets(widget_list)

    # ===========================================================================
    def add_widgets(self, widget_list):
        for widget in widget_list:
            if isinstance(widget, QtGui.QLayout):
                self.addLayout(widget)
            elif isinstance(widget, QtGui.QWidget):
                self.addWidget(widget)
            elif widget == UiDesign.stretch:
                self.addStretch()

    # ===========================================================================
    def add_widget_with_label(self, label_text, widget):
        layout = QtGui.QHBoxLayout()
        label = QtGui.QLabel(label_text)
        layout.addWidget(label)
        layout.addWidget(widget)
        self.addLayout(layout)
        return layout

    # ===========================================================================
    def add_row_widgets(self, *widgets):
        h_layout = QtGui.QHBoxLayout()
        for widget in widgets:
            if isinstance(widget, QtGui.QLayout):
                h_layout.addLayout(widget)
            elif widget == UiDesign.stretch:
                h_layout.addStretch()
            elif isinstance(widget, QtGui.QWidget):
                h_layout.addWidget(widget)
        self.addLayout(h_layout)


# ===========================================================================
class VerticalLayout(QtGui.QVBoxLayout, Layout):
    def __init__(self, widget_list=None, parent = None):
        QtGui.QVBoxLayout.__init__(self, parent)
        Layout.__init__(self, widget_list)


# ===========================================================================
class HorizontalLayout(QtGui.QHBoxLayout):
    def __init__(self, widget_list=None, parent = None):
        QtGui.QHBoxLayout.__init__(self, parent)
        Layout.__init__(widget_list)


# ===========================================================================
class HorizontalPlaceHoder(QtGui.QWidget):
    def __init__(self, widget_list, max_width=None, parent=None):
        super(HorizontalPlaceHoder, self).__init__(parent)
        
        self.setLayout(HorizontalLayout(widget_list))

        if max_width:
            self.setMaximumWidth(max_width)


# ===========================================================================
class VerticalPlaceHoder(QtGui.QWidget):
    def __init__(self, widget_list, max_height=None, parent=None):
        super(VerticalPlaceHoder, self).__init__(parent)

        self.setLayout(VerticalLayout(widget_list))

        if max_height:
            self.setMaximumHeight(max_height)


# ===========================================================================
class Button(QtGui.QPushButton):
    # ===========================================================================
    def __init__(self, text, action, size=None, style=None, enabled=True):
        super(Button, self).__init__(text)
        self.clicked.connect(lambda: action())
        self.setEnabled(enabled)
        if size is not None:
            self.setFixedSize(size)
        if style is not None:
            self.setStyleSheet(style)


# ===========================================================================
class Combo(QtGui.QComboBox):
    # ===========================================================================
    def __init__(self, items, action=None, parent=None):
        super(Combo, self).__init__(parent)
        for item in items:
            self.addItem(item)
        if action:
            self.currentIndexChanged.connect(action)


# ===========================================================================
class LineEdit(QtGui.QLineEdit):
    # ===========================================================================
    def __init__(self, text, action, parent=None):
        super(LineEdit, self).__init__(text, parent)
        self.textChanged.connect(action)


# ===========================================================================
class TextEdit(QtGui.QTextEdit):
    # ===========================================================================
    def __init__(self, value, action, parent=None):
        super(TextEdit, self).__init__(parent)
        self.document().setPlainText(value)
        self.textChanged.connect(action)
        width = self.document().size().width()
        height = self.document().size().height() + 10
        self.setMinimumSize(width, height)
        self.resize(width, height)


# ===========================================================================
class UiDesign:
    stretch = 'stretch'
    # ===========================================================================
    def __init__(self):
        self.main_layout = QtGui.QVBoxLayout()
        self.setLayout(self.main_layout)

    # ===========================================================================
    def add_row_widgets(self, *widgets):
        h_layout = QtGui.QHBoxLayout()
        for widget in widgets:
            if isinstance(widget, QtGui.QLayout):
                h_layout.addLayout(widget)
            elif widget == UiDesign.stretch:
                h_layout.addStretch()
            elif isinstance(widget, QtGui.QWidget):
                h_layout.addWidget(widget)
        self.main_layout.addLayout(h_layout)

    # ===========================================================================
    def add_widget(self, widget):
        self.main_layout.addWidget(widget)

    # ===========================================================================
    def add_widget_with_label(self, label_text, widget):
        layout = QtGui.QHBoxLayout()
        label = QtGui.QLabel(label_text)
        layout.addWidget(label)
        layout.addWidget(widget)
        self.main_layout.addLayout(layout)

    # ===========================================================================
    def add_line_edit(self, name, value=''):
        # create label and line edit
        label = QtGui.QLabel(name)
        line_edit = QtGui.QLineEdit(value)
        # add them to a horizontal layout
        self.add_row_widgets(label, line_edit)

    # ===========================================================================
    def add_text_edit(self, name, value='', compact=False):
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
    def add_scroll_area(self):
        # scroll area
        scroll_area = QtGui.QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area_widget_contents = QtGui.QWidget(parent=scroll_area)
        scroll_area_widget_contents.setGeometry(QtCore.QRect(0, 0, 50, 100))
        scroll_area.setWidget(scroll_area_widget_contents)

        self.main_layout.addWidget(scroll_area)
        # scrollable vertical layout
        return VerticalLayout(parent=scroll_area_widget_contents)


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
    def __init__(self, mother, closable=False, action=None, parent=None):
        super(TabWidget, self).__init__(parent)
        self.mother = mother
        self.setTabsClosable(closable)
        if action:
            self.tabCloseRequested.connect(action)
        self.label = ''

    # ===========================================================================
    def addTab(self, QWidget, label):
        super(TabWidget, self).addTab(QWidget, label)
        QWidget.label = label


# ===========================================================================
class TabWidgetProgress(TabWidget, Result):
    signal_update = QtCore.SIGNAL('TabWidgetProgress.update')

    # ===========================================================================
    def __init__(self, mother, closable=False, action=None, parent=None):
        TabWidget.__init__(self, mother, closable, action, parent)
        Result.__init__(self)

    # ===========================================================================
    def update_progress(self):
        self.reset_progress()

        total_started = 0
        total_failed = 0
        total_succeeded = 0
        total_in_progress = 0

        total_results = 0
        for i in range(self.count()):
            if isinstance(self.widget(i), Result):
                total_results += 1
                
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
        if total_started == total_results:
            self.started = True
        # all failed
        elif total_failed == total_results:
            self.failed = True
        # all succeeded
        elif total_succeeded == total_results:
            self.succeeded = True
        # all in progress
        elif total_in_progress == total_results:
            self.in_progress = True
        # at least one in progress
        elif total_in_progress > 0:
            self.in_progress = True
        # nothing in progress, but at least one started
        elif total_started > 0:
            self.started = True
        # nothing in progress and nothing started, but at least one succeeded
        elif total_succeeded > 0:
            self.succeeded = True

        mother = self.mother
        if not isinstance(mother, TabWidgetProgress):
            self.emit(TabWidgetProgress.signal_update)
            return
        index = mother.indexOf(self)
        tab_bar = mother.tabBar()

        # all started
        if self.started:
            tab_bar.setTabText(index, self.label)
            tab_bar.setTabTextColor(index, Result.started_color)
        # all failed
        elif self.failed:
            tab_bar.setTabText(index, self.label)
            tab_bar.setTabTextColor(index, Result.failed_color)
        # all succeeded
        elif self.succeeded:
            tab_bar.setTabText(index, self.label)
            tab_bar.setTabTextColor(index, Result.succeeded_color)
        # all in progress
        elif self.in_progress:
            tab_bar.setTabText(index, self.label + ' ' + str(self.progress) + '%')
            tab_bar.setTabTextColor(index, Result.in_progress_color)
        # at least one in progress
        elif self.in_progress:
            tab_bar.setTabText(index, self.label + ' ' + str(self.progress) + '%')
            # any failed or any started?
            if total_failed > 0 or total_started > 0:
                tab_bar.setTabTextColor(index, Result.weak_in_progress_color)
            # no fail and no started
            else:
                tab_bar.setTabTextColor(index, Result.in_progress_color)
        # nothing in progress, but at least one started
        elif self.started:
            tab_bar.setTabText(index, self.label)
            tab_bar.setTabTextColor(index, Result.started_color)
        # nothing in progress and nothing started, but at least one succeeded
        elif self.succeeded:
            # any failed?
            if total_failed > 0:
                tab_bar.setTabText(index, self.label)
                tab_bar.setTabTextColor(index, Result.weak_succeeded_color)
            # no fail
            else:
                tab_bar.setTabText(index, self.label)
                tab_bar.setTabTextColor(index, Result.succeeded_color)

        mother.update_progress()


