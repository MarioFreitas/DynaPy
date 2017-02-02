from PyQt4.QtCore import *
from PyQt4.QtGui import *


class AnimationCanvas(QGraphicsView):
    def __init__(self, parent):
        super(AnimationCanvas, self).__init__(parent)
        self.scene1 = QGraphicsScene()
        self.setScene(self.scene1)

        # TODO Build animation (everything)