import sys  # Importing the sys module for system-specific parameters and functions
import os  # Importing the os module for operating system-dependent functionality
import os.path  # Importing os.path module for common pathname manipulations
import numpy as np  # Importing numpy for numerical computing
from PyQt5 import QtWidgets, uic  # Importing necessary classes from PyQt5 for GUI development
from PyQt5.QtWidgets import QMainWindow, QGraphicsScene, QFileDialog, QGraphicsPixmapItem, QGraphicsView, QRubberBand, QMessageBox, QApplication, QDialog  # Importing necessary classes from PyQt5 for GUI widgets
from PyQt5.QtGui import QPixmap, QImage, QPen  # Importing necessary classes from PyQt5 for GUI graphics
import PyQt5.QtCore  # Importing QtCore module from PyQt5
from PyQt5.QtCore import Qt, QRect, QPoint  # Importing necessary classes from PyQt5 for core Qt functionality
import scanpro  # Importing scanpro module
import cv2 as cv  # Importing OpenCV library
from PIL import Image  # Importing Image module from PIL library for image processing
import shutil  # Importing shutil module for high-level file operations


#  https://specifications.freedesktop.org/icon-naming-spec/latest/ar01s04.html


# Bekannte Probleme:
# - Geteilte Bilder werden nicht gespeichert

# Class for the main window UI
class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        self.ui = uic.loadUi("main.ui", self)
        #QtCore.QMetaObject.connectSlotsByName(MainWindow)
        # Connecting slots by object name using QtCore.QMetaObject.connectSlotsByName(MainWindow)

