import sys
import numpy as np
from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QGraphicsScene, QFileDialog, QGraphicsPixmapItem, QGraphicsView, QRubberBand
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt, QRect, QPoint
import os.path
import scanpro
import cv2 as cv


# https://specifications.freedesktop.org/icon-naming-spec/latest/ar01s04.html

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = uic.loadUi("main.ui", self)
        
        self.ui.action_oeffnen.triggered.connect(self.openFileDialog)
        self.ui.actionSpeichern.triggered.connect(self.saveFileDialog)
        self.ui.actionUndo.triggered.connect(self.undo)
        self.ui.actionrefresh.triggered.connect(self.refresh)
        self.ui.actionLinks_rotieren.triggered.connect(self.leftRotate)
        self.ui.actionRechts_rotieren.triggered.connect(self.rightRotate)
        self.ui.actionZuschnitt_1.triggered.connect(self.zuschnitt_1)
        self.ui.actionZuschnitt_2.triggered.connect(self.zuschnitt_2)
        self.ui.actionZuschnitt_3.triggered.connect(self.zuschnitt_3)
        self.ui.actionBlackWhite.triggered.connect(self.schwarzWeiss)
        self.ui.actionGrau.triggered.connect(self.grau)
        self.ui.actionRetouch.triggered.connect(self.retouch)
        

        #self.ui.graphicsView.setDragMode(QGraphicsView.RubberBandDrag)
        self.ui.graphicsView.rubberBandChanged.connect(self.rubberBand)
        
        self.ui.listWidget.itemClicked.connect(self.itemClicked_event)

        self.scene = QGraphicsScene()
        self.ui.graphicsView.setScene(self.scene)

        self.retouchMode = False
        self.rubberBandArea = QRect()
        
        self.lastImg = ""
        self.lastImgBackup = ""

    def openFileDialog(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Bilder öffnen", "","Image Files (*.png *.jpg)")
        if files:
            for f in files:
                head, tail = os.path.split(f)
                i = scanpro.img(f, tail)
                self.ui.listWidget.addItem(i)

    def saveFileDialog(self):
        fileName, _ = QFileDialog.getSaveFileName(self)
        if fileName:
            print(fileName)

    def rightRotate(self):
        if self.ui.listWidget.selectedItems():
            self.setBackup(self.ui.listWidget.selectedItems()[0])
            self.ui.listWidget.selectedItems()[0].rotate_90_clockwise()
            self.refresh()

    def leftRotate(self):
        if self.ui.listWidget.selectedItems():
            self.setBackup(self.ui.listWidget.selectedItems()[0])
            self.ui.listWidget.selectedItems()[0].rotate_90_counterclockwise()
            self.refresh()

    def zuschnitt_1(self):
        if self.ui.listWidget.selectedItems():
            self.setBackup(self.ui.listWidget.selectedItems()[0])
            self.ui.listWidget.selectedItems()[0].auto_cut(contrast="thresh", max_cnt="area")
            self.refresh()

    def zuschnitt_2(self):
        if self.ui.listWidget.selectedItems():
            self.setBackup(self.ui.listWidget.selectedItems()[0])
            self.ui.listWidget.selectedItems()[0].auto_cut(contrast="canny", max_cnt="area")
            self.refresh()

    def zuschnitt_3(self):
        if self.ui.listWidget.selectedItems():
            self.setBackup(self.ui.listWidget.selectedItems()[0])
            self.ui.listWidget.selectedItems()[0].auto_cut(contrast="canny", max_cnt="length")
            self.refresh()

    def grau(self):
        if self.ui.listWidget.selectedItems():
            self.setBackup(self.ui.listWidget.selectedItems()[0])
            self.ui.listWidget.selectedItems()[0].setGray()
            self.refresh()

    def schwarzWeiss(self):
        if self.ui.listWidget.selectedItems():
            self.setBackup(self.ui.listWidget.selectedItems()[0])
            self.ui.listWidget.selectedItems()[0].setBlackWhite()
            self.refresh()

    def itemClicked_event(self, item):
        pic = QGraphicsPixmapItem()
        p = item.image_qt.scaled(self.ui.graphicsView.width(), self.ui.graphicsView.height(), Qt.KeepAspectRatio)
        pic.setPixmap(QPixmap.fromImage(p))
        self.scene.clear()
        self.scene.addItem(pic)

    def refresh(self):
        if self.ui.listWidget.selectedItems():
            self.itemClicked_event(self.ui.listWidget.selectedItems()[0])

    def setBackup(self, img):
        self.lastImg = img
        self.lastImgBackup = img.img.copy()

    def undo(self):
        self.lastImg.setImg(self.lastImgBackup.copy())
        self.refresh()

    def retouch(self):
        if self.retouchMode == False:
            self.retouchMode = True
            self.ui.graphicsView.setDragMode(QGraphicsView.RubberBandDrag)
        else:
            self.retouchMode = False
            self.ui.graphicsView.setDragMode(QGraphicsView.NoDrag)
            
    def rubberBand(self, viewportRect, fromScenePoint, toScenePoint):
        if viewportRect == QRect():
            mask = np.zeros((self.ui.listWidget.selectedItems()[0].img.shape[0],self.ui.listWidget.selectedItems()[0].img.shape[1],3), np.uint8)

            scal_x = self.ui.graphicsView.width() / self.ui.listWidget.selectedItems()[0].img.shape[1]
            scal_y = self.ui.graphicsView.height() / self.ui.listWidget.selectedItems()[0].img.shape[0]
            scal = min(scal_x, scal_y)

            start = self.ui.graphicsView.mapToScene(self.rubberBandArea.topLeft())/scal
            ende = self.ui.graphicsView.mapToScene(self.rubberBandArea.bottomRight())/scal

            white = (255, 255, 255)
            mask = cv.rectangle(mask, (int(start.x()), int(start.y())), (int(ende.x()), int(ende.y())), white, -1)
            mask = cv.cvtColor(mask, cv.COLOR_BGR2GRAY)

            output = cv.inpaint(self.ui.listWidget.selectedItems()[0].img, mask, 3, flags=cv.INPAINT_TELEA)
            cv.imwrite("/home/toni/git/output2.jpg", output)
        else:
            self.rubberBandArea = viewportRect


def main():
    app = QtWidgets.QApplication(sys.argv)
    main = MainWindow()
    main.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
