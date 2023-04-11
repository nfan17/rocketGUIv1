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
    QGroupBox,
    QMessageBox
)

from PyQt6.QtCore import Qt, QTimer, QDateTime, QObject, pyqtSignal
from PyQt6.QtGui import QColor, QIcon, QPalette


MIN_SIZE = 600
ICON_PATH = r"src\octoLogo"

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

HEADER_STYLE = "color: white; font-family: consolas; font-size: 9px; "
LAUNCH_STATES = ("IDLE", "HIGH PRESSURE", "TANK HIGH PRESSURE", "FIRE")
LEAK_ACCEPT_RATE = "1 PSI / Min"

#STATIC_F_MODE = ("IDLE", "HIGH PRESSURE", "TANK HIGH PRESSURE", "FIRE")

# Dynamic Labels Map
DIAGRAM_LABEL = "D_Label"
STATUS_LABEL = "Status"
CURR_STATE = "StateDisplay"

# Button Map
PROCEED = "ADVANCE STAGE"
IGNITION_FAILURE = "IGNITION FAIL"
OVERPRESSURE = "OVERPRESSURE"

# Pin Map

STAGE_FONT_WHITE = "color: white; font-family: consolas; font-size: 13px; "
STAGE_FONT_BLUE = "color: #00A891; font-family: consolas; font-size: 13px; "

class RocketStates:

    # States
    IDLE = "1. Leak Checks"
    HIGH_PRESS = "2. Upper Pressurization"
    TANK_HP = "3. Fuel/Ox Pressurization"
    FIRE = "4. Initiate Launch"

    states = (IDLE, HIGH_PRESS, TANK_HP, FIRE)

    # Indexing
    TASK_DESC = 0
    TASK_STATE = 1

    # Idle Tasks
    COPV_OPEN = "COPV_O"
    COPV_OPEN_MSG = (
        "-> Open COPV SV until PTs stabilize\n"
        + "  ->  Acceptable rate = 1 PSI / Min"
    )

    # High Pressure Tasks
    KBOTTLE = "KBOTTLE"
    COPV_EQ = "COPV_E"
    KBOTTLE_MSG = "-> Open K-bottle on launch pad"
    COPV_EQ_MSG = "-> Open COPV SV to equalize pressure\n   in COPV"

    # Tank High Press Tasks
    COPV_CLOSE = "COPV_C"
    TANKS_OPEN = "TANKS"
    COPV_CLOSE_MSG = "-> Close COPV SV"
    TANKS_OPEN_MSG = "-> Open tank SVs (3) and validate\n   leak rate"

    # Fire Tasks
    FIRE_INIT = "FIRE_I"
    FIRE_INIT_MSG = "-> Start fire sequence"

    # Tasks
    IDLE_TASKS = { COPV_OPEN: (COPV_OPEN_MSG, False) }
    HP_TASKS = { KBOTTLE: (KBOTTLE_MSG, False), COPV_EQ: (COPV_EQ_MSG, False) }
    TANK_HP_TASKS = { COPV_CLOSE: (COPV_CLOSE_MSG, False), TANKS_OPEN: (TANKS_OPEN_MSG, False) }
    FIRE_TASKS = { FIRE_INIT: (FIRE_INIT_MSG, False) }

class TaskList(QLabel):

    def __init__(self) -> None:
        super().__init__()
        self.currentStage = 0
        self.labels = {}

        self.stages = {
            RocketStates.IDLE: self.addStage(RocketStates.IDLE, RocketStates.IDLE_TASKS),
            RocketStates.HIGH_PRESS: self.addStage(RocketStates.HIGH_PRESS, RocketStates.HP_TASKS),
            RocketStates.TANK_HP: self.addStage(RocketStates.TANK_HP, RocketStates.TANK_HP_TASKS),
            RocketStates.FIRE: self.addStage(RocketStates.FIRE, RocketStates.FIRE_TASKS),
        }

        self.generalLayout = QGridLayout()
        for i, stage in enumerate(self.stages.keys()):
            self.generalLayout.addLayout(self.stages[stage], i, 0)

        self.setLayout(self.generalLayout)

    def addStage(self, name: str, tasks: dict) -> QGridLayout:
        layout = QGridLayout()
        header = QLabel(f"<h1> {name} </h1>")
        header.setStyleSheet(HEADER_STYLE)
        self.labels[name] = header
        layout.addWidget(header, 0, 0, 1, 1)

        for i, task in enumerate(tasks.keys()):
            t = tasks[task]
            label = QLabel(f"{t[0]}")
            label.setStyleSheet(STAGE_FONT_WHITE)
            self.labels[task] = label
            layout.addWidget(label, i + 1, 0, 1, 1)
        return layout

    def changeStatus(self, label: str, status: bool= True) -> None:
        color = "#00A891" if status else "white"
        fontSize = 9 if label in RocketStates.states else 13
        self.labels[label].setStyleSheet(
            f"color: {color}; font-family: consolas; font-size: {fontSize}px; "
        )

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
        currentTime = QDateTime.currentDateTime().toString("       hh:mm:ss | MM/dd/yyyy")
        self.dateTime.setText(currentTime)

