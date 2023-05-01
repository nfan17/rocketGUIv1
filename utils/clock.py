"""
Author: Nick Fan
Date: 3/2023
Description: Clock object for use with PyQt6 applications.
"""

from PyQt6.QtWidgets import QLabel
from PyQt6.QtCore import Qt, QTimer, QDateTime

class Clock:
    """QLabel clock class to display self-updating label with time/date."""

    def __init__(self, style: str) -> None:
        self.dateTime = QLabel()
        self.dateTime.setStyleSheet(style)
        self.dateTime.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.timer = QTimer()
        self.updateTime()
        self.timer.timeout.connect(self.updateTime)
        self.timer.start(1000)
    
    def updateTime(self):
        """Updates the time and date display."""
        currentTime = QDateTime.currentDateTime().toString("hh:mm:ss | MM/dd/yyyy")
        self.dateTime.setText(currentTime)
