import cv2
from svgpathtools import svg2paths2, wsvg, Path, Line, CubicBezier
from svgelements import SVG
from reportlab.graphics import renderPM
from svglib.svglib import svg2rlg

# def renderProgress(progress, imgSize):
paths, attributes, svg_attributes = svg2paths2('snapShot.svg')

svg = SVG.parse('snapShot.svg')
elements = list(svg.elements())
paths = elements[0][1]

previewPath = []
segments = Path()
prevIndex = 0

for i in range(len(paths)):
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

wsvg(previewPath, filename='progress.svg')

drawing = svg2rlg("progress.svg")

renderPM.drawToFile(drawing, "progress.png", fmt="PNG")