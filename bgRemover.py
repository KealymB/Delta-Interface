import cv2
from cvzone.SelfiSegmentationModule import SelfiSegmentation

def removeBG(size=(600, 600)):
    seg = SelfiSegmentation()
    bg = cv2.imread("white.bmp")     # background image
    bg = cv2.resize(bg, size)        #resize to size of webcam
    
    img = cv2.imread("snapShot.bmp") # Snapshot
    imgout = seg.removeBG(img, bg)
    
    cv2.imwrite("snapShot.bmp", imgout)