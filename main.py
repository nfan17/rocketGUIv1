#! /usr/bin/env python3

"""
Author: Nick Fan
Date: February 2023
Description: Liquid Rocket Project Launch Control GUI prototype.
"""

import re
import sys
from PyQt6.QtWidgets import (
    QApplication,
    QInputDialog,
    QGridLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QWidget,
    QFrame,
    QMessageBox,
    QTextEdit,
    QLineEdit,
)

from PyQt6.QtCore import Qt, QTimer, QDateTime, QThread, pyqtSlot
from PyQt6.QtGui import QIcon

from utils import *


MIN_SIZE = 600
ICON_PATH = "./src/rocketIcon.png"

WARNING = 0
ERROR = 1
MESSAGE_LABELS = ("Warning", "Error")

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
SETUP_SER = "SERIAL SETTINGS"
SER_TOGGLE = "START SERIAL"
SER_ON = "START SERIAL"
SER_OFF = "STOP SERIAL"
SERIAL_SEND = "Send"

# Pin Map
COMMAND_LEN = 8

class RocketStates:
    """Rocket state names and values."""

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
    """Fire procedure task list."""

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
        """Creates a layout for a new stage.
        
        Args:
            name(str): name of the stage (RocketStates.<STAGE> enums)
            tasks(str): dictionary of tasks (RocketStates.<STAGE>_TASKS enums)
        
        Returns:
            QGridLayout: layout for the stage.
        """
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
        """Changes the status of a task.
        
        Args:
            label(str): the label dictionary key
        """
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
    
    def idleTasks(self) -> tuple:
        """Returns state and confirmation messages for idle tasks.
        
        Returns:
            tuple: RocketStates.<STATE>, "<Confirmation message>"
        """
        if not self.tasks[RocketStates.IDLE][RocketStates.COPV_OPEN]:
            return RocketStates.COPV_OPEN, "Confirm COPV open/Acceptable leak rate?"
        return RocketStates.NULL, "No more tasks, advance stage to continue."

    def highPressTasks(self):
        """Returns state and confirmation messages for high press tasks.
        
        Returns:
            tuple: RocketStates.<STATE>, "<Confirmation message>"
        """
        if not self.tasks[RocketStates.HIGH_PRESS][RocketStates.KBOTTLE]:
            return RocketStates.KBOTTLE, "Confirm K-bottle has been opened?"
        if not self.tasks[RocketStates.HIGH_PRESS][RocketStates.COPV_EQ]:
            return RocketStates.COPV_EQ, "Confirm COPV pressure equalization?"
        return RocketStates.NULL, "No more tasks, advance stage to continue."

    def tankHighPressTasks(self):
        """Returns state and confirmation messages for tank high press tasks.
        
        Returns:
            tuple: RocketStates.<STATE>, "<Confirmation message>"
        """
        if not self.tasks[RocketStates.TANK_HP][RocketStates.COPV_CLOSE]:
            return RocketStates.COPV_CLOSE, "Confirm COPV SV is closed?"
        if not self.tasks[RocketStates.TANK_HP][RocketStates.TANKS_OPEN]:
            return RocketStates.TANKS_OPEN, "Confirm top 3 SVs open/Acceptable leak rate?"
        return RocketStates.NULL, "No more tasks, advance stage to continue."

    def fireTasks(self):
        """Returns state and confirmation messages for fire tasks.
        
        Returns:
            tuple: RocketStates.<STATE>, "<Confirmation message>"
        """
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

        self.serialSet = False
        self.serialOn = False

    # SERIAL FUNCTIONS

    def threadingSetup(self, serial: SerialComm) -> None:
        """Sets up threading, serial worker and signals/slots.
        
        *Serial Window Core
        """
        self.serialThread = QThread()
        self.serialLock = QMutex()
        self.serialWorker = SerialWorker(serial, self.serialLock, "")
        self.serialWorker.moveToThread(self.serialThread)
        self.serialThread.started.connect(self.serialWorker.run)
        self.serialWorker.cleanup.connect(self.serialThread.quit)
        self.serialWorker.error.connect(self.serialError)
        self.serialWorker.msg.connect(self.displayControl)
        self.serialThread.start()

    def selectPort(self) -> bool:
        """Checks for available ports and asks for a selection.

        Returns:
            bool: True setup is successful, False otherwise
        
        *Serial Window Core
        """
        ports = serial.tools.list_ports.comports()
        if len(ports) < 1:
            self.createConfBox(
                "Serial Error",
                "No COM ports available.\nPlease plug in devices before starting.",
            )
            return False
        
        warning = (
            "ATTENTION:\nWhen selecting a port, look for \"Arduino\" or \"Serial-USB\" "
            + "If you do not see an option like this, please cancel and check your USB connection."
        )
        conf = QMessageBox(
            QMessageBox.Icon.Warning,
            "Setup Confirmation",
            warning,
            QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
            self.centralWidget(),
        )

        conf.exec()

        selection, ok = QInputDialog().getItem(
            self.centralWidget(),
            "COM select", 
            "Select a port:",
            [f"{desc}" for name, desc, hwid in ports],
        )
        if not ok:
            return False

        self.port = str(re.findall(r"COM[0-9]+", selection)[0])  # get port

        return True

    def selectBaud(self) -> bool:
        """Asks for selection of a baudrate.

        Returns:
            bool: True setup is successful, False otherwise
        """
        selection, ok = QInputDialog().getItem(
            self.centralWidget(),
            "Baudrate select", 
            "Select a baudrate:",
            [str(rate) for rate in BAUDRATES],
        )

        if not ok:
            return False
        try:
            self.baud = int(selection)
        except ValueError:
            error = QMessageBox(
                QMessageBox.Icon.Critical,
                "Setup Error",
                "Setup error detected!",
                QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
                self.centralWidget(),
            )
            error.exec()
            return False
        return True
    
    def setupSerial(self) -> None:
        """Serial option selection."""
        if not self.selectPort() or not self.selectBaud():
            self.serialSet = False
        else:
            self.serialSet = True

    def toggleSerial(self) -> None:
        """Toggles serial connection on/off."""
        if self.serialSet and not self.serialOn:
            try:
                self.serial = setupConnection(self.port, self.baud)
                self.threadingSetup(self.serial)
                self.serialOn = True
                self.buttons[SER_TOGGLE].setText(SER_OFF)
            except serial.SerialException:
                self.createConfBox(
                    "Serial Error",
                    "Serial connection could not be established.",
                    QMessageBox.Icon.Critical
                )
        elif self.serialOn:
            self.serialOn = False
            self.serialWorker.program = False
            time.sleep(0.1)
            if self.serial.connection.is_open:
                self.serial.close()
            self.buttons[SER_TOGGLE].setText(SER_ON)
        else:
            self.createConfBox(
                "Serial Error",
                "Serial settings not configured.",
                QMessageBox.Icon.Critical,
            )
    
    def displayPrint(self, string: str, reformat=True) -> None:
        """Displays to monitor and logs data.

        Args:
            string(str): the string to display and log
            reformat(bool | None): add strFormat if True, otherwise do not
        """
        if reformat:
            string = self.strFormat(string)
        self.monitor.append(string)
        self.monitor.verticalScrollBar().setValue(
            self.monitor.verticalScrollBar().maximum()
        )
    
    def updateDisplay(self, dataset: list) -> None:
        """Updates display values in the window dictionaries.
        
        Args:
            dataset(list): list of parsed data in the format destination, value
        
        *Serial Window Core
        """
        for dest, value in dataset:
            try:
                self.dynamicLabels[dest].update(value.strip())
            except KeyError:
                continue

    @pyqtSlot(str)
    def displayControl(self, string: str) -> None:
        """Prints to display monitor, parses data, and updates live labels.

        Args:
            string(str): the incoming data
        
        *Serial Window Core
        """
        self.displayPrint(string)
        #data = self.parseData(string)
        #self.updateDisplay(data)
    
    def sendMessage(self) -> None:
        """Sends a specific message to toggle without starting a preset.
        
        *Serial Window Core
        """
        if self.serialSet and self.serialOn:
            #command = self.serialEntry.toPlainText()
            command = self.serialEntry.text()
            if len(set(command)) < len(command):
                self.createConfBox("Serial Message Warning", "Duplicate pin detected - please try again.")
                return
            self.monitor.append(self.strFormat(f"Send: {command}"))
            self.serialWorker.sendToggle(command + "0" * (COMMAND_LEN - len(command)))
        else:
            self.createConfBox("Serial Error", "Serial must be configured and on.", QMessageBox.Icon.Critical)

    def serialError(self) -> None:
        """Displays error popup upon handling of a serial exception."""
        self.createConfBox("Serial Error", "Serial error detected! Please try again.", QMessageBox.Icon.Warning)
        self.toggleSerial()
    
    def strFormat(self, string: str) -> str:
        """Returns formatted string for monitor display.

        Args:
            string(str): the string to format

        Returns:
            str: the formatted string
        """
        return QDateTime.currentDateTime().toString(DATE_TIME_FORMAT) + string.strip()

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

    def createConfBox(self, title: str, message: str,
            icon: QMessageBox.Icon=QMessageBox.Icon.Warning, default: bool=True) -> bool:
        """Creates a confirmation box.
        
        Args:
            title(str): title of the box window
            message(str): the message to display
            icon(QMessageBox.Icon): the icon for the window
            default(bool): default button ok (True) or cancel (False)
        """
        conf = QMessageBox(
            icon,
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

        

        grid.addWidget(self.createLabelBox(), 1, 9, 9, 3)
        grid.addWidget(self.createLayoutBox(self.createButtonSets([(SETUP_SER, 0, 0, 1, 1), (SER_ON, 0, 1, 1, 1)])), 10, 9, 1, 3)
        grid.addWidget(self.createLayoutBox(self.createSerialLayout()), 11, 9, 3, 3)

        return grid

    def createSerialLayout(self) -> list:
        """Creates and returns items of the serial setup for a layoutBox."""
        # Serial monitor box
        self.monitor = QTextEdit()
        self.monitor.setReadOnly(True)
        self.monitor.setFrameStyle(QFrame.Shape.NoFrame)
        self.monitor.setStyleSheet(COLOR_CSS)

        '''
        self.serialEntry = QTextEdit()
        self.serialEntry.setFrameStyle(QFrame.Shape.Panel)
        self.serialEntry.setMaximumHeight(LINE_HEIGHT)
        self.serialEntry.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.serialEntry.setStyleSheet(COLOR_CSS + FONT_CSS)
        '''
        # Message entry line
        self.serialEntry = QLineEdit()
        self.serialEntry.setStyleSheet(COLOR_CSS + FONT_CSS)
        self.serialEntry.setMaximumHeight(LINE_HEIGHT)
        
        # Send button
        self.buttons[SERIAL_SEND] = QPushButton(SERIAL_SEND)
        self.buttons[SERIAL_SEND].setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.buttons[SERIAL_SEND].setStyleSheet(BUTTON_STYLE)

        return [(
            self.serialEntry, 0, 0, 1, 1),
            (self.buttons[SERIAL_SEND], 0, 1, 1, 1),
            (self.monitor, 1, 0, 1, 2)
        ]

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
        """Advance current state.
        May be deprecated.
        """
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
                self.createConfBox(
                    "Stage Advancement",
                    "Incomplete tasks remaining, unable to advance.",
                    QMessageBox.Icon.Critical
                )
                return
            if self.currentState <= len(self.mode) - 2 and not self.aborted:
                self.currentState += 1
                self.dynamicLabels[CURR_STATE].setText(f"<h1>STAGE: {self.mode[self.currentState]}")
                self.dynamicLabels[CURR_STATE].setStyleSheet(HEADER_STYLE)
            # ADD SAFETY HERE FOR COMPLETION OF ALL STAGES OR MOVE INTO AN IF STATEMENT
            self.procedure.changeStatus(last)
    
    def updateTask(self):
        """Tries to update a task."""
        if not self.aborted:
            task, msg = self.sm.states[self.sm.current].confirms()
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
        if self.createConfBox("Mission Abort Confirmation",
                confirmation, default=False):
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
        self.buttons[SER_TOGGLE].clicked.connect(self.toggleSerial)
        self.buttons[SETUP_SER].clicked.connect(self.setupSerial)
        self.buttons[SERIAL_SEND].clicked.connect(self.sendMessage)

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


if __name__ == "__main__":
    app = QApplication(sys.argv)
    rocketDisplay = RocketDisplayWindow()
    rocketDisplay.showMaximized()
    sys.exit(app.exec())
