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

from PyQt6.QtCore import Qt, QTimer, QDateTime
from PyQt6.QtGui import QColor, QIcon, QPalette

MIN_SIZE = 600
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
    )
)

HEADER_STYLE = "color: white; font-family: consolas; font-size: 9px"
LAUNCH_STATES = ("IDLE", "HIGH PRESSURE", "TANK HIGH PRESSURE", "FIRE")
LEAK_ACCEPT_RATE = "1 PSI / Min"

#STATIC_F_MODE = ("IDLE", "HIGH PRESSURE", "TANK HIGH PRESSURE", "FIRE")

# Dynamic Labels Map
DIAGRAM_LABEL = "D_Label"
STATUS_LABEL = "Status"
CURR_STATE = "StateDisplay"

# Button Map
PROCEED = "PROCEED"
IGNITION_FAILURE = "IGNITION FAIL"
OVERPRESSURE = "OVERPRESSURE"

class State:
    """State object to manage state displays."""

    class Task:
        """Task object to manage task data."""

        def __init__(self, name: str, description: list[str]) -> None:
            self.taskName = name
            self.notes = description
    
    def __init__(self, name: str, tasks: list[tuple]) -> None:
        self.stateName = name
        self.tasklist = [self.Task(taskInfo[0], taskInfo[1]) for taskInfo in tasks if len(tasks) > 0]


