from PyQt4.QtCore import *
from PyQt4.QtGui import *


class TLCDCanvas(QGraphicsView):
    def __init__(self, parent):
        super(TLCDCanvas, self).__init__(parent)

        self.scene1 = QGraphicsScene(self)
        self.setScene(self.scene1)

    def painter(self, tlcd):
        greyColor = QColor(100, 100, 100, 255)
        blueColor = QColor(51, 255, 255, 255)

        pen4 = QPen()
        pen4.setWidth(4)

        pen0 = QPen()
        pen0.setColor(QColor(0, 0, 0, 0))

        blueBrush = QBrush()
        blueBrush.setColor(blueColor)
        blueBrush.setStyle(Qt.SolidPattern)

        font40 = QFont('Times', 40)

        if tlcd is None:
            self.scene1 = QGraphicsScene(self)
            self.setScene(self.scene1)

            # icon = QStyle.SP_MessageBoxWarning
            # self.msgRemoveStory = QMessageBox()
            # self.msgRemoveStory.setText('Opção ainda não implementada.')
            # self.msgRemoveStory.setWindowTitle('Erro de Implementação')
            # self.msgRemoveStory.setWindowIcon(self.msgRemoveStory.style().standardIcon(icon))
            # self.msgRemoveStory.show()

        elif tlcd.type == 'TLCD Simples':
            self.scene1 = QGraphicsScene(self)
            self.setScene(self.scene1)

            D = tlcd.diameter*100
            B = tlcd.width*100
            h = tlcd.waterHeight*100
            H = h*2

            h1 = QGraphicsLineItem(-B/2, 0, B/2, 0)
            h2 = QGraphicsLineItem(-B/2+D, -D, B/2-D, -D)
            h3 = QGraphicsLineItem(-B/2, -H, -B/2+D, -H)
            h4 = QGraphicsLineItem(B/2, -H, B/2-D, -H)
            h5 =QGraphicsLineItem(-B/2, -h, -B/2+D, -h)
            h6 = QGraphicsLineItem(B/2, -h, B/2-D, -h)

            v1 = QGraphicsLineItem(-B/2, 0, -B/2, -H)
            v2 = QGraphicsLineItem(B/2, 0, B/2, -H)
            v3 = QGraphicsLineItem(-B/2+D, -D, -B/2+D, -H)
            v4 = QGraphicsLineItem(B/2-D, -D, B/2-D, -H)

            r1 = QGraphicsRectItem(-B/2+2, 0-2, D-4, -h+4)
            r2 = QGraphicsRectItem(B/2-D+2, 0-2, D-4, -h+4)
            r3 = QGraphicsRectItem(-B/2+2, 0-2, B-4, -D+4)

            h1.setPen(pen4)
            h2.setPen(pen4)
            h3.setPen(pen4)
            h4.setPen(pen4)
            h5.setPen(pen4)
            h6.setPen(pen4)
            v1.setPen(pen4)
            v2.setPen(pen4)
            v3.setPen(pen4)
            v4.setPen(pen4)
            r1.setPen(pen0)
            r2.setPen(pen0)
            r3.setPen(pen0)

            r1.setBrush(blueBrush)
            r2.setBrush(blueBrush)
            r3.setBrush(blueBrush)

            self.scene1.addItem(h1)
            self.scene1.addItem(h2)
            self.scene1.addItem(h3)
            self.scene1.addItem(h4)
            self.scene1.addItem(h5)
            self.scene1.addItem(h6)
            self.scene1.addItem(v1)
            self.scene1.addItem(v2)
            self.scene1.addItem(v3)
            self.scene1.addItem(v4)
            self.scene1.addItem(r1)
            self.scene1.addItem(r2)
            self.scene1.addItem(r3)

            diameter = QGraphicsTextItem('D = {:.0f} cm'.format(D))
            diameter.setFont(font40)
            diameter.setTextWidth(diameter.boundingRect().width())
            diameter.setPos(0-diameter.textWidth()/2, 20)

            width = QGraphicsTextItem('B = {:.0f} m'.format(B/100))
            width.setFont(font40)
            width.setTextWidth(width.boundingRect().width())
            width.setPos(0-width.textWidth()/2, 140)

            waterHeight = QGraphicsTextItem('h = {:.0f} cm'.format(h))
            waterHeight.setFont(font40)
            waterHeight.setTextWidth(waterHeight.boundingRect().width())
            waterHeight.setPos(0-waterHeight.textWidth()/2, 80)

            self.scene1.addItem(diameter)
            self.scene1.addItem(width)
            self.scene1.addItem(waterHeight)

            self.setViewportMargins(10, 10, 10, 10)
            self.fitInView(self.scene1.itemsBoundingRect(), Qt.KeepAspectRatio)