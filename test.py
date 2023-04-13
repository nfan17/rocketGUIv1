
from main import *

STAGE_FONT_WHITE = "color: white; font-family: consolas; font-size: 13px; "
STAGE_FONT_BLUE = "color: #00A891; font-family: consolas; font-size: 13px; "

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
        + "  ->  Acceptable rate = 1 PSI / Min\n"
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
    FIRE_INIT_MSG = "-> Start fire sequence\n\n"

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

    class State:

        def __init__(self, next, confirms) -> None:
            self.next = next
            self.confirms = confirms

    def __init__(self, procedure: FireProcedure):
        self.states = {}
        self.procedure = procedure
        self.start = procedure.currentStage
    
    @property
    def current(self) -> str:
        return self.procedure.currentStage

    @current.setter
    def current(self, stage: str) -> None:
        self.procedure.currentStage = stage

    def addState(self, name, next, confirms):
        self.states[name] = StateMachine.State(next, confirms)

    def update(self):
        print(self.procedure.tasks[self.current])
        for task in self.procedure.tasks[self.current].values():
            if not task:
                return False
        last = self.current
        self.current = self.states[self.current].next
        return last


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.mainLayout = QGridLayout()
        self.generalLayout = QGridLayout()
        self.setPalette(DarkCyanPalette())
        self.setMaximumHeight(500)
        self.setMaximumWidth(300)

        self.procedure = FireProcedure()
        self.generalLayout.addWidget(self.procedure)
        self.sm = StateMachine(self.procedure)
        self.sm.addState(RocketStates.IDLE, RocketStates.HIGH_PRESS, self.procedure.idleTasks)
        self.sm.addState(RocketStates.HIGH_PRESS, RocketStates.TANK_HP, self.procedure.highPressTasks)
        self.sm.addState(RocketStates.TANK_HP, RocketStates.FIRE, self.procedure.tankHighPressTasks)
        self.sm.addState(RocketStates.FIRE, None, self.procedure.fireTasks)

        buttonLay = QGridLayout()
        stage = QPushButton("Advance Stage")
        sett = QPushButton("Mark Next Task")
        buttonLay.addWidget(stage)
        buttonLay.addWidget(sett)
        stage.clicked.connect(self.updateStage)
        sett.clicked.connect(self.updateTask)
    
        self.generalLayout.addLayout(buttonLay, 1, 0)
        centralWidget = QWidget()
        centralWidget.setLayout(self.generalLayout)
        self.setCentralWidget(centralWidget)
    
    def updateStage(self):
        last = self.sm.update()
        if not last:
            print("tasks incomplete")
            return
        self.procedure.changeStatus(last)
    
    def updateTask(self):
        task, msg = self.sm.states[self.sm.current].confirms()
        print(task, msg)
        conf = QMessageBox(
            QMessageBox.Icon.Warning,
                "Status Confirmation",
                msg,
                QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
                self.centralWidget(),
        )
        conf.setDefaultButton(QMessageBox.StandardButton.Cancel)
        if conf.exec() == QMessageBox.StandardButton.Ok and task != RocketStates.NULL:
            self.procedure.changeStatus(task)
            print(self.procedure.tasks)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    tasksDisplay = MainWindow()
    tasksDisplay.showMaximized()
    sys.exit(app.exec())