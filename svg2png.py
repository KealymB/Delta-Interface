import cv2
from svgpathtools import svg2paths2, wsvg, Path, Line, CubicBezier
from svgelements import SVG
from reportlab.graphics import renderPM
from svglib.svglib import svg2rlg
import logging

def renderProgress(imgSize, img_name = "snapShot.svg", progress = None):
    # Generates progress image from svg
    logger = logging.getLogger('gen')
    logger.info("Generating Progress Image")
    paths, attributes, svg_attributes = svg2paths2(img_name)
    logger.info("Loaded Paths")

    svg = SVG.parse(img_name)
    elements = list(svg.elements())
    paths = elements[0][1]

    if progress is None:
        progress = len(elements[0])

    previewPath = []
    segments = Path()
    prevIndex = 0

    if len(elements[0]) <= 2:
        initX = 0
        initY = 0
        for path in paths[0]:
            # if "L" in str(path): # Drawn Line
            #     line = str(path).split(" ")
                
            #     startCoords = line[1].split(",")
            #     endCoords = line[3].split(",")

            #     startX = float(startCoords[0])
            #     startY = float(startCoords[1])

            #     endX = float(endCoords[0])
            #     endY = float(endCoords[0])
            #     initX = endX
            #     initY = initY
            #     segments.append(Line(complex(startX, startY), complex(endX, endY)))

            if "C" in str(path): # Drawn Line
                line = str(path).split(" ")
                #split into start, c1, c2, end
                start = line[1].split(",")
                c1 = line[3].split(",")
                c2 = line[4].split(",")
                endP = line[5].split(",")

                startX = float(start[0])
                startY = float(start[1])

                c1X = float(c1[0])
                c1Y = float(c1[1])

                c2X = float(c2[0])
                c2Y = float(c2[1])

                endX = float(endP[0])
                endY = float(endP[1])
                
                segments.append(CubicBezier(complex(startX, startY), complex(c1X, c1Y), complex(c2X, c2Y), complex(endX, endY)))

            previewPath.append(segments)

    else: 
        for i in range(progress):
            initX = 0
            initY = 0
            for path in paths[i]:
                # if "L" in str(path): # Drawn Line
                #     line = str(path).split(" ")
                    
                #     startCoords = line[1].split(",")
                #     endCoords = line[3].split(",")

                #     startX = float(startCoords[0])
                #     startY = float(startCoords[1])

                #     endX = float(endCoords[0])
                #     endY = float(endCoords[0])
                #     initX = endX
                #     initY = initY
                #     segments.append(Line(complex(startX, startY), complex(endX, endY)))

                if "C" in str(path): # Drawn Line
                    line = str(path).split(" ")
                    #split into start, c1, c2, end
                    start = line[1].split(",")
                    c1 = line[3].split(",")
                    c2 = line[4].split(",")
                    endP = line[5].split(",")

                    startX = float(start[0])
                    startY = float(start[1])

                    c1X = float(c1[0])
                    c1Y = float(c1[1])

                    c2X = float(c2[0])
                    c2Y = float(c2[1])

                    endX = float(endP[0])
                    endY = float(endP[1])
                    
                    segments.append(CubicBezier(complex(startX, startY), complex(c1X, c1Y), complex(c2X, c2Y), complex(endX, endY)))


                if prevIndex != i:
                    previewPath.append(segments)
                    segments = Path()

                prevIndex = i

    logger.info("Generated Preview paths")

    wsvg(previewPath, filename='progress.svg')

    logger.info("Saved to progress.svg")

    drawing = svg2rlg("progress.svg")

    renderPM.drawToFile(drawing, "progress.png", fmt="PNG")

    logger.info("Drawn to progress.png")
    
    img = cv2.imread("progress.png")
    imgSize = (450, 450)
    img_resized = cv2.resize(img, imgSize)
    cv2.imwrite("progress.png", img_resized)

    logger.info("Resized image")
