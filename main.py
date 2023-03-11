import sys
import os
import os.path
import numpy as np
from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QMainWindow, QGraphicsScene, QFileDialog, QGraphicsPixmapItem, QGraphicsView, QRubberBand, QMessageBox, QApplication
from PyQt5.QtGui import QPixmap, QImage, QPen
import PyQt5.QtCore
from PyQt5.QtCore import Qt, QRect, QPoint
import scanpro
import cv2 as cv
from PIL import Image
import shutil


#  https://specifications.freedesktop.org/icon-naming-spec/latest/ar01s04.html


# Bekannte Probleme:
# - Geteilte Bilder werden nicht gespeichert

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        self.ui = uic.loadUi("main.ui", self)
        #QtCore.QMetaObject.connectSlotsByName(MainWindow)


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        #super().__init__(parent)
        QMainWindow.__init__(self, parent=parent)
        self.setupUi(self)
        
        self.scene = QGraphicsScene()
        self.ui.graphicsView.setScene(self.scene)

        # Buttons
        self.ui.action_oeffnen.triggered.connect(self.openFileDialog)
        self.ui.actionSpeichern.triggered.connect(self.saveFileDialog)
        self.ui.actionUndo.triggered.connect(self.undo)
        self.ui.actionDeletItem.triggered.connect(self.delItem)
        self.ui.actionrefresh.triggered.connect(self.refresh)
        self.ui.actionHoch.triggered.connect(self.listUp)
        self.ui.actionRunter.triggered.connect(self.listDown)
        self.ui.actionLinks_rotieren.triggered.connect(self.leftRotate)
        self.ui.actionRechts_rotieren.triggered.connect(self.rightRotate)
        self.ui.actionZuschnitt_1.triggered.connect(self.zuschnitt_1)
        self.ui.actionZuschnitt_2.triggered.connect(self.zuschnitt_2)
        self.ui.actionZuschnitt_3.triggered.connect(self.zuschnitt_3)
        self.ui.actionBlackWhite.triggered.connect(self.schwarzWeiss)
        self.ui.actionGrau.triggered.connect(self.grau)
        self.ui.actionRetouch.triggered.connect(self.retouch)
        self.ui.actionFuellen.triggered.connect(self.bucketFill)
        self.ui.actionSeiteTeilen.triggered.connect(self.seiteTeilen)
        self.ui.actionAuto.triggered.connect(self.auto)
        self.ui.actionPDF_Export.triggered.connect(self.PDFExport)
        self.ui.actionManueller_Zuschnitt.triggered.connect(self.manuelCut)
        self.ui.actionLineLeft.triggered.connect(self.shiftLineLeft)
        self.ui.actionLineRight.triggered.connect(self.shiftLineRight)

        # Maus
        self.ui.graphicsView.setDragMode(QGraphicsView.RubberBandDrag)
        self.ui.graphicsView.rubberBandChanged.connect(self.rubberBand)
        self.ui.listWidget.itemClicked.connect(self.itemClicked_event)
        

        # Variablen
        self.tempDir = ""
        self.selectedItem = ""
        self.rubberBandArea = QRect()
        self.ui.actionUndo.setDisabled(True)
        self.backupList = list()
        self.pen = QPen(Qt.green, 3, Qt.DashDotLine, Qt.RoundCap, Qt.RoundJoin)
        self.imgFormat = [".jpg", ".png", ".jpeg"]
        

        # Einstellungen
        self.maxBackups = 10

    def openFileDialog(self):
