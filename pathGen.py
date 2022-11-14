from tokenize import Number
from PIL import Image
from svgelements import SVG
import numpy as np
import os
import logging
import cv2


# conversions for Points to Pixels
pt2px = 1.333
px2pt = 0.75

# scale factor
scale_factor = 1.15

# Drawing params
drawingWidth = 140 * scale_factor * px2pt     # width in mm
drawingHeight = 140 * scale_factor * px2pt  # height in mm


penDrawingHeight = -1.0 # Drawing height in mm
penLiftHeight = penDrawingHeight + 5.0    # lifted pen height in mm

minCubicLength = 2 # minimum cubic length that will be turned into linear move if smaller

def genSVG(image_name = "snapShot"):
    # generates an svg image from a bitmap image
    logger = logging.getLogger('pathGen')

    # Potrace params
    turdsize = 50       # suppress speckles of up to this many pixels.
    alphamax = 1.2      # The default value  is  1.  The  smaller  this  value,  the more sharp corners will be produced. If this parameter is 0, then no smoothing will be performed and the output is a polygon. If this parameter  is  greater  than  4/3,  then all corners are suppressed and the output is completely smooth.
    opttolerance = 250  #Larger values  allow  more consecutive Bezier curve segments to be joined together in a single segment, at the expense of accuracy.

    logger.info("Generating svg")
    logger.info("TurdSize: {}, AlphaMax: {}, Op: {}".format(turdsize, alphamax, opttolerance))

    # attempt to find edges
    # img = cv2.imread("{}.bmp".format(image_name))
    # edges = cv2.Canny(img,100,200)
    # cv2.imwrite("{}_de.bmp".format(image_name), edges)
    # it wraps around when drawing so no good

    # use mkbitmap
    # os.system("mkbitmap {}.bmp -f 200 -s 2 -t 0.60".format(image_name))

    # im = Image.open("{}.pbm".format(image_name))
    # im.save("{}_de.bmp".format(image_name))

    # Image segmentation using k-closet

    sample_image = cv2.imread("{}.bmp".format(image_name))
    img = cv2.cvtColor(sample_image, cv2.COLOR_BGR2RGB)

    twoDimage = img.reshape((-1,3))
    twoDimage = np.float32(twoDimage)


    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
    K = 2
    attempts=20

    ret, label, center = cv2.kmeans(twoDimage,K,None,criteria,attempts,cv2.KMEANS_PP_CENTERS)
    center = np.uint8(center)
    res = center[label.flatten()]
    result_image = res.reshape((img.shape))

    cv2.imwrite("{}_edit.bmp".format(image_name), result_image)

    # convert bitmap image to svg file
    os.system("potrace --svg {image_name}_edit.bmp -o {image_name}.svg -t {turdsize} -a {alphamax} -O {tolerance}".format(image_name = image_name, turdsize=turdsize, alphamax=alphamax, tolerance=opttolerance))

    logger.info("Generated SVG successfully")


def genCommands(image_name = None, drawHeight = penDrawingHeight, liftHeight = penLiftHeight):
    # Generate path commands (LM, PL, PD, CB) from SVG files
    logger = logging.getLogger('pathGen')
    if image_name is None:
        #genSVG()
        image_name = "snapShot"

    logger.info("Generating Commands")

    # Calculate scaling and offsets needed to fit svg onto drawing platform
    im = Image.open('{}.bmp'.format(image_name))

    logger.info("Loaded Image")

    width, height = im.size         # get image size, used for offsetting...

    width = width * pt2px
    height = height * pt2px

    logger.info("Image Width: {}, Height: {}".format(width, height))

    xScale = drawingWidth/width
    xOffset = width/2

    yScale = drawingHeight/height
    yOffset = height/2

    logger.info("Image xScale: {}, yScale: {}, xOffset: {}, yOffset: {}".format(xScale, yScale, xOffset, yOffset))

    svg = SVG.parse('{}.svg'.format(image_name))
    elements = list(svg.elements())
    paths = elements[0][1]

    logger.info("Parsed SVG")

    logger.info("Paths length: {}".format(len(paths)))

    commands = []

    def translateX(x):
        return round((float(x)- xOffset)*xScale, 2)

    def translateY(y):
        return round((float(y) - yOffset)*yScale, 2)

    lastPos = (0, 0)

    for i in range(len(paths)):
        for path in paths[i]:
            if "M" in str(path): # Lifted move
                line = str(path).split(" ")
                coords = line[1].split(",")

                x = translateX(coords[0])
                y = translateY(coords[1])
                lastPos = (x, y)

                # perform pen lift at current position
                commands.append("JZ {}!".format(liftHeight)) # Lift pen at current location
                commands.append("LM {} {} {}!".format(x, y, liftHeight)) # perform linear move with lifted pen
                commands.append("JZ {}!".format(drawHeight)) # Drop pen at current location

            if "Z" in str(path): # Lifted move
                # perform pen lift at current position
                commands.append("LM {} {} {}!".format(lastPos[0], lastPos[1], drawHeight)) # perform linear move with lifted pen

            if "L" in str(path): # Drawn Line
                line = str(path).split(" ")
                coords = line[3].split(",")
                x = translateX(coords[0])
                y = translateY(coords[1])
                commands.append("LM {} {} {}!".format(x, y, drawHeight)) # perform linear move (pen down)

            if "C" in str(path): # Drawn Line
                line = str(path).split(" ")
                length = path.length()*xScale
                if length < minCubicLength:
                    endP = line[5].split(",")
                    x = translateX(endP[0])
                    y = translateY(endP[1])
                    commands.append("LM {} {} {}!".format(x, y, drawHeight)) # perform linear move (pen down)
                else: 
                    #split into start, c1, c2, end
                    start = line[1].split(",")
                    c1 = line[3].split(",")
                    c2 = line[4].split(",")
                    endP = line[5].split(",")

                    startX = translateX(start[0])
                    startY = translateY(start[1])

                    c1X = translateX(c1[0])
                    c1Y = translateY(c1[1])

                    c2X = translateX(c2[0])
                    c2Y = translateY(c2[1])

                    endX = translateX(endP[0])
                    endY = translateY(endP[1])

                    commands.append("CB {} {} {} {} {} {} {} {} {}!".format(startX, startY, c1X, c1Y, c2X, c2Y, endX, endY, drawHeight)) # perform linear move (lifted pen)


    logger.info("Generated Commands Successfully")

    with open('commands.txt', 'w') as f:
        for line in commands:
            f.write(f"{line}\n")

    logger.info("Wrote Commands to file Successfully")
            
    return commands, len(paths)
        

if __name__ == 'main':
    genSVG()