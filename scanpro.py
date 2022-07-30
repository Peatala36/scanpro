import cv2 as cv
import numpy as np
import argparse

from PyQt5.QtWidgets import QListWidgetItem
from PyQt5.QtGui import QImage

import os

#ap = argparse.ArgumentParser()
#ap.add_argument("-i", "--image", required = True, help = "Path to the image to be scanned")

#args = vars(ap.parse_args())

parser=argparse.ArgumentParser()
parser.parse_args()

def manual_processing(path, gray=True, rotate=0):
    # rotate=0: alles belassen, =1: alle auf Hochkant drehen, =2: alle auf Querformat drehen
    # manual_processing(r"/home/toni/Scans/Verkehrsgeographie")
    files = sorted(os.listdir(path))
    x = 0
    for f in files:
        if os.path.isfile(path + "/" + f):
            try:
                img = cv.imread(path + "/" + f)
                print(f + " eingelesen")

                # Bild drehen:
                img = drehen(img)
                print(f + " gedreht")

                # Bild zuschneiden
                img = zuschnitt(img)
                print(f + " zugeschnitten")

                # Bild ausgrauen
                if gray == True:
                    img = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
                    print(f + " gegraut")

                # Bild halbieren
                img1, img2 = teilen(img)

                cv.imwrite(path + r"/Seite_" + str(x) + ".jpg", img1)
                if img2 != []:
                    x+=1
                    cv.imwrite(path + r"/Seite_" + str(x) + ".jpg", img2)
                print(f + " wurde gespeichert")
                x+=1
            except Exception as e:
                print("Fehler bei " + f + ": " + str(e))
    print("Es wurden " + str(x) + " Seiten verarbeitet")
 

def zuschnitt(ir):
    try:
        width = 500
        scale = width / ir.shape[1]
        height = int(ir.shape[0] * scale)
                
        imS = cv.resize(ir, (width, height))
        cv.imshow("Original", imS)
                
        for mode in range(1, 4):
            if mode == 1:
                img1 = img_cut(ir, contrast="thresh", max_cnt="area")
            elif mode == 2:
                img1 = img_cut(ir, contrast="canny", max_cnt="area")
            elif mode == 3:
                img1 = img_cut(ir, contrast="canny", max_cnt="length")

            new_width = int(img1.shape[1] * scale)
            new_height = int(img1.shape[0] * scale)
            img1S = cv.resize(img1, (new_width, new_height))
                    
            cv.imshow("Bearbeitet", img1S)
            while(True):
                k = cv.waitKey(33)
                if k==27: # Esc key to stop
                    exit()
                elif k==13: # Enter key
                    cv.destroyAllWindows()
                    return(img1)
                elif k==83: # Pfeiltaste rechts
                    print("Nächster Modus")
                    break
                elif k==-1:
                    continue
                else:
                    print(k)
    except Exception as e:
        print("Fehler beim Zuschnitt: " + str(e))

def drehen(img):
    try:
        while(True):
            width = 500
            scale = width / img.shape[1]
            height = int(img.shape[0] * scale)
                
            imS = cv.resize(img, (width, height))
            cv.imshow("Drehen?", imS)
            
            k = cv.waitKey(33)
            if k==27: # Esc key to stop
                exit()
            elif k==13: # Enter key
                cv.destroyAllWindows()
                return(img)
            elif k==81: # Pfeiltaste links
                cv.destroyAllWindows()
                img = cv.rotate(img, cv.ROTATE_90_COUNTERCLOCKWISE)
            elif k==83: # Pfeiltaste rechts
                cv.destroyAllWindows()
                img = cv.rotate(img, cv.ROTATE_90_CLOCKWISE)
            elif k==-1:
                continue
            else:
                print(k)
    except Exception as e:
        print("Fehler beim Drehen: " + str(e))