class Clock:
    """QLabel clock class to display self-updating label with time/date."""

    def __init__(self, style: str) -> None:
        self.dateTime = QLabel()
        self.dateTime.setStyleSheet(style)
        self.timer = QTimer()
        self.updateTime()
        self.timer.timeout.connect(self.updateTime)
        self.timer.start(1000)
    
    def updateTime(self):
        """Updates the time and date display."""
        currentTime = QDateTime.currentDateTime().toString("hh:mm:ss\nMM/dd/yyyy")
        self.dateTime.setText(currentTime)

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
        """Constructs new Rocket Display Window."""
        super().__init__()

        # control aspects
        self.mode = LAUNCH_STATES
        self.currentState = 0
        self.aborted = False
        self.buttons = {}
        self.dynamicLabels = {}

        # display
        self.setWindowTitle("LR Mission Control")
        #self.setStyleSheet(f"background-color: {PRIMARY_H};")
        self.setMinimumSize(MIN_SIZE * 2, MIN_SIZE)
        self.setWindowIcon(QIcon(ICON_PATH))

        self.pal = DarkCyanPalette()
        self.setPalette(self.pal)

        self.clock = Clock(HEADER_STYLE)

        self.generalLayout = self._createMainGrid()

        centralWidget = QWidget()
        centralWidget.setLayout(self.generalLayout)
        self.setCentralWidget(centralWidget)

        self._linkButtons()


    def _createLabelBox(self, message: str | None = None, labelType: str | None=None, style: str | None = None) -> QLabel:
        """Creates frame box with optional label message.
        
        Args:
            labelType(str): labelType to map label to dict of labels.
            message(str): the label message itself.
            style(str): style sheet configurations.
        
        Returns:
            QLabel: the generated frame box with optional message.
        """
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
        """Creates a frame box with layout of widgets.

        Args:
            widgets(list): list of widgets to place in layout,
            plus grid location.
        
        Returns:
            QLabel: the generated frame box with given widgets.

        Argument format example:
        [(button, x, y), (button, x, y), (someWidget, x, y)]
        """
        label = QLabel()
        pos = QGridLayout(label)
        for widget in widgets:
            pos.addWidget(widget[0], widget[1], widget[2])
        label.setFrameStyle(QFrame.Shape.Panel)
        label.setPalette(self.pal)
        label.setLineWidth(1)
        return label
    
    def _createMainGrid(self) -> QGridLayout:
        """Creates primary display grid with frame boxes and components.

        Returns:
            QGridLayout: the primary frame layout
        """
        grid = QGridLayout()
        grid.setHorizontalSpacing(1)
        grid.setVerticalSpacing(1)

        # top row
        grid.addWidget(self._createLabelBox("<h1> VEHICLE STATUS </h1>", STATUS_LABEL, HEADER_STYLE), 0, 0, 1, 3)
        grid.addWidget(self._createLabelBox("<h1> FLUIDS CONTROL DISPLAY </h1>", DIAGRAM_LABEL, HEADER_STYLE), 0, 3, 1, 6)
        grid.addWidget(self._createLabelBox(), 0, 9, 1, 3)

        # left column
        grid.addWidget(self._createLabelBox(f"<h1>STATE: {self.mode[self.currentState]}</h1>", CURR_STATE, HEADER_STYLE), 1, 0, 1, 3)
        grid.addWidget(self._createLabelBox("Hello", "helloTest", HEADER_STYLE), 2, 0, 8, 3)
        grid.addWidget(self._createLayoutBox(self._createButtonSets([PROCEED])), 10, 0, 1, 3)
        grid.addWidget(self._createLayoutBox([(self.clock.dateTime, 0, 0)]), 11, 0, 2, 3)

        # middle, right column
        grid.addWidget(self._createLabelBox(), 1, 3, 12, 6)
        grid.addWidget(self._createLabelBox(), 1, 9, 12, 3)

        # bottom row
        #grid.addWidget(self._createLabelBox(), 13, 0, 3, 6)
        #grid.addWidget(self._createLabelBox(), 13, 6, 3, 5)
        #grid.addWidget(self._createLayoutBox([(self.clock.dateTime, 0, 0)]), 13, 11, 3, 1)

        return grid

    #def _createTaskList(self)
    
    def _createButtonSets(self, keys: list[str]) -> list[tuple]:
        """Generate status control buttons.
        
        Args:
            keys(list[str]): list of button names (for dictionary hashing)

        Returns:
            list[tuple]: list of tuples with buttons and x, y grid locations.

        """
        buttonDisplay = []
        for num, key in enumerate(keys):
            self.buttons[key] = QPushButton(key)
            self.buttons[key].setFocusPolicy(Qt.FocusPolicy.NoFocus)
            self.buttons[key].setStyleSheet(BUTTON_STYLE)
            buttonDisplay.append((self.buttons[key], 0, num))
        return buttonDisplay

    def _advanceState(self) -> None:
        """Advance current state."""
        # display
        if self.currentState <= len(self.mode) - 2 and not self.aborted:
            self.currentState += 1
            self.dynamicLabels[CURR_STATE].setText(f"<h1>STATE: {self.mode[self.currentState]}")
            self.dynamicLabels[CURR_STATE].setStyleSheet(HEADER_STYLE)
            
        elif self.currentState == len(self.mode) - 1 and not self.aborted:
            self._countDown()
            # reference for removing and adding widgets
            remove = self.generalLayout.itemAtPosition(2, 0)
            widget = remove.widget()
            self.generalLayout.removeWidget(widget)
            self.generalLayout.addWidget(self._createLabelBox("whoooo", "helloTest", HEADER_STYLE), 2, 0, 8, 3)
    
    def _abortMission(self) -> None:
        """Abort mission."""
        self.dynamicLabels[CURR_STATE].setText("<h1> MISSION ABORTED </h1>")
        self.aborted = True
        try:
            self.countdown.stop()
        except AttributeError:
            pass

    def _linkButtons(self) -> None:
        """Link buttons to functionality."""
        self.buttons[PROCEED].clicked.connect(self._advanceState)
        #self.buttons["ABORT"].clicked.connect(self._abortMission)
    
    def _countDown(self) -> None:
        """Starts countdown"""
        if not self.aborted:
            self.moment = 11
            def _countSecond():
                self.moment -= 1
                if self.moment == 0:
                    self.moment = "BLASTOFF"
                    self.countdown.stop()
                self.dynamicLabels[CURR_STATE].setText(f"<h1> COUNTDOWN: {self.moment} </h1>")
            _countSecond()
            self.countdown = QTimer()
            self.countdown.timeout.connect(_countSecond)
            self.countdown.start(1000)

def main():
    """Rocket Control GUI"""
    app = QApplication(sys.argv)
    rocketDisplay = RocketDisplayWindow()
    rocketDisplay.showMaximized()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()





'''
class RocketControlWindow:

    def __init__(self, view: RocketDisplayWindow, model=None) -> None:
        self._respond = model
        self._view = view
    
    def _connectButtonSignals(self):
        #self._view.buttons["PROCEED"].clicked.connect(self._view._advanceState)
        pass'''