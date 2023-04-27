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
    QWidget,
    QFrame,
    QMessageBox
)

from PyQt6.QtCore import Qt, QTimer, QDateTime, QThread, pyqtSlot
from PyQt6.QtGui import QIcon

from utils import *


MIN_SIZE = 600
ICON_PATH = r"src\octoLogo"

LAUNCH_STATES = ("IDLE", "HIGH PRESSURE", "TANK HIGH PRESSURE", "FIRE")
LEAK_ACCEPT_RATE = "1 PSI / Min"

# Dynamic Labels Map
DIAGRAM_LABEL = "D_Label"
STATUS_LABEL = "Status"
CURR_STATE = "StateDisplay"
ABORT = "Abort"

# Button Map
PROCEED = "\nADVANCE STAGE\n"
MARK_STEP = "\nMARK NEXT TASK\n"
IGNITION_FAILURE = "IGNITION FAIL"
OVERPRESSURE = "OVERPRESSURE"

# Pin Map


class RocketStates:

    # States
    IDLE = "Leak Checks:"
    HIGH_PRESS = "Upper Pressurization:"
    TANK_HP = "Fuel/Ox Pressurization:"
    FIRE = "Initiate Launch:"

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

    NULL = None


class FireProcedure(QLabel):

    def __init__(self) -> None:
        super().__init__()
        self.currentStage = RocketStates.IDLE
        self.labels = {}
        self.tasks = {}

        # set stages ------------------------------------------------------------------------------|
        self.stages = {
            RocketStates.IDLE: self.addStage(RocketStates.IDLE, RocketStates.IDLE_TASKS),
            RocketStates.HIGH_PRESS: self.addStage(RocketStates.HIGH_PRESS, RocketStates.HP_TASKS),
            RocketStates.TANK_HP: self.addStage(RocketStates.TANK_HP, RocketStates.TANK_HP_TASKS),
            RocketStates.FIRE: self.addStage(RocketStates.FIRE, RocketStates.FIRE_TASKS),
        }
        # -----------------------------------------------------------------------------------------|

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
            label.setStyleSheet(HEADER_STYLE + "font-size: 13px")
            self.labels[task] = label
            try:
                self.tasks[name].update({ task: t[1] })
            except KeyError:
                self.tasks[name] = { task: t[1]}
            layout.addWidget(label, i + 1, 0, 1, 1)
        return layout

    def changeStatus(self, label: str, status: bool= True) -> None:
        color = "#00A891" if status else "white"
        try:
            if label in RocketStates.states:
                fontSize = 9
            else:
                fontSize = 13
                self.tasks[self.currentStage][label] = status
            self.labels[label].setStyleSheet(
                f"color: {color}; font-family: consolas; font-size: {fontSize}px; "
            )
        except KeyError:
            return
    
    def idleTasks(self):
        if not self.tasks[RocketStates.IDLE][RocketStates.COPV_OPEN]:
            return RocketStates.COPV_OPEN, "Confirm COPV open/Acceptable leak rate?"
        return RocketStates.NULL, "No more tasks, advance stage to continue."

    def highPressTasks(self):
        if not self.tasks[RocketStates.HIGH_PRESS][RocketStates.KBOTTLE]:
            return RocketStates.KBOTTLE, "Confirm K-bottle has been opened?"
        if not self.tasks[RocketStates.HIGH_PRESS][RocketStates.COPV_EQ]:
            return RocketStates.COPV_EQ, "Confirm COPV pressure equalization?"
        return RocketStates.NULL, "No more tasks, advance stage to continue."

    def tankHighPressTasks(self):
        if not self.tasks[RocketStates.TANK_HP][RocketStates.COPV_CLOSE]:
            return RocketStates.COPV_CLOSE, "Confirm COPV SV is closed?"
        if not self.tasks[RocketStates.TANK_HP][RocketStates.TANKS_OPEN]:
            return RocketStates.TANKS_OPEN, "Confirm top 3 SVs open/Acceptable leak rate?"
        return RocketStates.NULL, "No more tasks, advance stage to continue."

    def fireTasks(self):
        if not self.tasks[RocketStates.FIRE][RocketStates.FIRE_INIT]:
            return RocketStates.FIRE_INIT, "Confirm begin fire sequence?"
        return RocketStates.NULL, "No more tasks."

