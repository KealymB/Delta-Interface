import cv2
import cvzone
from cvzone.SelfiSegmentationModule import SelfiSegmentation

def removeBG(size=(450, 450)):
    seg = SelfiSegmentation()
    bg = cv2.imread("white.bmp")     # background image
    bg = cv2.resize(bg, size)        #resize to size of webcam
    
    img = cv2.imread("snapShot.bmp") # Snapshot
    imgout = seg.removeBG(img, bg)
    
    cv2.imwrite("snapShot.bmp", imgout)