
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

class TaskList(QLabel):

    def __init__(self) -> None:
        super().__init__()
        self.currentStage = 0
        self.labels = {}

        self.stages = {
            RocketStates.IDLE: self.addStage("Leak Checks:", RocketStates.IDLE_TASKS),
            RocketStates.HIGH_PRESS: self.addStage("Upper Pressurization:", RocketStates.HP_TASKS),
            RocketStates.TANK_HP: self.addStage("Fuel/Ox Pressurization:", RocketStates.TANK_HP_TASKS),
            RocketStates.FIRE: self.addStage("Initiate Launch:", RocketStates.FIRE_TASKS),
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
            label.setStyleSheet(HEADER_STYLE + "font-size: 13px")
            self.labels[task] = label
            layout.addWidget(label, i + 1, 0, 1, 1)
        return layout

    def changeStatus(self, label: str, status: bool= True) -> None:
        color = "#00A891" if status else "white"
        fontSize = 9 if label in RocketStates.states else 13
        self.labels[label].setStyleSheet(
            f"color: {color}; font-family: consolas; font-size: {fontSize}px; "
        )

class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.mainLayout = QGridLayout()
        self.generalLayout = QGridLayout()
        self.setPalette(DarkCyanPalette())
        self.setMaximumHeight(500)
        self.setMaximumWidth(300)
        self.states = TaskList()
        self.generalLayout.addWidget(self.states)
        self.states.changeStatus(RocketStates.IDLE)
        self.states.changeStatus(RocketStates.COPV_OPEN)
        self.states.changeStatus(RocketStates.KBOTTLE)

        centralWidget = QWidget()
        centralWidget.setLayout(self.generalLayout)
        self.setCentralWidget(centralWidget)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    tasksDisplay = MainWindow()
    tasksDisplay.showMaximized()
    sys.exit(app.exec())