class StateMachine:
    """State machine for launch procedure steps."""

    class State:
        """Linked nodes to point to next state."""

        def __init__(self, next, confirms) -> None:
            self.next = next
            self.confirms = confirms

    def __init__(self, procedure: FireProcedure):
        self.states = {}
        self.procedure = procedure
        self.start = procedure.currentStage
    
    @property
    def current(self) -> str:
        """Current state property."""
        return self.procedure.currentStage

    @current.setter
    def current(self, stage: str) -> None:
        """Sets current procedure in FireProcedure."""
        self.procedure.currentStage = stage

    def addState(self, name, next, confirms) -> None:
        """Adds a state.
        
        Args:
            name: the name of the state
            next: the next state
            confirms: the confirmation message to procede
        """
        self.states[name] = StateMachine.State(next, confirms)

    def update(self):
        """Updates task status."""
        for task in self.procedure.tasks[self.current].values():
            if not task:
                return False
        last = self.current
        self.current = self.states[self.current].next
        return last

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
        currentTime = QDateTime.currentDateTime().toString("      hh:mm:ss | MM/dd/yyyy")
        self.dateTime.setText(currentTime)

# MAIN WINDOW -------------------------------------------------------------------------------------------------|

class RocketDisplayWindow(QMainWindow):
    """Main Rocket Control Window."""

    def __init__(self) -> None:
        """Constructs new Rocket Display Window."""
        super().__init__()

        # values
        self.mode = LAUNCH_STATES
        self.currentState = 0
        self.aborted = False
        self.buttons = {}
        self.dynamicLabels = {}

        # window
        self.setWindowTitle("Mission Control")
        self.setMinimumSize(MIN_SIZE * 2, MIN_SIZE)
        self.setWindowIcon(QIcon(ICON_PATH))
        self.pal = DarkCyanPalette()
        self.setPalette(self.pal)

        # layout
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

    def createLayout(self, parent, widgets: list[tuple]) -> QGridLayout:
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

    def createConfBox(self, title: str, message: str, default: bool=True) -> bool:
        conf = QMessageBox(
            QMessageBox.Icon.Warning,
                title,
                message,
                QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
                self.centralWidget(),
        )
        if not default:
            conf.setDefaultButton(QMessageBox.StandardButton.Cancel)
        if conf.exec() == QMessageBox.StandardButton.Ok:
            return True
        return False

    def createMainGrid(self) -> QGridLayout:
        """Creates primary display grid with frame boxes and components.

        Returns:
            QGridLayout: the primary frame layout
        """
        grid = QGridLayout()
        grid.setHorizontalSpacing(1)
        grid.setVerticalSpacing(1)

        # top row
        self.clock = Clock("color: white; font-family: consolas; font-size: 16px; ")
        
        grid.addWidget(self.createLabelBox("<h1> VEHICLE STATUS </h1>", STATUS_LABEL, HEADER_STYLE), 0, 0, 1, 3)
        grid.addWidget(self.createLabelBox("<h1> FLUIDS CONTROL DISPLAY </h1>", DIAGRAM_LABEL, HEADER_STYLE), 0, 3, 1, 6)
        grid.addWidget(self.createLayoutBox([(self.clock.dateTime, 0, 0, 1, 1)]), 0, 9, 1, 3)

        # left column
        self.procedure = FireProcedure()
        self.sm = StateMachine(self.procedure)
        self.sm.addState(RocketStates.IDLE, RocketStates.HIGH_PRESS, self.procedure.idleTasks)
        self.sm.addState(RocketStates.HIGH_PRESS, RocketStates.TANK_HP, self.procedure.highPressTasks)
        self.sm.addState(RocketStates.TANK_HP, RocketStates.FIRE, self.procedure.tankHighPressTasks)
        self.sm.addState(RocketStates.FIRE, None, self.procedure.fireTasks)

        grid.addWidget(self.createLabelBox(f"<h1>STAGE: {self.mode[self.currentState]}</h1>", CURR_STATE, HEADER_STYLE), 1, 0, 1, 3)
        grid.addWidget(self.createLayoutBox([(self.procedure, 0, 0, 1, 1)]), 2, 0, 8, 3)
        grid.addWidget(self.createLayoutBox(self.createButtonSets([(PROCEED, 0, 0, 1, 1), (MARK_STEP, 0, 1, 1, 1)])), 10, 0, 2, 3)
        #grid.addWidget(self.createLayoutBox([(self.clock.dateTime, 0, 0)]), 12, 0, 2, 3)
        #grid.addWidget(self.createLayoutBox([(self.states, 0, 0, 1, 1)]), 4, 0, 8, 3)
        #grid.addWidget(self.createLayoutBox(self.createButtonSets([(PROCEED, 0, 0, 1, 1), (MARK_STEP, 0, 1, 1, 1)])), 2, 0, 2, 3)
        grid.addWidget(self.createLabelBox(f"<h1>ABORT MISSION: </h1>", ABORT, HEADER_STYLE), 12, 0, 1, 3)
        grid.addWidget(self.createLayoutBox(self.createButtonSets([(OVERPRESSURE, 0, 0, 1, 1), (IGNITION_FAILURE, 0, 1, 1, 1)])), 13, 0, 1, 3)

        # middle, right column
        grid.addWidget(self.createLabelBox(), 1, 3, 13, 6)
        grid.addWidget(self.createLabelBox(), 1, 9, 11, 3)
        grid.addWidget(self.createLabelBox(), 12, 9, 2, 3)

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
            self.dynamicLabels[CURR_STATE].setText(f"<h1>STAGE: {self.mode[self.currentState]}")
            self.dynamicLabels[CURR_STATE].setStyleSheet(HEADER_STYLE)

        elif self.currentState == len(self.mode) - 1 and not self.aborted:
            self.countDown()
            # reference for removing and adding widgets
            remove = self.generalLayout.itemAtPosition(2, 0)
            widget = remove.widget()
            self.generalLayout.removeWidget(widget)
            self.generalLayout.addWidget(self.createLabelBox("whoooo", "helloTest", HEADER_STYLE), 2, 0, 8, 3)

    def updateStage(self):
        """Tries to update the stage."""
        if not self.aborted:
            if not self.createConfBox("Stage Advancement", "Confirm: advance to next stage?", default=False):
                return
            last = self.sm.update()
            if not last:
                self.createConfBox("Stage Advancement", "Incomplete tasks remaining, unable to advance.")
                return
            if self.currentState <= len(self.mode) - 2 and not self.aborted:
                self.currentState += 1
                self.dynamicLabels[CURR_STATE].setText(f"<h1>STAGE: {self.mode[self.currentState]}")
                self.dynamicLabels[CURR_STATE].setStyleSheet(HEADER_STYLE)
            self.procedure.changeStatus(last)
    
    def updateTask(self):
        """Tries to update a task."""
        if not self.aborted:
            task, msg = self.sm.states[self.sm.current].confirms()
            print(task, msg)
            conf = self.createConfBox("Status Confirmation", msg, default=False)
            if conf and task != RocketStates.NULL:
                self.procedure.changeStatus(task)

    def abortMission(self, confirmation: str) -> bool:
        """Abort mission confirmation.
        
        Args:
            confirmation(str): the confirmation message to ask

        Returns:
            bool: abortion confirmation status
        """
        if self.createConfBox("Mission Abort Confirmation", confirmation, default=False):
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
        self.buttons[PROCEED].clicked.connect(self.updateStage)
        self.buttons[MARK_STEP].clicked.connect(self.updateTask)
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
