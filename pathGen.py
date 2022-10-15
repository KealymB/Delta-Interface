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

# Drawing params
drawingWidth = 120 * px2pt     # width in mm
drawingHeight = 120 * px2pt  # height in mm

penLiftHeight = 165    # lifted pen height in mm
penDrawingHeight = 160 # Drawing height in mm

def genSVG(image_name = "snapShot"):
    # generates an svg image from a bitmap image

    # Potrace params
    turdsize = 30 # suppress speckles of up to this many pixels.
    alphamax = 1.1 # The default value  is  1.  The  smaller  this  value,  the more sharp corners will be produced. If this parameter is 0, then no smoothing will be performed and the output is a polygon. If this parameter  is  greater  than  4/3,  then all corners are suppressed and the output is completely smooth.
    opttolerance = 100 #Larger values  allow  more consecutive Bezier curve segments to be joined together in a single segment, at the expense of accuracy.

    # attempt to find edges
    # img = cv2.imread("{}.bmp".format(image_name))
    # edges = cv2.Canny(img,100,200)
    # cv2.imwrite("{}_de.bmp".format(image_name), edges)
    # it wraps around when drawing so no good
    # use mkbitmap
    # os.system("mkbitmap {}.bmp -f 200 -s 2 -t 0.60".format(image_name))

    # im = Image.open("{}.pbm".format(image_name))
    # im.save("{}_de.bmp".format(image_name))

    # convert bitmap image to svg file
    os.system("potrace --svg {image_name}.bmp -o {image_name}.svg -t {turdsize} -a {alphamax} -O {tolerance}".format(image_name = image_name, turdsize=turdsize, alphamax=alphamax, tolerance=opttolerance))



def genCommands(image_name = None):
    # Generate path commands (LM, PL, PD, CB) from SVG files
    logger = logging.getLogger('pathGen')
    if image_name is None:
        #genSVG()
        image_name = "snapShot"

    # Calculate scaling and offsets needed to fit svg onto drawing platform
    im = Image.open('{}.bmp'.format(image_name))

    logger.info("Loaded Image")

    width, height = im.size         # get image size, used for offsetting...

    width = width * pt2px
    height = height * pt2px

    logger.info("Image Width: {}, Height: {}".format(width, height))

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


    for i in range(len(paths)):
        for path in paths[i]:
            logger.info(path)
            if "M" in str(path).upper(): # Lifted move
                line = str(path).split(" ")
                coords = line[1].split(",")

                x = translateX(coords[0])
                y = translateY(coords[1])

                # perform pen lift at current position
                commands.append("PL !") # Lift pen at current location
                commands.append("LM {} {} {}!".format(x, y, penLiftHeight)) # perform linear move with lifted pen
                commands.append("PD !") # Drop pen at current location

            if "L" in str(path): # Drawn Line
                line = str(path).split(" ")
                coords = line[3].split(",")
                x = translateX(coords[0])
                y = translateY(coords[1])
                commands.append("LM {} {} {}!".format(x, y, penDrawingHeight)) # perform linear move (lifted pen)

            if "C" in str(path): # Drawn Line
                line = str(path).split(" ")
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

                commands.append("CB {} {} {} {} {} {} {} {}!".format(startX, startY, c1X, c1Y, c2X, c2Y, endX, endY)) # perform linear move (lifted pen)


    logger.info("Generated Commands")

    with open('commands.txt', 'w') as f:
        for line in commands:
            f.write(f"{line}\n")

    logger.info("Wrote Commands")
            
    return commands, len(paths)
        