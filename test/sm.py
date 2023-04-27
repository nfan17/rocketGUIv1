class RocketStates:

    # States
    IDLE = "IDLE"
    HIGH_PRESS = "HIGH PRESSURE"
    TANK_HP = "TANK HIGH PRESSURE"
    FIRE = "FIRE"

    # Indexing
    TASK_DESC = 0
    TASK_STATE = 1

    # Idle Tasks
    COPV_OPEN = "COPV_O"
    COPV_OPEN_MSG = (
        "-> Open COPV SV until PTs reach COPV PSI\n"
        + "  ->  Acceptable rate = 1 PSI / Min"
    )

    # High Pressure Tasks
    KBOTTLE = "KBOTTLE"
    COPV_EQ = "COPV_E"
    KBOTTLE_MSG = "-> Open K-bottle on launch pad (manual)"
    COPV_EQ_MSG = "-> Open COPV SV to equalize pressure in COPV"

    # Tank High Press Tasks
    COPV_CLOSE = "COPV_C"
    TANKS_OPEN = "TANKS"
    COPV_CLOSE_MSG = "-> Close COPV SV"
    TANKS_OPEN_MSG = "-> Open tank SVs (3) and validate leak rate"

    # Fire Tasks
    FIRE_INIT = "FIRE_I"
    FIRE_INIT_MSG = "-> Initiate fire initialization"

    # Tasks
    IDLE_TASKS = { COPV_OPEN: (COPV_OPEN_MSG, False) }
    HP_TASKS = { KBOTTLE: (KBOTTLE_MSG, False), COPV_EQ: (COPV_EQ_MSG, False) }
    TANK_HP_TASKS = { COPV_CLOSE: (COPV_CLOSE_MSG, False), TANKS_OPEN: (TANKS_OPEN_MSG, False) }
    FIRE = { FIRE_INIT: (FIRE_INIT_MSG, False) }


class StateMachine:
    def __init__(self):
        self.handlers = {}
        self.start = None
        self.current = None
        self.ends = []

    def addState(self, name, handler, end_state=False):
        name = name
        self.handlers[name] = handler
        if end_state:
            self.ends.append(name)

    def setStart(self, name):
        self.start = name
        self.current = self.start

    def update(self, value):
        handler = self.handlers[self.current]
        (self.current, output) = handler(value)
        print(self.current, output)
        return self.current, output


# Example usage:

def idleHandler(state_input: bool):
    if input == 'go':
        return ('state2', 'going')
    else:
        return ('state1', '')

def handler2():
    if input == 'stop':
        return ('end', 'stopping')
    else:
        return ('state2', '')

m = StateMachine()
m.add_state('state1', handler1)
m.add_state('state2', handler2)
m.add_state('end', None, end_state=True)
m.set_start('state1')

try:
    while True:
        output = m.update(input("Enter input: "))
        print(output)
        if output[1]:
            break
except KeyboardInterrupt:
    pass
