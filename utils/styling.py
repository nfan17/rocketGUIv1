"""
Author: Nick Fan
Date: 3/2023
Description: Styling for PyQt6 gui.
"""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPalette


# CONSTANTS --------------------------------------------------------------------|
PRIMARY = QColor(23, 24, 23)
PRIMARY_H = "#171817"
WHITE = Qt.GlobalColor.white
DETAILING = QColor(0, 168, 145) # darker blue
DETAILING_H = "#00A891"
#DETAILING = QColor(48, 170, 170) # lighter blue
SECONDARY = WHITE

BUTTON_STYLE = (
    """
    QPushButton {
        font-family: consolas;
        background-color: %s;
        border-style: outset;
        border-width: 1px;
        border-radius: 2px;
        border-color: %s;
        font: bold 16px;
    }
    QPushButton:hover {
        color: white;
        background-color: %s;
    }
    QPushButton:pressed {
        color: white;
        background-color: %s;
    }""" % (
        DETAILING_H,
        DETAILING_H,
        DETAILING_H,
        PRIMARY_H
    )
)

HEADER_STYLE = "color: white; font-family: consolas; font-size: 9px; "
STAGE_FONT_WHITE = "color: white; font-family: consolas; font-size: 13px; "
STAGE_FONT_BLUE = "color: #00A891; font-family: consolas; font-size: 13px; "

DATE_TIME_FORMAT = "MM/dd/yyyy | hh:mm:ss:zzz -> "

# PALETTE ----------------------------------------------------------------------|
class DarkCyanPalette(QPalette):
    """Dark and Cyan Palette."""

    def __init__(self) -> None:
        super().__init__()
        self.setColor(QPalette.ColorRole.Window, PRIMARY)
        self.setColor(QPalette.ColorRole.WindowText, DETAILING)
        self.setColor(QPalette.ColorRole.Text, WHITE)
        self.setColor(QPalette.ColorRole.Base, SECONDARY)
