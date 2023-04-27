"""
Author: Nick Fan
Date: 3/2023
Description: Serial module for use with PyQt6 applications.
"""

import time
import serial
import serial.tools.list_ports
from PyQt6.QtCore import QMutex, QObject, pyqtSignal

class SerialComm:
    """Serial Com Manager."""

    def __init__(self, com: str, baudrate: int) -> None:
        """Creates new serial com manager.

        Args:
            com(str): the COM port
            baudrate(int): the baudrate
        """
        self.port = com
        self.baudrate = baudrate
        self.connection = serial.Serial(self.port, self.baudrate, timeout=0.05)

    def receiveMessage(self) -> str:
        """Read from serial com if there is data in."""
        if not self.connection.is_open:
            self.connection.open()
        try:
            data = str(self.connection.readall().decode("ascii"))
            if data:
                return data
        except serial.SerialException:
            pass
        return ""

    def readEolLine(self) -> str:
        """Reads line specifically using LF for eol.

        EoL readline by: lou under CC BY-SA 3.0
        src: https://stackoverflow.com/questions/16470903/pyserial-2-6-specify-end-of-line-in-readline
        Changes have been made to adjust for integration in this program.
        """
        eol = b"\n"
        eolLen = len(eol)
        line = bytearray()
        while True:
            c = self.connection.read(1)
            if c:
                line += c
                if line[-eolLen:] == eol:
                    break
            else:
                break
        return str(line.decode("ascii"))

    def sendMessage(self, message: str) -> bool:
        """Writes to serial com."""
        if not self.connection.is_open:
            self.connection.open()
        try:
            self.connection.write(message.encode("utf-8"))
            time.sleep(0.002)
            return True
        except serial.SerialException:
            return False

    def close(self):
        """Closes the com connection."""
        self.connection.close()


class SerialWorker(QObject):
    """GUI Serial Manager Thread."""

    msg = pyqtSignal(str)
    cleanup = pyqtSignal()
    error = pyqtSignal()

    def __init__(self, connection: SerialComm, lock: QMutex, pins: str, parent=None) -> None:
        """Constructs new Serial Worker.

        Args:
            connection(SerialComm): the serial connection to use
            pins(str): pins to toggle
            parent(QObject): optional parent
        """
        super().__init__(parent)
        self.serialConnection = connection
        self.pins = pins
        self.mutex = lock
        self.program = True

    def setPins(self, newPins: str) -> None:
        """Sets new pins.

        Args:
            newPins(str): a new set of pins to toggle.
        """
        self.pins = newPins

    def run(self) -> None:
        """Sends initial toggle and continuously reads
        until indicated to stop, then toggles again."""
        # read serial
        error = False
        while self.program:
            if not error:
                if self.mutex.tryLock():

                    try:
                        received = self.serialConnection.readEolLine()
                    except (serial.SerialException, UnicodeDecodeError):
                        self.error.emit()
                        error = True
                        received = None

                    time.sleep(0.05)
                    self.mutex.unlock()
                    time.sleep(0.02)
                    if not received:
                        continue
                    self.msg.emit(received)
    
        self.cleanup.emit()

    def sendToggle(self, pins: str | None = None) -> None:
        """Sends message, which by default is the pins instance variable.
        
        Args:
            pins(str): optional argument to indicate pins to toggle.
        """
        if pins:
            message = pins + "\n"
        else:
            message = self.pins + "\n"
        while True:
            if self.mutex.tryLock():
                self.serialConnection.sendMessage(message)
                self.mutex.unlock()
                break