class DarkCyanPalette(QPalette):
    """Dark and Cyan Palette."""

    def __init__(self) -> None:
        super().__init__()
        self.setColor(QPalette.ColorRole.Window, PRIMARY)
        self.setColor(QPalette.ColorRole.WindowText, DETAILING)
        self.setColor(QPalette.ColorRole.Text, WHITE)
        self.setColor(QPalette.ColorRole.Base, SECONDARY)


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

        self.clock = Clock("color: white; font-family: consolas; font-size: 16px; ")

        self.generalLayout = self.createMainGrid()

        centralWidget = QWidget()
        centralWidget.setLayout(self.generalLayout)
        self.setCentralWidget(centralWidget)

        self.linkButtons()

    def createLabelBox(self, message: str | None= None,
                labelType: str | None= None,
                style: str | None= None) -> QLabel:
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

    @staticmethod
    def createLayout(parent, widgets: list[tuple]) -> QGridLayout:
        """Creates a layout of widgets.
        
        Args:
            widgets(list): list of widgets to place in layout,
            plus layout

        Returns:
            QGridLayout: layout of widgets

        Widget list format example:
        [(button, x, y, h, l), (button, x, y, h, l), (someWidget, x, y, h, l)]
        """
        pos = QGridLayout(parent)
        for widget in widgets:
            params = len(widget)
            if params == 3:  # widget, x, y
                pos.addWidget(widget[0], widget[1], widget[2])
            elif params == 5:  # widget, x, y, height, length
                pos.addWidget(widget[0], widget[1], widget[2], widget[3], widget[4])
        return pos

    def createLayoutBox(self, widgets: list[tuple]) -> QLabel:
        """Creates a frame box with layout of widgets.

        Args:
            widgets(list): list of widgets to place in layout,
            plus grid location.
        
        Returns:
            QLabel: the generated frame box with given widgets.

        Widget list format example:
        [(button, x, y, h, l), (button, x, y, h, l), (someWidget, x, y, h, l)]
        """
        label = QLabel()
        self.createLayout(label, widgets)
        label.setFrameStyle(QFrame.Shape.Panel)
        label.setLineWidth(1)
        return label
    
    def createMainGrid(self) -> QGridLayout:
        """Creates primary display grid with frame boxes and components.

        Returns:
            QGridLayout: the primary frame layout
        """
        grid = QGridLayout()
        grid.setHorizontalSpacing(1)
        grid.setVerticalSpacing(1)

        # top row
        grid.addWidget(self.createLabelBox("<h1> VEHICLE STATUS </h1>", STATUS_LABEL, HEADER_STYLE), 0, 0, 1, 3)
        grid.addWidget(self.createLabelBox("<h1> FLUIDS CONTROL DISPLAY </h1>", DIAGRAM_LABEL, HEADER_STYLE), 0, 3, 1, 6)
        #grid.addWidget(self.createLabelBox(), 0, 9, 1, 3)
        grid.addWidget(self.createLayoutBox([(self.clock.dateTime, 0, 0, 1, 1)]), 0, 9, 1, 3)

        # left column
        self.states = TaskList()
        self.states.changeStatus(RocketStates.IDLE, True)

        grid.addWidget(self.createLabelBox(f"<h1>STATE: {self.mode[self.currentState]}</h1>", CURR_STATE, HEADER_STYLE), 1, 0, 1, 3)
        grid.addWidget(self.createLayoutBox([(self.states, 0, 0, 1, 1)]), 2, 0, 8, 3)
        grid.addWidget(self.createLayoutBox(self.createButtonSets([(PROCEED, 0, 0, 1, 2), (OVERPRESSURE, 1, 0, 1, 1), (IGNITION_FAILURE, 1, 1, 1, 1)])), 10, 0, 2, 3)
        #grid.addWidget(self.createLayoutBox([(self.clock.dateTime, 0, 0)]), 12, 0, 2, 3)
        grid.addWidget(self.createLabelBox(), 12, 0, 2, 3)

        # middle, right column
        grid.addWidget(self.createLabelBox(), 1, 3, 13, 6)
        grid.addWidget(self.createLabelBox(), 1, 9, 13, 3)

        # bottom row
        #grid.addWidget(self.createLabelBox(), 13, 0, 3, 6)
        #grid.addWidget(self.createLabelBox(), 13, 6, 3, 5)
        #grid.addWidget(self.createLayoutBox([(self.clock.dateTime, 0, 0)]), 13, 11, 3, 1)

        return grid

    def createButtonSets(self, keys: list[tuple]) -> list[tuple]:
        """Generate status control buttons.
        
        Args:
            keys(list[str]): list of button names (for dictionary hashing)

        Returns:
            list[tuple]: list of tuples with buttons and x, y grid locations.

        """
        buttonDisplay = []
        for key, w, x, y, z in keys:
            self.buttons[key] = QPushButton(key)
            self.buttons[key].setFocusPolicy(Qt.FocusPolicy.NoFocus)
            self.buttons[key].setStyleSheet(BUTTON_STYLE)
            buttonDisplay.append((self.buttons[key], w, x, y, z))
        return buttonDisplay

    def advanceState(self) -> None:
        """Advance current state."""
        # display
        if self.currentState <= len(self.mode) - 2 and not self.aborted:
            self.currentState += 1
            self.dynamicLabels[CURR_STATE].setText(f"<h1>STATE: {self.mode[self.currentState]}")
            self.dynamicLabels[CURR_STATE].setStyleSheet(HEADER_STYLE)

        elif self.currentState == len(self.mode) - 1 and not self.aborted:
            self.countDown()
            # reference for removing and adding widgets
            remove = self.generalLayout.itemAtPosition(2, 0)
            widget = remove.widget()
            self.generalLayout.removeWidget(widget)
            self.generalLayout.addWidget(self.createLabelBox("whoooo", "helloTest", HEADER_STYLE), 2, 0, 8, 3)

    def abortMission(self, confirmation: str) -> bool:
        """Abort mission confirmation.
        
        Args:
            confirmation(str): the confirmation message to ask

        Returns:
            bool: abortion confirmation status
        """
        conf = QMessageBox(
                QMessageBox.Icon.Warning,
                "Mission Abort Confirmation",
                confirmation,
                QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
                self.centralWidget(),
        )
        conf.setDefaultButton(QMessageBox.StandardButton.Cancel)
        if conf.exec() == QMessageBox.StandardButton.Ok:
            self.dynamicLabels[CURR_STATE].setText("<h1> MISSION ABORTED </h1>")
            self.aborted = True
            try:
                self.countdown.stop()
            except AttributeError:
                pass
            return True
        return False

    def abortOverpressure(self) -> None:
        """Begins overpressurization abort sequence on confirmation."""
        if not self.aborted:
            if self.abortMission("Begin overpressurization abort sequence?"):
                print("Change task display: beginning pressure relief sequence.")
                print("Close K-bottle SV.")
                print("Open Bottom right SV")
                print("Open Bottom Left SV")
                print("Open Fuel line SV")
                print("Open Ox line SV")
                print("Open top center SV")
                print("Change task display: Overpressure abort sequence complete.")
    
    def abortIgnitionFail(self) -> None:
        """Begins ignition fail abort sequence on confirmation."""
        if not self.aborted:
            if self.abortMission("Begin ignition fail abort sequence?"):
                print("Change task display: Ignition failure: entering HOLD stage.")
                print("Closing K-bottle SV")
                print("Close Bottom right SV")
                print("Close Bottom Left SV")
                print("Close Fuel line SV")
                print("Close Ox line SV")
                print("Close top center SV")
                print("Change task display: HOLD STAGE")

    def linkButtons(self) -> None:
        """Link buttons to functionality."""
        self.buttons[PROCEED].clicked.connect(self.advanceState)
        self.buttons[OVERPRESSURE].clicked.connect(self.abortOverpressure)
        self.buttons[IGNITION_FAILURE].clicked.connect(self.abortIgnitionFail)
    
    def countDown(self) -> None:
        """Starts countdown"""
        if not self.aborted:
            self.moment = 11
            def countSecond():
                self.moment -= 1
                if self.moment == 0:
                    self.moment = "BLASTOFF"
                    self.countdown.stop()
                self.dynamicLabels[CURR_STATE].setText(f"<h1> COUNTDOWN: {self.moment} </h1>")
            countSecond()
            self.countdown = QTimer()
            self.countdown.timeout.connect(countSecond)
            self.countdown.start(1000)

def main():
    """Rocket Control GUI"""
    app = QApplication(sys.argv)
    rocketDisplay = RocketDisplayWindow()
    rocketDisplay.showMaximized()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