def teilen(img):
    try:
        w = img.shape[1]
        h = img.shape[0]

        img1 = img[0:h, 0:w//2]
        img2 = img[0:h, w//2:w]

        width = 500
        scale1 = width / img1.shape[1]
        height1 = int(img1.shape[0] * scale1)
                
        im1S = cv.resize(img1, (width, height1))
        cv.imshow("Links", im1S)

        scale2 = width / img2.shape[1]
        height2 = int(img1.shape[0] * scale2)
                
        im2S = cv.resize(img2, (width, height2))
        cv.imshow("Rechts", im2S)

        while(True):
            k = cv.waitKey(33)
            if k==27: # Esc key to stop
                exit()
            elif k==13: # Enter key
                cv.destroyAllWindows()
                return(img1, img2)
    except Exception as e:
        print("Fehler beim Teilen: " + str(e))
        

def size(x):
    return x.shape[0] * x.shape[1]



# Klasse für das Handling der Bilder
class img(QListWidgetItem):
    def __init__(self, orgPath, name):
        super(img, self).__init__()
        self.orgPath = orgPath
        self.name = name
        self.setText(name)
        self.img = ""
        self.image_qt = ""
        try:
            self.orgImg = cv.imread(orgPath)
        except:
            print(str(orgPath) + " konnte nicht eingelesen werden.")
        self.setImg(self.orgImg.copy())

    def setImg(self, img):
        
        self.img = img
        
        """Convert from an opencv image to QPixmap"""
        rgb_image = cv.cvtColor(img, cv.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        self.image_qt = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)

    def auto_cut(self, contrast="thresh", max_cnt="area"):
        orig = self.img.copy()

        width = 500
        scale = width / self.img.shape[1]
        height = int(self.img.shape[0] * scale)
        re_img = cv.resize(self.img, (width, height), interpolation = cv.INTER_AREA)

        if len(re_img.shape) > 2:
            imgray = cv.cvtColor(re_img, cv.COLOR_BGR2GRAY)
        else:
            imgray = re_img
            
        if contrast == "thresh":
            _,thresh = cv.threshold(imgray,127,255,0 | cv.THRESH_OTSU)
        elif contrast == "canny":
            imgray = cv.GaussianBlur(imgray, (5, 5), 0)
            thresh = cv.Canny(imgray, 75, 200)
        
        contours,_ = cv.findContours(thresh,cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)

        #orig_r = cv.resize(orig, (width, height), interpolation = cv.INTER_AREA)

        cnt = []
        if max_cnt == "length":
            x=-1
            max_cl = 0
            for c in contours:
                x += 1
                if max_cl < cv.arcLength(c, False):
                    max_cl = cv.arcLength(c, False)
            cnt = contours[x]
        if max_cnt == "area":
            try:
                cnt = max(contours, key=cv.contourArea)
            except:
                return
        
        rect = cv.minAreaRect(cnt)
        box = cv.boxPoints(rect)
        box = np.int0(box)

        self.setImg(self._four_point_transform(orig, box / scale))


    def _order_points(self, pts):
        # initialzie a list of coordinates that will be ordered
        # such that the first entry in the list is the top-left,
        # the second entry is the top-right, the third is the
        # bottom-right, and the fourth is the bottom-left
        rect = np.zeros((4, 2), dtype = "float32")
        # the top-left point will have the smallest sum, whereas
        # the bottom-right point will have the largest sum
        s = pts.sum(axis = 1)
        rect[0] = pts[np.argmin(s)]
        rect[2] = pts[np.argmax(s)]
        # now, compute the difference between the points, the
        # top-right point will have the smallest difference,
        # whereas the bottom-left will have the largest difference
        diff = np.diff(pts, axis = 1)
        rect[1] = pts[np.argmin(diff)]
        rect[3] = pts[np.argmax(diff)]
        # return the ordered coordinates
        return rect

    def _four_point_transform(self, image, pts):
        # obtain a consistent order of the points and unpack them
        # individually
        rect = self._order_points(pts)
        (tl, tr, br, bl) = rect
        # compute the width of the new image, which will be the
        # maximum distance between bottom-right and bottom-left
        # x-coordiates or the top-right and top-left x-coordinates
        widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
        widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
        maxWidth = max(int(widthA), int(widthB))
        # compute the height of the new image, which will be the
        # maximum distance between the top-right and bottom-right
        # y-coordinates or the top-left and bottom-left y-coordinates
        heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
        heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
        maxHeight = max(int(heightA), int(heightB))
        # now that we have the dimensions of the new image, construct
        # the set of destination points to obtain a "birds eye view",
        # (i.e. top-down view) of the image, again specifying points
        # in the top-left, top-right, bottom-right, and bottom-left
        # order
        dst = np.array([
            [0, 0],
            [maxWidth - 1, 0],
            [maxWidth - 1, maxHeight - 1],
            [0, maxHeight - 1]], dtype = "float32")
        # compute the perspective transform matrix and then apply it
        M = cv.getPerspectiveTransform(rect, dst)
        warped = cv.warpPerspective(image, M, (maxWidth, maxHeight))
        # return the warped image
        return warped

    def rotate_90_counterclockwise(self):
        try:
            self.setImg(cv.rotate(self.img, cv.ROTATE_90_COUNTERCLOCKWISE))
        except Exception as e:
            print("Fehler beim Drehen: " + str(e))

    def rotate_90_clockwise(self):
        try:
            self.setImg(cv.rotate(self.img, cv.ROTATE_90_CLOCKWISE))
        except Exception as e:
            print("Fehler beim Drehen: " + str(e))

    def setGray(self):
        try:
            if len(self.img.shape) > 2:
                self.setImg(cv.cvtColor(self.img, cv.COLOR_BGR2GRAY))
        except Exception as e:
            print("Fehler bei Grau: " + str(e))

    def setBlackWhite(self):
        try:
            if len(self.img.shape) > 2:
                grayImage = cv.cvtColor(self.img, cv.COLOR_BGR2GRAY)
            else:
                grayImage = self.img
            _, BlackAndWhiteImage = cv.threshold(grayImage, 128, 255, cv.THRESH_BINARY | cv.THRESH_OTSU)
            self.setImg(BlackAndWhiteImage)
        except Exception as e:
            print("Fehler bei Schwarz/Weiß: " + str(e))

    def manuel_cut(self, rect):
        try:
            c = rect.getCoords()
            self.setImg(self.img[c[0]:c[2], c[1]:c[3]])
            pass
        except Exception as e:
            print("Fehler beim Zuschnitt: " + str(e))

    def retouch(self, rect, gv):
        try:
            scal_x = gv.width() / self.img.shape[1]
            scal_y = gv.height() / self.img.shape[0]
            scal = min(scal_x, scal_y)

            start = gv.mapToScene(rect.topLeft()) / scal
            ende = gv.mapToScene(rect.bottomRight()) / scal

            white = (255, 255, 255)
            mask = np.zeros((self.img.shape[0], self.img.shape[1], 3), np.uint8)
            mask = cv.rectangle(mask, (int(start.x()), int(start.y())), (int(ende.x()), int(ende.y())), white, -1)
            mask = cv.cvtColor(mask, cv.COLOR_BGR2GRAY)
            self.setImg(cv.inpaint(self.img, mask, 10, flags=cv.INPAINT_TELEA))
        except Exception as e:
            print("Fehler beim Retuschieren: " + str(e))
        
    def floodfill(self, seed=(0,0)):
        try:
            flood = self.img.copy()
            cv.floodFill(flood, None, seedPoint=seed, newVal=(255, 255, 255))
            self.setImg(flood)
        except Exception as e:
            print("Fehler beim Füllen: " + str(e))