# Class for the PDF dialog UI
class Ui_Pdf(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = uic.loadUi('pdf.ui', self)
        #self.ui.buttonBox.accepted.connect(self.onOk)
        # Connecting accepted signal of the button box to the onOk method

# Class for the progress bar dialog UI
class ProgressDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = uic.loadUi('ProgressDialog.ui', self)
        self.step = 0

# Main window class inheriting from QMainWindow and Ui_MainWindow
class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        #super().__init__(parent)
        # Initializing QMainWindow
        QMainWindow.__init__(self, parent=parent)
        # Setting up the UI from Ui_MainWindow
        self.setupUi(self)

        # Creating a QGraphicsScene and setting it to the graphicsView
        self.scene = QGraphicsScene()
        self.ui.graphicsView.setScene(self.scene)

        # Connecting actions to their respective slots
        self.ui.action_oeffnen.triggered.connect(self.openFileDialog)
        self.ui.actionSpeichern.triggered.connect(self.saveFileDialog)
        self.ui.actionUndo.triggered.connect(self.undo)
        self.ui.actionRestore.triggered.connect(self.restore)
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

        # Setting drag mode to RubberBandDrag and connecting rubberBandChanged signal
        self.ui.graphicsView.setDragMode(QGraphicsView.RubberBandDrag)
        self.ui.graphicsView.rubberBandChanged.connect(self.rubberBand)
        self.ui.listWidget.itemClicked.connect(self.itemClicked_event)
        

        # Initializing variables
        self.folder = ""
        self.tmpDir = ""
        self.selectedItem = ""
        self.rubberBandArea = QRect()
        self.ui.actionUndo.setDisabled(True)
        self.backupList = list()
        self.pen = QPen(Qt.green, 3, Qt.DashDotLine, Qt.RoundCap, Qt.RoundJoin)
        self.imgFormat = [".jpg", ".png", ".jpeg"]
        

        # Setting up settings
        self.maxBackups = 10

    def openFileDialog(self):
        # Method to open file dialog and populate the list widget with images from the selected folder
##        files, _ = QFileDialog.getOpenFileNames(self, "Bilder öffnen", "","Image Files (*.png *.jpg)")
        dialog = QFileDialog()
        self.folder = dialog.getExistingDirectory(self, 'Wählen Sie einen Ordner')
        if self.folder != "":
            i = 0
            self.tmpDir = os.path.join(self.folder, "temp")

            # Create new folder for Backup
            if not os.path.exists(self.tmpDir):
                os.mkdir(self.tmpDir)
                print("Temporärer Speicherort " + self.tmpDir + " wurde angelegt")

            # Show wait cursor
            QApplication.setOverrideCursor(Qt.WaitCursor)

            dlg = ProgressDialog(self)
            dlg.progressBar.setMaximum(len(os.listdir(self.folder)))
            dlg.show()

            for file in sorted(os.listdir(self.folder)):
                file = os.path.join(self.folder, file)
                if os.path.isfile(file):
                    head, tail = os.path.split(file)
                    root, ext = os.path.splitext(tail)
                    if ext in self.imgFormat:
                        # Create new instance of class img and add it to the listWidget
                        self.ui.listWidget.addItem(scanpro.img(file, root))

                        # Copy the image in the backup folder
                        if not os.path.exists(os.path.join(self.tmpDir, tail)):
                            shutil.copy(file, self.tmpDir)

                        i += 1
                        dlg.progressBar.setValue(i)

            dlg.close()
            
            # Show standard cursor
            QApplication.restoreOverrideCursor()

            # Set message in the Statusbar
            self.ui.statusbar.showMessage(str(i) + " Dateien wurden gefunden")

    def saveFileDialog(self):
        # Method to save the selected image
        fileName, _ = QFileDialog.getSaveFileName(self)
        if fileName:
            print(fileName)
            cv.imwrite(fileName, self.selectedItem.img)

    def listUp(self):
        # Method to move the current row up in the list widget
        self.listWidget.setCurrentRow(self.listWidget.currentRow() - 1)
        self.refresh()
    
    def listDown(self):
        # Method to move the current row down in the list widget
        if self.ui.listWidget.selectedItems():
            self.listWidget.setCurrentRow(self.listWidget.currentRow() + 1)
            self.refresh()
        else:
            self.ui.listWidget.item(0).setSelected(True)

    def delItem(self):
        # Method to delete the selected item from the list widget and remove its corresponding file
        if self.ui.listWidget.selectedItems():
            if self.yesNo("Soll " + self.selectedItem.text() + " gelöscht werden?"):
                file = os.path.join(self.folder, self.selectedItem.text() + ".jpg")
                if os.path.exists(file):
                    os.remove(file)
                    self.ui.statusbar.showMessage(file + " wurde gelöscht")
                self.ui.listWidget.takeItem(self.listWidget.currentRow())

    def rightRotate(self):
        # Method to rotate the selected image 90 degrees clockwise
        if self.ui.listWidget.selectedItems():
            self.setBackup(self.selectedItem)
            self.selectedItem.rotate_90_clockwise()
            self.refresh()

    def leftRotate(self):
        # Method to rotate the selected image 90 degrees counterclockwise
        if self.ui.listWidget.selectedItems():
            self.setBackup(self.selectedItem)
            self.selectedItem.rotate_90_counterclockwise()
            self.refresh()

    def zuschnitt_1(self):
        # Method for image cropping option 1
        if self.ui.listWidget.selectedItems():
            self.setBackup(self.selectedItem)
            self.selectedItem.auto_cut(contrast="thresh", max_cnt="area")
            self.refresh()

    def zuschnitt_2(self):
        # Method for image cropping option 2
        if self.ui.listWidget.selectedItems():
            self.setBackup(self.selectedItem)
            self.selectedItem.auto_cut(contrast="canny", max_cnt="area")
            self.refresh()

    def zuschnitt_3(self):
        # Method for image cropping option 3
        if self.ui.listWidget.selectedItems():
            self.setBackup(self.selectedItem)
            self.selectedItem.auto_cut(contrast="canny", max_cnt="length")
            self.refresh()

    def grau(self):
        # Method to convert the selected image to grayscale
        if self.ui.listWidget.selectedItems():
            self.setBackup(self.selectedItem)
            self.selectedItem.setGray()
            self.refresh()

    def schwarzWeiss(self):
        # Method to convert the selected image to black and white
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
        # Method to handle rubber band selection in the graphics view
        if viewportRect != QRect():
            self.rubberBandArea = viewportRect

    def retouch(self):
        # Method for image retouching
        if self.rubberBandArea:
            self.setBackup(self.selectedItem)
            self.selectedItem.retouch(self.rubberBandArea, self.ui.graphicsView)
            self.refresh()

    def manuelCut(self):
        # Method for manual image cropping
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
        # Method for bucket filling
        if self.ui.listWidget.selectedItems():
            self.setBackup(self.selectedItem)
            self.selectedItem.floodfill()
            self.refresh()

    def shiftLineLeft(self):
        # Method to shift the cutting line to the left
        self.selectedItem.line_x -= 10
        self.refresh()

    def shiftLineRight(self):
        # Method to shift the cutting line to the right
        self.selectedItem.line_x += 10
        self.refresh()

    def seiteTeilen(self):
        # Method to split the page
##        if self.ui.listWidget.selectedItems():            
##            i1 = self.selectedItem
##            i2 = scanpro.img(i1.orgPath, i1.name)
##            i2.img = i1.img.copy()
##            
##            self.setBackup(i1)
##            w = i1.img.shape[1]
##            h = i1.img.shape[0]
##            r1 = QRect(0, 0, i1.line_x, h)
##            r2 = QRect(i1.line_x, 0, i1.line_x, h)
##            
##            i1.manuel_cut(r1)
##            i2.manuel_cut(r2)
##            i2.setName(i2.name + "_2")
##
##            cur = self.listWidget.currentRow()
##            self.ui.listWidget.insertItem(cur+1, i2)
        self.refresh()


    def auto(self):
        # Method for automatic image processing
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
        # Method to handle item clicked event
        self.selectedItem = item
        
        # (Re)load image from the file system
        item.load()

        # Clean graphicView
        self.scene.clear()
        
        # Convert image to QGraphicsPixmapItem
        item.covert2qt()
        p = item.image_qt.scaled(self.ui.graphicsView.width(), self.ui.graphicsView.height(), Qt.KeepAspectRatio)
        pic = QGraphicsPixmapItem()
        pic.setPixmap(QPixmap.fromImage(p))
        self.scene.addItem(pic)

        # Calculate size of the image in byte
        if len(item.img.shape) == 3:
            row, column, depth = item.img.shape
        elif len(item.img.shape) == 2:
            row, column = item.img.shape
            depth = 1

        is_success, im_buf_arr = cv.imencode(".jpg", item.img)
        byte_im = round(sys.getsizeof(im_buf_arr) / 1024, 2)

        # Show calculated size of the image in byte in the status bar
        self.ui.statusbar.showMessage(str(column) + "x" + str(row) + " / " + str(byte_im) + " KiB")

    def refresh(self):
        # Method to refresh the UI
        if self.ui.listWidget.selectedItems():
            # Manuel call of the itemClicked_event:
            self.itemClicked_event(self.selectedItem)
            #tmpFile = os.path.join(self.tmpDir, self.ui.listWidget.selectedItems()[0].text() + ".jpg")
            #cv.imwrite(tmpFile, self.ui.listWidget.selectedItems()[0].img)
            
            cv.imwrite(self.selectedItem.orgPath, self.selectedItem.img)
            self.rubberBandArea = QRect()
            x1 = self.scene.width() * self.selectedItem.getLineXPercentage()
            y2 = self.scene.height()
            line = self.scene.addLine(x1,0,x1,y2,self.pen)
            

    def setBackup(self, img):
        # Method to set a backup for undo operation
        b = backup(img)
        self.backupList.append(b)
        self.ui.actionUndo.setDisabled(False)
        if len(self.backupList) > self.maxBackups:
            del self.backupList[0]

    def undo(self):
        # Method to perform undo operation
        if self.backupList:
            self.backupList[-1].lastImg.setImg(self.backupList[-1].lastImgBackup.copy())
            self.refresh()
            del self.backupList[-1]
            if self.backupList == []:
                self.ui.actionUndo.setDisabled(True)

    def restore(self):
        # method to restore the original image from the tmp folder
        if self.ui.listWidget.selectedItems():
            tmpFile = os.path.join(self.tmpDir, self.selectedItem.name + ".jpg")
            if os.path.exists(tmpFile):
                shutil.copy(tmpFile, self.folder)
                #self.refresh()
            

    def yesNo(self, message):
        # Method to display a yes/no message box
        qm = QMessageBox()
        return qm.warning(self,'', message, qm.Yes | qm.No)

    def PDFExport(self):
        # Method to export images to PDF format
        dlg = Ui_Pdf(self)
        dlg.show()
        if dlg.exec_():
            dpi = int(dlg.dpi.currentText())
            
            if dlg.format.currentText() == "A3":
                x_s, y_s = 11.7, 16.5
            elif dlg.format.currentText() == "A4":
                x_s, y_s = 8.27, 11.7
            elif dlg.format.currentText() == "A5":
                x_s, y_s = 5.3, 8.27
            
            if dlg.quer.isChecked():
                size = (int(y_s*dpi), int(x_s*dpi))
            else:
                size = (int(x_s*dpi), int(y_s*dpi))
            
            fileName, _ = QFileDialog.getSaveFileName(self)            
        
            if fileName:
                imgList_converted = list()
                imgDict = dict()
                imNpArray = np.zeros(self.listWidget.count())
                print(len(imNpArray))
                imgList = [self.listWidget.item(i) for i in range(self.listWidget.count())]
                print(imgList)
                print(str(len(imgList)) + " Elemente wurden gefunden.")
                x = 0
                for i in imgList:
                    i.load()
                    print(i.name)
                    color_coverted = cv.cvtColor(i.img, cv.COLOR_BGR2RGB)
                    im_pil = Image.fromarray(color_coverted)
                    scale_x = im_pil.size[0] / size[0]
                    scale_y = im_pil.size[1] / size[1]
                    if scale_x<scale_y:
                        scale = scale_y
                    else:
                        scale = scale_x
                    size_new = (int(im_pil.size[0]/scale), int(im_pil.size[1]/scale))
                    im_pil=im_pil.resize(size_new)
                    a4im = Image.new('RGB', size, (255,255,255))
                    a4im.paste(im_pil, im_pil.getbbox())
                    #imgList_converted.append(a4im)
                    #imgDict[i.name] = a4im
                    imNpArray[x] = a4im
                    del i
                    x += 1
                im1 = imgList_converted[0]
                del imgList_converted[0]
                im1.save(fileName, save_all=True, append_images=imgList_converted, resolution=dpi)
                print("PDF fertig konvertiert")
            




# Class for storing backup versions for undo operation
class backup():
    def __init__(self, img):
        self.lastImg = img
        self.lastImgBackup = img.img.copy()

# Main function to run the application
def main():
    app = QtWidgets.QApplication(sys.argv)
    main = MainWindow()
    main.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
