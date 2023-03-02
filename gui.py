#! /usr/bin/env python3

"""
Author: Nick Fan
Date: February 2023
"""

import sys
from PyQt6.QtWidgets import (
    QApplication,
    QGridLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QFrame,
    QGroupBox
)

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QIcon, QPalette

MIN_SIZE = 575
ICON_PATH = r"src\hydraLogo"

PRIMARY = QColor(23, 24, 23)
PRIMARY_H = "#171817"
WHITE = Qt.GlobalColor.white
#DETAILING = QColor(55,247,18) # green
#DETAILING = QColor(40,231,98) # darker green
#DETAILING = QColor(247,0,246) # purp
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
        font: bold 14px;
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
    ))

HEADER_STYLE = "color: white; font-family: consolas; font-size: 10px"

LAUNCH_MODE = ("LOADING", "FUEL OUT", "IGNITION", "TAKEOFF", "IN FLIGHT")
STATIC_F_MODE = ("LOADING", "FUEL OUT", "IGNITION")

class DarkCyanPalette(QPalette):
    """Dark and Cyan Palette."""

    def __init__(self) -> None:
        super().__init__()
        self.setColor(QPalette.ColorRole.Window, PRIMARY)
        self.setColor(QPalette.ColorRole.WindowText, DETAILING)
        self.setColor(QPalette.ColorRole.Text, WHITE)
        self.setColor(QPalette.ColorRole.Base, SECONDARY)
        #self.setColor(QPalette.ColorRole.ToolTipBase, WHITE)
        #self.setColor(QPalette.ColorRole.ToolTipText, WHITE)
        #self.setColor(QPalette.ColorRole.Dark, QColor(11, 12, 11))
        #self.setColor(QPalette.ColorRole.Shadow, Qt.GlobalColor.black)
        #self.setColor(QPalette.ColorRole.AlternateBase, PRIMARY)
        #self.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.black)
        #self.setColor(QPalette.ColorRole.ToolTipText, DETAILING)
        #self.setColor(QPalette.ColorRole.Text, WHITE)
        #self.setColor(QPalette.ColorRole.Button, DETAILING)
        #self.setColor(QPalette.ColorRole.ButtonText, WHITE)
        #self.setColor(QPalette.ColorRole.BrightText, DETAILING)
        #self.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
        #self.setColor(QPalette.ColorRole.HighlightedText, QColor(127,127,127))
                

class RocketDisplayWindow(QMainWindow):
    """Main Rocket Control Window."""

    def __init__(self) -> None:
        super().__init__()

        # control aspects
        self.mode = LAUNCH_MODE
        self.currentState = 0
        self.aborted = False
        self.buttons = {}
        self.dynamicLabels = {}

        # display
        self.setWindowTitle("LR Mission Control")
        self.setStyleSheet("background-color: #171817;")
        self.setMinimumSize(MIN_SIZE * 2, MIN_SIZE)
        self.setWindowIcon(QIcon(ICON_PATH))

        self.generalLayout = QVBoxLayout()
        centralWidget = QWidget()
        centralWidget.setLayout(self.generalLayout)
        self.setCentralWidget(centralWidget)

        self.pal = DarkCyanPalette()
        self.setPalette(self.pal)

        self._createFrame()
        self._linkButtons()


    def _createLabelBox(self, labelType: str | None=None, message: str | None = None, style: str | None = None) -> QLabel:
        label = QLabel()
        if labelType:
            pos = QGridLayout(label)
            self.dynamicLabels[labelType] = QLabel(message)
            if style:
                self.dynamicLabels[labelType].setStyleSheet(style)
            pos.addWidget(self.dynamicLabels[labelType])
        label.setFrameStyle(QFrame.Shape.Panel)
        label.setPalette(self.pal)
        label.setLineWidth(1)
        return label

    def _createLayoutBox(self, widgets: list) -> QLabel:
        label = QLabel()
        pos = QGridLayout(label)
        for widget in widgets:
            pos.addWidget(widget[0], widget[1], widget[2])
        label.setFrameStyle(QFrame.Shape.Panel)
        label.setPalette(self.pal)
        label.setLineWidth(1)
        return label
    
    def _createGrid(self, parent: QWidget | None = None):
        grid = QGridLayout(parent)
        grid.setHorizontalSpacing(1)
        grid.setVerticalSpacing(1)

        # top row
        grid.addWidget(self._createLabelBox("LeftTitle", "<h1> VEHICLE STATUS </h1>", HEADER_STYLE), 0, 0, 1, 2)
        grid.addWidget(self._createLabelBox("DiagTitle", "<h1> FLUIDS CONTROL DISPLAY </h1>", HEADER_STYLE), 0, 2, 1, 6)
        grid.addWidget(self._createLabelBox(), 0, 8, 1, 4)

        # right column
        grid.addWidget(self._createLabelBox(), 1, 0, 10, 2)
        grid.addWidget(self._createLabelBox("StateDisplay", f"<h1> STATE: {self.mode[self.currentState]}</h1>", HEADER_STYLE), 11, 0, 1, 2)
        grid.addWidget(self._createLayoutBox(self._createStatusButtons()), 12, 0, 1, 2)        

        # middle, left column
        grid.addWidget(self._createLabelBox(), 1, 2, 12, 6)
        grid.addWidget(self._createLabelBox(), 1, 8, 12, 4)

        # bottom row
        grid.addWidget(self._createLabelBox(), 13, 0, 1, 6)
        grid.addWidget(self._createLabelBox(), 13, 6, 1, 6)

        return grid

    def _createFrame(self):
        #frame = self._createLabel()
        #self._createGrid()
        #self.generalLayout.addWidget(frame)
        self.generalLayout.addLayout(self._createGrid())
    
    def _createStatusButtons(self):
        keys = ["ABORT", "PROCEED"]
        buttonDisplay = []
        for num, key in enumerate(keys):
            self.buttons[key] =  QPushButton(key)
            self.buttons[key].setStyleSheet(BUTTON_STYLE)
            buttonDisplay.append((self.buttons[key], 0, num))
        return buttonDisplay

    def _advanceState(self):
        """Advance current state."""
        # display
        if self.currentState < len(self.mode) - 1 and not self.aborted:
            self.currentState += 1
            self.dynamicLabels["StateDisplay"].setText(f"<h1> STATE: {self.mode[self.currentState]}")
            self.dynamicLabels["StateDisplay"].setStyleSheet(HEADER_STYLE)
    
    def _abortMission(self):
        """Abort mission."""
        self.dynamicLabels["StateDisplay"].setText("<h1> MISSION ABORTED </h1>")
        self.aborted = True

    def _linkButtons(self):
        """Link buttons to functionality."""
        self.buttons["PROCEED"].clicked.connect(self._advanceState)
        self.buttons["ABORT"].clicked.connect(self._abortMission)
        


class RocketControlWindow:

    def __init__(self, view: RocketDisplayWindow, model=None) -> None:
        self._respond = model
        self._view = view
    
    def _connectButtonSignals(self):
        #self._view.buttons["PROCEED"].clicked.connect(self._view._advanceState)
        pass

        
def main():
    """Rocket Control GUI"""
    app = QApplication([])
    rocketDisplay = RocketDisplayWindow()
    rocketDisplay.showMaximized()
    RocketControlWindow(view=rocketDisplay)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

