from PIL import Image
from svgelements import SVG
import numpy as np
import os

# Drawing params
drawingWidth = 100      # width in mm
drawingHeight = 100     # height in mm

penLiftHeight = 165     # lifted pen height in mm
penDrawingHeight = 160  # Drawing height in mm

def genSVG(image_name = "snapShot"):
    # generates an svg image from a bitmap image

    # Potrace params
    turdsize = 10 # suppress speckles of up to this many pixels.
    alphamax = 1.1 # The default value  is  1.  The  smaller  this  value,  the more sharp corners will be produced. If this parameter is 0, then no smoothing will be performed and the output is a polygon. If this parameter  is  greater  than  4/3,  then all corners are suppressed and the output is completely smooth.
    opttolerance = 1 #Larger values  allow  more consecutive Bezier curve segments to be joined together in a single segment, at the expense of accuracy.

    # convert bitmap image to svg file
    os.system("potrace --svg {image_name}.bmp -o {image_name}.svg -t {turdsize} -a {alphamax} -O {tolerance}".format(image_name = image_name, turdsize=turdsize, alphamax=alphamax, tolerance=opttolerance))



def genCommands(image_name = None):
    # Generate path commands (LM, PL, PD, CB) from SVG files
    if image_name is None:
        #genSVG()
        image_name = "snapShot"

    # Calculate scaling and offsets needed to fit svg onto drawing platform
    im = Image.open('{}.bmp'.format(image_name))
    width, height = im.size         # get image size, used for offsetting...

    xScale = drawingWidth/width
    xOffset = drawingWidth/2

    yScale = drawingHeight/height
    yOffset = drawingHeight/2

    svg = SVG.parse('{}.svg'.format(image_name))
    elements = list(svg.elements())
    paths = elements[0][1]

    commands = []

    for i in range(len(paths)):
        for path in paths[i]:
            if "M" in str(path): # Lifted move
                line = str(path).split(" ")
                coords = line[1].split(",")

                x = round(float(coords[0])*xScale - xOffset, 2)
                y = round(float(coords[1])*yScale - yOffset, 2)

                # perform pen lift at current position
                commands.append("PL !") # Lift pen at current location
                commands.append("LM {} {} {}!".format(x, y, penLiftHeight)) # perform linear move with lifted pen
                commands.append("PD !") # Drop pen at current location

            if "L" in str(path): # Drawn Line
                line = str(path).split(" ")
                coords = line[3].split(",")
                x = round(float(coords[0])*xScale - xOffset, 2)
                y = round(float(coords[1])*yScale - yOffset, 2)
                commands.append("LM {} {} {}!".format(x, y, penDrawingHeight)) # perform linear move (lifted pen)

            if "C" in str(path): # Drawn Line
                line = str(path).split(" ")
                #split into start, c1, c2, end
                start = line[1].split(",")
                c1 = line[3].split(",")
                c2 = line[4].split(",")
                endP = line[5].split(",")

                startX = round(float(start[0])*xScale - xOffset, 2)
                startY = round(float(start[1])*yScale - yOffset, 2)

                c1X = round(float(c1[0])*xScale - xOffset, 2)
                c1Y = round(float(c1[1])*yScale - yOffset, 2)

                c2X = round(float(c2[0])*xScale - xOffset, 2)
                c2Y = round(float(c2[1])*yScale - yOffset, 2)

                endX = round(float(endP[0])*xScale - xOffset, 2)
                endY = round(float(endP[1])*yScale - yOffset, 2)

                commands.append("CB {} {} {} {} {} {} {} {}!".format(startX, startY, c1X, c1Y, c2X, c2Y, endX, endY)) # perform linear move (lifted pen)

    with open('commands.txt', 'w') as f:
        for line in commands:
            f.write(f"{line}\n")
            
    return commands, len(paths)
        