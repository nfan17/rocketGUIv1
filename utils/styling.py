"""
Author: Nick Fan
Date: 3/2023
Description: Styling for PyQt6 gui.
"""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPalette


# CONSTANTS --------------------------------------------------------------------|
LIGHT = False
if LIGHT:
    PRIMARY = QColor(200, 200, 200)
    PRIMARY_H = "#c8c8c8"
    WHITE = Qt.GlobalColor.white
    DETAILING = QColor(0, 0, 0)
    DETAILING_H = "#000000"
    SECONDARY = Qt.GlobalColor.black
    TEXT = "black"
    BUTTON_OFF = "gray"
else:
    PRIMARY = QColor(23, 24, 23)
    PRIMARY_H = "#171817"
    WHITE = Qt.GlobalColor.white
    DETAILING = QColor(0, 168, 145) # darker blue
    DETAILING_H = "#00A891"
    #DETAILING = QColor(48, 170, 170) # lighter blue
    SECONDARY = WHITE
    TEXT = "white"
    BUTTON_OFF = "white"

VALVE_ON = "green"
BOLD = "font-weight: bold; "

GREEN = "color: green; "
YELLOW = "color: yellow; "
RED = "color: red; "

COLOR_CSS = f"background: {PRIMARY_H}; color: {DETAILING_H}; "
FONT_CSS = "font-family: consolas; "

FONT_SIZE = lambda size: f"font-size: {size}px; "

PRESS_GREEN = f"{GREEN} {FONT_CSS}; {BOLD} {FONT_SIZE(13)}"
PRESS_YELLOW = f"{YELLOW} {FONT_CSS}; {BOLD} {FONT_SIZE(13)}"
PRESS_RED = f"{RED} {FONT_CSS}; {BOLD} {FONT_SIZE(13)}"
SV_CSS = f"color: {TEXT}; {FONT_CSS} {FONT_SIZE(12)}"

LINE_HEIGHT = 25

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
        color: %s;
    }
    QPushButton:hover {
        color: white;
        background-color: %s;
    }
    QPushButton:pressed {
        color: white;
        background-color: %s;
    }
    QPushButton:disabled{
        color: %s;
    }
    """ % (
        DETAILING_H,
        DETAILING_H,
        PRIMARY_H,
        DETAILING_H,
        PRIMARY_H,
        BUTTON_OFF,
    )
)

HEADER_STYLE = f"color: {TEXT}; font-family: consolas; {FONT_SIZE(9)}"
STAGE_FONT_WHITE = f"color: {TEXT}; font-family: consolas; {FONT_SIZE(20)} {BOLD}"
STAGE_FONT_BLUE = f"color: {DETAILING_H}; font-family: consolas; {FONT_SIZE(20)} {BOLD}"

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
