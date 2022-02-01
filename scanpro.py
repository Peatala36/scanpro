import cv2 as cv
import numpy as np
import argparse

import os

#ap = argparse.ArgumentParser()
#ap.add_argument("-i", "--image", required = True, help = "Path to the image to be scanned")

#args = vars(ap.parse_args())

import argparse
parser=argparse.ArgumentParser()
parser.parse_args()

def staple_processing(path, gray=True, contrast="thresh"):
    files = sorted(os.listdir(path))
    x = 0
    for f in files:
        if os.path.isfile(path + "/" + f):
            try:
                if True:
                    ir = cv.imread(path + "/" + f)
                    s = size(ir)
                    img1 = cut_image(ir, contrast="thresh", max_cnt="area")
                    #img2 = cut_image(ir, contrast="thresh", max_cnt="length")
                    img3 = cut_image(ir, contrast="canny", max_cnt="area")
                    img4 = cut_image(ir, contrast="canny", max_cnt="length")

                    if size(img1) == s:
                        img1 = []

                    if size(img3) == s:
                        img3 = []

                    if size(img4) == s:
                        img4 = []

                    img = max([img1, img3, img4], key=size)
    
                if gray == True:
                    img = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
                cv.imwrite(path + r"/Seite_" + str(x) + ".jpg", img)
                x+=1
            except Exception as e:
                print("Fehler bei " + f + ": " + str(e))
    print("Es wurden " + str(x) + " Seiten verarbeitet")

def size(x):
    return x.shape[0] * x.shape[1]

def cut_image(img, contrast="thresh", max_cnt="area"):
    orig = img.copy()

    width = 500
    scale = width / img.shape[1]
    height = int(img.shape[0] * scale)
    img = cv.resize(img, (width, height), interpolation = cv.INTER_AREA)

    imgray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    if contrast == "thresh":
        _,thresh = cv.threshold(imgray,127,255,0)
    if contrast == "canny":
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

    warped = four_point_transform(orig, box / scale)

    return warped

def order_points(pts):
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

def four_point_transform(image, pts):
    # obtain a consistent order of the points and unpack them
    # individually
    rect = order_points(pts)
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


#staple_processing(r"/home/toni/Scans/Verkehrsgeographie", gray=True, contrast="canny")

def test():
    r = cut_image(cv.imread(r"/home/toni/Scans/Verkehrsgeographie/20211128_114300.jpg"), "canny", "area")
    #cv.imwrite(r"/home/toni/Scans/Verkehrsgeographie/test.jpg", r)
    print(size(r))
    width = 500
    scale = width / r.shape[1]
    height = int(r.shape[0] * scale)
    r = cv.resize(r, (width, height), interpolation = cv.INTER_AREA)
    cv.imshow("Test", r)
    cv.waitKey(0)
    cv.destroyAllWindows()
