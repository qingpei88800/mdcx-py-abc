from PyQt5.QtCore import QEvent
from PyQt5.QtWidgets import QComboBox, QSpinBox, QSlider


class CustomQComboBox(QComboBox):

    def wheelEvent(self, e):
        if e.type() == QEvent.Wheel:
            e.ignore()


class CustomQSpinBox(QSpinBox):

    def wheelEvent(self, e):
        if e.type() == QEvent.Wheel:
            e.ignore()


class CustomQSlider(QSlider):

    def wheelEvent(self, e):
        if e.type() == QEvent.Wheel:
            e.ignore()
