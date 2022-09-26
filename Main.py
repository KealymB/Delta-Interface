from PIL import Image
import PySimpleGUI as sg
import cv2
import numpy as np
from enum import Enum
from pathGen import genCommands, setParams
from serialComs import readComs, handleComs
from svg2png import renderProgress
from bgRemover import removeBG

"""
GUI program for the HMI of the delta robot
"""

# TODO: need to adjust for image brightness and stuff for better potrace results

def Button(img, event, visible=True):
    return sg.Button('', image_filename="GUI_Elements\{}.png".format(img), key=event, button_color=('black'), border_width=0, visible=visible)

def Img2Byte(imgPath):
    img = cv2.imread(imgPath)
    imgbytes = cv2.imencode('.png', img)[1].tobytes()
    return imgbytes

def main():
    # Params
    imgSize = (450, 450)

    sg.theme('Black')

    input_bar = sg.Column([[Button("B_Capture", "Capture")], [Button("B_Draw", "Draw", False)], [Button("B_Clear", "Clear", False)]])

    # define the window layout
    layout = [[input_bar, sg.Column([[sg.Image(size=imgSize, filename='', key='image')]]), sg.Column([[Button("B_Exit", "Exit")]], vertical_alignment='t')]]

    # create the window and show it without the plot
    window = sg.Window('Delta Draw',
                       layout, location=(0, 0), no_titlebar=False, element_justification='c', size=(800, 480), keep_on_top=True).Finalize()

    #window.Maximize()

    # --- Event Loop --- #
    cap = cv2.VideoCapture(0)
    preview = True
    snapShot = None
    commands = [] # Command buffer for path commands
    index = 0     # Current position in command buffer
    numPaths = 0
    States = Enum('State', 'HOMING IDLE PREVIEW DRAWING ERROR')
    State = States.IDLE

    while True:
        # Serial Handling
        readComs()

        # Instruction Handling
        if len(commands) > 0:
            if handleComs(commands[index]) > 0: # if it is a new instruction and a move has been competed, send next command
                index += 1

        # GUI Handling
        event, values = window.read(timeout=20)
        if event == 'Exit' or event == sg.WIN_CLOSED:
            return

        if event == 'Capture' and State != States.HOMING:
            ret, frame = cap.read()
            croped_img = frame[0:imgSize[0], 0:imgSize[1]]
            cv2.imwrite("snapShot.bmp", croped_img)
            removeBG(imgSize)
            commands, totalPaths = genCommands()
            renderProgress(totalPaths, imgSize)
            snapShot = Img2Byte("progress.png")
            State = States.PREVIEW

        if event == 'Clear':
            window['Capture'].update(visible = True)             # show capture button
            window['Draw'].update(visible = False)               # hide draw button
            window['Clear'].update(visible = False)              # hide clear button
            State = States.IDLE

        if event == 'Draw':
            print(commands)
            State = States.DRAWING

        if State == States.HOMING:
            window['image'].update(data=Img2Byte("GUI_Elements/homing.png"), size=imgSize)

        if State == States.PREVIEW:
            window['Capture'].update(visible = False)           # hide capture button
            window['Draw'].update(visible = True)               # show draw button
            window['Clear'].update(visible = True)              # show clear button
            window['image'].update(data=snapShot, size=imgSize) # show the final image

        if State == States.IDLE:
            ret, frame = cap.read()
            croped_img = frame[0:imgSize[0], 0:imgSize[1]]
            imgbytes = cv2.imencode('.png', croped_img)[1].tobytes()
            window['image'].update(data=imgbytes, size=imgSize)
        

if __name__ == "__main__":
    main()