##        files, _ = QFileDialog.getOpenFileNames(self, "Bilder öffnen", "","Image Files (*.png *.jpg)")
        dialog = QFileDialog()
        self.folder = dialog.getExistingDirectory(self, 'Wählen Sie einen Ordner')
        if self.folder != "":
            i = 0
            self.tmpDir = os.path.join(self.folder, "temp")
            
            if not os.path.exists(self.tmpDir):
                os.mkdir(self.tmpDir)
                print("Temporärer Speicherort " + self.tmpDir + " wurde angelegt")

            QApplication.setOverrideCursor(Qt.WaitCursor)
            for file in sorted(os.listdir(self.folder)):
                file = os.path.join(self.folder, file)
                if os.path.isfile(file):
                    head, tail = os.path.split(file)
                    root, ext = os.path.splitext(tail)
                    if ext in self.imgFormat:
                        self.ui.listWidget.addItem(scanpro.img(file, root))
                        if not os.path.exists(os.path.join(self.tmpDir, tail)):
                            shutil.copy(file, self.tmpDir)
                        i += 1
            QApplication.restoreOverrideCursor()
            self.ui.statusbar.showMessage(str(i) + " Dateien wurden gefunden")

    def saveFileDialog(self):
        fileName, _ = QFileDialog.getSaveFileName(self)
        if fileName:
            print(fileName)
            cv.imwrite(fileName, self.selectedItem.img)

    def listUp(self):
        self.listWidget.setCurrentRow(self.listWidget.currentRow() - 1)
        self.refresh()
    
    def listDown(self):
        if self.ui.listWidget.selectedItems():
            self.listWidget.setCurrentRow(self.listWidget.currentRow() + 1)
            self.refresh()
        else:
            self.ui.listWidget.item(0).setSelected(True)

    def delItem(self):
        if self.ui.listWidget.selectedItems():
            if self.yesNo("Soll " + self.selectedItem.text() + " gelöscht werden?"):
                tmpFile = os.path.join(self.tmpDir, self.selectedItem.text() + ".jpg")
                if os.path.exists(tmpFile):
                    os.remove(tmpFile)
                self.ui.listWidget.takeItem(self.listWidget.currentRow())

    def rightRotate(self):
        if self.ui.listWidget.selectedItems():
            self.setBackup(self.selectedItem)
            self.selectedItem.rotate_90_clockwise()
            self.refresh()

    def leftRotate(self):
        if self.ui.listWidget.selectedItems():
            self.setBackup(self.selectedItem)
            self.selectedItem.rotate_90_counterclockwise()
            self.refresh()

    def zuschnitt_1(self):
        if self.ui.listWidget.selectedItems():
            self.setBackup(self.selectedItem)
            self.selectedItem.auto_cut(contrast="thresh", max_cnt="area")
            self.refresh()

    def zuschnitt_2(self):
        if self.ui.listWidget.selectedItems():
            self.setBackup(self.selectedItem)
            self.selectedItem.auto_cut(contrast="canny", max_cnt="area")
            self.refresh()

    def zuschnitt_3(self):
        if self.ui.listWidget.selectedItems():
            self.setBackup(self.selectedItem)
            self.selectedItem.auto_cut(contrast="canny", max_cnt="length")
            self.refresh()

    def grau(self):
        if self.ui.listWidget.selectedItems():
            self.setBackup(self.selectedItem)
            self.selectedItem.setGray()
            self.refresh()

    def schwarzWeiss(self):
        if self.ui.listWidget.selectedItems():
            i = self.selectedItem
            self.setBackup(i)
            i.setBlackWhite()
            h = i.img.shape[0]
            w = i.img.shape[1]
            #i.floodfill((0,0))
            #i.floodfill((0,h-1))
            #i.floodfill((w-1,0))
            #i.floodfill((w-1,h-1))
            self.refresh()
    
    def rubberBand(self, viewportRect, fromScenePoint, toScenePoint):
        if viewportRect != QRect():
            self.rubberBandArea = viewportRect

    def retouch(self):
        if self.rubberBandArea:
            self.setBackup(self.selectedItem)
            self.selectedItem.retouch(self.rubberBandArea, self.ui.graphicsView)
            self.refresh()

    def manuelCut(self):
        if self.rubberBandArea:
            self.setBackup(self.selectedItem)
            scal_x = self.ui.graphicsView.width() / self.selectedItem.img.shape[1]
            scal_y = self.ui.graphicsView.height() / self.selectedItem.img.shape[0]
            scal = min(scal_x, scal_y)

            start = self.ui.graphicsView.mapToScene(self.rubberBandArea.topLeft()) / scal
            ende = self.ui.graphicsView.mapToScene(self.rubberBandArea.bottomRight()) / scal

            r = QRect(int(start.x()), int(start.y()), int(ende.x()-start.x()), int(ende.y()-start.y()))
            self.selectedItem.manuel_cut(r)
            self.refresh()

    def bucketFill(self):
        if self.ui.listWidget.selectedItems():
            self.setBackup(self.selectedItem)
            self.selectedItem.floodfill()
            self.refresh()

    def shiftLineLeft(self):
        self.selectedItem.line_x -= 10
        self.refresh()

    def shiftLineRight(self):
        self.selectedItem.line_x += 10
        self.refresh()

    def seiteTeilen(self):
        if self.ui.listWidget.selectedItems():            
            i1 = self.selectedItem
            i2 = scanpro.img(i1.orgPath, i1.name)
            i2.img = i1.img.copy()
            
            self.setBackup(i1)
            w = i1.img.shape[1]
            h = i1.img.shape[0]
            r1 = QRect(0, 0, i1.line_x, h)
            r2 = QRect(i1.line_x, 0, i1.line_x, h)
            
            i1.manuel_cut(r1)
            i2.manuel_cut(r2)
            i2.setName(i2.name + "_2")

            cur = self.listWidget.currentRow()
            self.ui.listWidget.insertItem(cur+1, i2)
            self.refresh()


    def auto(self):
        if self.ui.listWidget.selectedItems():
            self.setBackup(self.selectedItem)
            self.selectedItem.auto_cut(contrast="thresh", max_cnt="area")
            self.selectedItem.setGray()
            i1 = self.selectedItem
            i2 = scanpro.img(i1.orgPath, i1.name)
            i2.img = i1.img.copy()
            
            self.setBackup(i1)
            w = i1.img.shape[1]
            h = i1.img.shape[0]
            r1 = QRect(0, 0, w//2, h)
            r2 = QRect(w//2, 0, w//2, h)
            
            i1.manuel_cut(r1)
            i2.manuel_cut(r2)
            i2.setName(i2.name + "_2")

            cur = self.listWidget.currentRow()
            self.ui.listWidget.insertItem(cur+1, i2)
            self.refresh()

    def itemClicked_event(self, item):
        pic = QGraphicsPixmapItem()
        self.selectedItem = self.ui.listWidget.selectedItems()[0]
        self.selectedItem.load()
        p = item.image_qt.scaled(self.ui.graphicsView.width(), self.ui.graphicsView.height(), Qt.KeepAspectRatio)
        pic.setPixmap(QPixmap.fromImage(p))
        self.scene.clear()
        self.scene.addItem(pic)

        if len(item.img.shape) == 3:
            row, column, depth = item.img.shape
        elif len(item.img.shape) == 2:
            row, column = item.img.shape
            depth = 1

        is_success, im_buf_arr = cv.imencode(".jpg", item.img)
        byte_im = round(sys.getsizeof(im_buf_arr) / 1024, 2)
        self.ui.statusbar.showMessage(str(column) + "x" + str(row) + " / " + str(byte_im) + " KiB")

    def refresh(self):
        if self.ui.listWidget.selectedItems():
            self.itemClicked_event(self.selectedItem)
            #tmpFile = os.path.join(self.tmpDir, self.ui.listWidget.selectedItems()[0].text() + ".jpg")
            #cv.imwrite(tmpFile, self.ui.listWidget.selectedItems()[0].img)
            cv.imwrite(self.selectedItem.orgPath, self.selectedItem.img)
            self.rubberBandArea = QRect()
            x1 = self.scene.width() * self.selectedItem.getLineXPercentage()
            y2 = self.scene.height()
            line = self.scene.addLine(x1,0,x1,y2,self.pen)
            

    def setBackup(self, img):
        b = backup(img)
        self.backupList.append(b)
        self.ui.actionUndo.setDisabled(False)
        if len(self.backupList) > self.maxBackups:
            del self.backupList[0]

    def undo(self):
        if self.backupList:
            self.backupList[-1].lastImg.setImg(self.backupList[-1].lastImgBackup.copy())
            self.refresh()
            del self.backupList[-1]
            if self.backupList == []:
                self.ui.actionUndo.setDisabled(True)

    def yesNo(self, message):
        qm = QMessageBox()
        return qm.warning(self,'', message, qm.Yes | qm.No)

    def PDFExport(self):
        fileName, _ = QFileDialog.getSaveFileName(self)
        if fileName:
            imgList_converted = list()
            imgList = [self.listWidget.item(i) for i in range(self.listWidget.count())]
            for i in imgList:
                color_coverted = cv.cvtColor(i.img, cv.COLOR_BGR2RGB)
                im_pil = Image.fromarray(color_coverted)
                imgList_converted.append(im_pil)
            im1 = imgList_converted[0]
            del imgList_converted[0]
            im1.save(fileName, save_all=True, append_images=imgList_converted)
            print("PDF fertig konvertiert")
            
        

# Klasse für die Speicherung der Versionsstände die mit Undo rückgängig gemacht werden können
class backup():
    def __init__(self, img):
        self.lastImg = img
        self.lastImgBackup = img.img.copy()


def main():
    app = QtWidgets.QApplication(sys.argv)
    main = MainWindow()
    main.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
