from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *


class StructureCanvas(QGraphicsView):
    def __init__(self, parent):
        super(StructureCanvas, self).__init__(parent)

        # self.setGeometry(0, 0, 200, 300)
        self.scene1 = QGraphicsScene()
        self.setScene(self.scene1)

        self.blackColor = QColor(0, 0, 0, 255)
        self.whiteColor = QColor(255, 255, 255, 255)

        self.pen4 = QPen()
        self.pen4.setWidth(4)
        self.pen4.setColor(self.blackColor)

        self.brush = QBrush()
        self.brush.setColor(self.blackColor)
        self.brush.setStyle(Qt.SolidPattern)

        self.brush2 = QBrush()
        self.brush2.setColor(self.whiteColor)
        self.brush2.setStyle(Qt.SolidPattern)

        self.font40 = QFont("Times", 40)

        # self.painter2()

    def painter(self, stories):
        self.scene1 = QGraphicsScene()
        self.setScene(self.scene1)

        level = 0
        b = 300
        h = 20
        for i in range(1, len(stories)+1):
            height = stories[i].height*100
            beam = QGraphicsRectItem(0, -(level+height),
                                     b, -h)
            beam.setPen(self.pen4)
            beam.setBrush(self.brush)

            column1 = QGraphicsLineItem(0, -level,
                                        0, -(level+height))
            column1.setPen(self.pen4)

            column2 = QGraphicsLineItem(b, -level,
                                        b, -(level+height))
            column2.setPen(self.pen4)

            storyNum = QGraphicsTextItem('{}'.format(i))
            storyNum.setFont(self.font40)
            storyNum.setTextWidth(storyNum.boundingRect().width())
            storyNum.setPos(b/2-storyNum.textWidth()/2, -(level+height/2)-30)
            numCircle = QGraphicsEllipseItem(b/2-storyNum.textWidth()/2-20,
                                             -(level+height/2)-30,
                                             storyNum.boundingRect().width()+40,
                                             80)

            storyMass = QGraphicsTextItem('{} ton'.format(stories[i].mass/1000))
            storyMass.setFont(self.font40)
            storyMass.setTextWidth(storyMass.boundingRect().width())
            # storyMass.setPos(b+20, -(level+height+40))
            storyMass.setPos(b/2-storyMass.textWidth()/2, -(level+height-10))


            storyHeight = QGraphicsSimpleTextItem('{} m'.format(stories[i].height))
            storyHeight.setPos(b+20, -(level+height/2)-65)
            storyHeight.setFont(self.font40)

            storySection = QGraphicsSimpleTextItem('({} x {}) cm'.format(stories[i].width*100, stories[i].depth*100))
            storySection.setPos(b+20, -(level+height/2)-10)
            storySection.setFont(self.font40)

            storyE = QGraphicsTextItem('{} GPa'.format(stories[i].E/1e9))
            storyE.setFont(self.font40)
            storyE.setTextWidth(storyE.boundingRect().width())
            storyE.setPos(-(storyE.textWidth()+20), -(level+height/2)-65)

            if stories[i].support == 'Fix-Fix':
                support = '(F-F)'
            elif stories[i].support == 'Fix-Pin':
                support = '(F-P)'
            elif stories[i].support == 'Pin-Fix':
                support = '(P-F)'
            elif stories[i].support == 'Pin-Pin':
                support = '(P-P)'

            storySupport = QGraphicsTextItem('{}'.format(support))
            storySupport.setFont(self.font40)
            storySupport.setTextWidth(storySupport.boundingRect().width())
            storySupport.setPos(-(storySupport.textWidth()+20), -(level+height/2)-10)

            self.scene1.addItem(beam)
            self.scene1.addItem(column1)
            self.scene1.addItem(column2)
            self.scene1.addItem(storyNum)
            self.scene1.addItem(storyMass)
            self.scene1.addItem(storyHeight)
            self.scene1.addItem(storySection)
            self.scene1.addItem(storyE)
            self.scene1.addItem(storySupport)
            self.scene1.addItem(numCircle)

            if i == 1:
                if support == '(F-F)':
                    l1e = QGraphicsLineItem(-30, 0,
                                            30, 0)
                    l2e = QGraphicsLineItem(-40, 10,
                                            -30, 0)
                    l3e = QGraphicsLineItem(-25, 10,
                                            -15, 0)
                    l4e = QGraphicsLineItem(-10, 10,
                                            0, 0)
                    l5e = QGraphicsLineItem(5, 10,
                                            15, 0)
                    l6e = QGraphicsLineItem(20, 10,
                                            30, 0)
                    l1d = QGraphicsLineItem(-30 + b, 0,
                                            30 + b, 0)
                    l2d = QGraphicsLineItem(-40 + b, 10,
                                            -30 + b, 0)
                    l3d = QGraphicsLineItem(-25 + b, 10,
                                            -15 + b, 0)
                    l4d = QGraphicsLineItem(-10 + b, 10,
                                            0 + b, 0)
                    l5d = QGraphicsLineItem(5 + b, 10,
                                            15 + b, 0)
                    l6d = QGraphicsLineItem(20 + b, 10,
                                            30 + b, 0)

                    l1e.setPen(self.pen4)
                    l2e.setPen(self.pen4)
                    l3e.setPen(self.pen4)
                    l4e.setPen(self.pen4)
                    l5e.setPen(self.pen4)
                    l6e.setPen(self.pen4)
                    l1d.setPen(self.pen4)
                    l2d.setPen(self.pen4)
                    l3d.setPen(self.pen4)
                    l4d.setPen(self.pen4)
                    l5d.setPen(self.pen4)
                    l6d.setPen(self.pen4)

                    self.scene1.addItem(l1e)
                    self.scene1.addItem(l2e)
                    self.scene1.addItem(l3e)
                    self.scene1.addItem(l4e)
                    self.scene1.addItem(l5e)
                    self.scene1.addItem(l6e)
                    self.scene1.addItem(l1d)
                    self.scene1.addItem(l2d)
                    self.scene1.addItem(l3d)
                    self.scene1.addItem(l4d)
                    self.scene1.addItem(l5d)
                    self.scene1.addItem(l6d)

                elif support == '(F-P)':
                    l1e = QGraphicsLineItem(-30, 0,
                                            30, 0)
                    l2e = QGraphicsLineItem(-40, 10,
                                            -30, 0)
                    l3e = QGraphicsLineItem(-25, 10,
                                            -15, 0)
                    l4e = QGraphicsLineItem(-10, 10,
                                            0, 0)
                    l5e = QGraphicsLineItem(5, 10,
                                            15, 0)
                    l6e = QGraphicsLineItem(20, 10,
                                            30, 0)
                    l1d = QGraphicsLineItem(-45 + b, 40,
                                            45 + b, 40)
                    l2d = QGraphicsLineItem(-40 + b, 50,
                                            -30 + b, 40)
                    l3d = QGraphicsLineItem(-25 + b, 50,
                                            -15 + b, 40)
                    l4d = QGraphicsLineItem(-10 + b, 50,
                                            0 + b, 40)
                    l5d = QGraphicsLineItem(5 + b, 50,
                                            15 + b, 40)
                    l6d = QGraphicsLineItem(20 + b, 50,
                                            30 + b, 40)
                    l7d = QGraphicsLineItem(-30 + b, 40,
                                            0 + b, 0)
                    l8d = QGraphicsLineItem(30 + b, 40,
                                            0 + b, 0)

                    l1e.setPen(self.pen4)
                    l2e.setPen(self.pen4)
                    l3e.setPen(self.pen4)
                    l4e.setPen(self.pen4)
                    l5e.setPen(self.pen4)
                    l6e.setPen(self.pen4)
                    l1d.setPen(self.pen4)
                    l2d.setPen(self.pen4)
                    l3d.setPen(self.pen4)
                    l4d.setPen(self.pen4)
                    l5d.setPen(self.pen4)
                    l6d.setPen(self.pen4)
                    l7d.setPen(self.pen4)
                    l8d.setPen(self.pen4)

                    self.scene1.addItem(l1e)
                    self.scene1.addItem(l2e)
                    self.scene1.addItem(l3e)
                    self.scene1.addItem(l4e)
                    self.scene1.addItem(l5e)
                    self.scene1.addItem(l6e)
                    self.scene1.addItem(l1d)
                    self.scene1.addItem(l2d)
                    self.scene1.addItem(l3d)
                    self.scene1.addItem(l4d)
                    self.scene1.addItem(l5d)
                    self.scene1.addItem(l6d)
                    self.scene1.addItem(l7d)
                    self.scene1.addItem(l8d)

                elif support == '(P-F)':
                    l1e = QGraphicsLineItem(-45, 40,
                                            45, 40)
                    l2e = QGraphicsLineItem(-40, 50,
                                            -30, 40)
                    l3e = QGraphicsLineItem(-25, 50,
                                            -15, 40)
                    l4e = QGraphicsLineItem(-10, 50,
                                            0, 40)
                    l5e = QGraphicsLineItem(5, 50,
                                            15, 40)
                    l6e = QGraphicsLineItem(20, 50,
                                            30, 40)
                    l7e = QGraphicsLineItem(-30, 40,
                                            0, 0)
                    l8e = QGraphicsLineItem(30, 40,
                                            0, 0)
                    l1d = QGraphicsLineItem(-30 + b, 0,
                                            30 + b, 0)
                    l2d = QGraphicsLineItem(-40 + b, 10,
                                            -30 + b, 0)
                    l3d = QGraphicsLineItem(-25 + b, 10,
                                            -15 + b, 0)
                    l4d = QGraphicsLineItem(-10 + b, 10,
                                            0 + b, 0)
                    l5d = QGraphicsLineItem(5 + b, 10,
                                            15 + b, 0)
                    l6d = QGraphicsLineItem(20 + b, 10,
                                            30 + b, 0)

                    l1e.setPen(self.pen4)
                    l2e.setPen(self.pen4)
                    l3e.setPen(self.pen4)
                    l4e.setPen(self.pen4)
                    l5e.setPen(self.pen4)
                    l6e.setPen(self.pen4)
                    l7e.setPen(self.pen4)
                    l8e.setPen(self.pen4)
                    l1d.setPen(self.pen4)
                    l2d.setPen(self.pen4)
                    l3d.setPen(self.pen4)
                    l4d.setPen(self.pen4)
                    l5d.setPen(self.pen4)
                    l6d.setPen(self.pen4)

                    self.scene1.addItem(l1e)
                    self.scene1.addItem(l2e)
                    self.scene1.addItem(l3e)
                    self.scene1.addItem(l4e)
                    self.scene1.addItem(l5e)
                    self.scene1.addItem(l6e)
                    self.scene1.addItem(l7e)
                    self.scene1.addItem(l8e)
                    self.scene1.addItem(l1d)
                    self.scene1.addItem(l2d)
                    self.scene1.addItem(l3d)
                    self.scene1.addItem(l4d)
                    self.scene1.addItem(l5d)
                    self.scene1.addItem(l6d)

                elif support == '(P-P)':
                    l1e = QGraphicsLineItem(-45, 40,
                                            45, 40)
                    l2e = QGraphicsLineItem(-40, 50,
                                            -30, 40)
                    l3e = QGraphicsLineItem(-25, 50,
                                            -15, 40)
                    l4e = QGraphicsLineItem(-10, 50,
                                            0, 40)
                    l5e = QGraphicsLineItem(5, 50,
                                            15, 40)
                    l6e = QGraphicsLineItem(20, 50,
                                            30, 40)
                    l7e = QGraphicsLineItem(-30, 40,
                                            0, 0)
                    l8e = QGraphicsLineItem(30, 40,
                                            0, 0)
                    l1d = QGraphicsLineItem(-45 + b, 40,
                                            45 + b, 40)
                    l2d = QGraphicsLineItem(-40 + b, 50,
                                            -30 + b, 40)
                    l3d = QGraphicsLineItem(-25 + b, 50,
                                            -15 + b, 40)
                    l4d = QGraphicsLineItem(-10 + b, 50,
                                            0 + b, 40)
                    l5d = QGraphicsLineItem(5 + b, 50,
                                            15 + b, 40)
                    l6d = QGraphicsLineItem(20 + b, 50,
                                            30 + b, 40)
                    l7d = QGraphicsLineItem(-30 + b, 40,
                                            0 + b, 0)
                    l8d = QGraphicsLineItem(30 + b, 40,
                                            0 + b, 0)

                    l1e.setPen(self.pen4)
                    l2e.setPen(self.pen4)
                    l3e.setPen(self.pen4)
                    l4e.setPen(self.pen4)
                    l5e.setPen(self.pen4)
                    l6e.setPen(self.pen4)
                    l7e.setPen(self.pen4)
                    l8e.setPen(self.pen4)
                    l1d.setPen(self.pen4)
                    l2d.setPen(self.pen4)
                    l3d.setPen(self.pen4)
                    l4d.setPen(self.pen4)
                    l5d.setPen(self.pen4)
                    l6d.setPen(self.pen4)
                    l7d.setPen(self.pen4)
                    l8d.setPen(self.pen4)

                    self.scene1.addItem(l1e)
                    self.scene1.addItem(l2e)
                    self.scene1.addItem(l3e)
                    self.scene1.addItem(l4e)
                    self.scene1.addItem(l5e)
                    self.scene1.addItem(l6e)
                    self.scene1.addItem(l7e)
                    self.scene1.addItem(l8e)
                    self.scene1.addItem(l1d)
                    self.scene1.addItem(l2d)
                    self.scene1.addItem(l3d)
                    self.scene1.addItem(l4d)
                    self.scene1.addItem(l5d)
                    self.scene1.addItem(l6d)
                    self.scene1.addItem(l7d)
                    self.scene1.addItem(l8d)

            else:
                if support == '(F-F)':
                    pass
                if support == '(F-P)':
                    cd = QGraphicsEllipseItem(b-10, -(level+20+h), 20, 20)
                    cd.setBrush(self.brush2)
                    self.scene1.addItem(cd)
                if support == '(P-F)':
                    ce = QGraphicsEllipseItem(-10, -(level+20+h), 20, 20)
                    ce.setBrush(self.brush2)
                    self.scene1.addItem(ce)
                if support == '(P-P)':
                    ce = QGraphicsEllipseItem(-10, -(level+20+h), 20, 20)
                    ce.setBrush(self.brush2)
                    self.scene1.addItem(ce)
                    cd = QGraphicsEllipseItem(b-10, -(level+20+h), 20, 20)
                    cd.setBrush(self.brush2)
                    self.scene1.addItem(cd)

            level += stories[i].height*100

        # self.setGeometry(0, 0, self.sizeHint().width(), self.sizeHint().height())
        self.setViewportMargins(10, 10, 10, 10)
        self.fitInView(self.scene1.itemsBoundingRect(), Qt.KeepAspectRatio)
