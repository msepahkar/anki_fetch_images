from PyQt4 import QtCore


class ProgressChord:
    ####################################################################
    def __init__(self, center_x, center_y, radius, progress=0):
        self.center_x = center_x
        self.center_y = center_y
        self.radius = radius
        rect_x = self.center_x - self.radius
        rect_y = self.center_y - self.radius
        rect_width = self.radius * 2
        rect_height = self.radius * 2
        self.rect = QtCore.QRect(rect_x, rect_y, rect_width, rect_height)
        self.progress = progress
        self.start_angle = 0
        self.span_angle = 0
        self.update_progress(self.progress)

    ####################################################################
    def update_progress(self, progress):
        self.progress = progress
        angle = 180 - self.progress * 180 / 100
        self.start_angle = angle * 16
        self.span_angle = (180 - angle) * 2 * 16
