from PyQt5.QtWidgets import QApplication, QGraphicsScene, QGraphicsView
from PyQt5.QtGui import QPen, QColor
import sys

class MyView(QGraphicsView):
    def __init__(self, parent=None):
        super(MyView, self).__init__(parent)

        # Create a scene and set its size
        self.gScene = QGraphicsScene(self)
        self.setScene(self.gScene)
        self.setSceneRect(0, 0, 400, 400)

        # Create a pen to draw lines
        self.pen = QPen(QColor(255, 0, 0))
        self.pen.setWidth(3)

        # Draw a diagonal line
        self.gScene.addLine(0, 0, 400, 400, self.pen)

        # Set the view's background color
        self.setBackgroundBrush(QColor(255, 255, 255))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    view = MyView()
    view.show()
    sys.exit(app.exec_())
