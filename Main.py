#!/usr/bin/env python
from queue import Empty
import PySimpleGUI as sg
import cv2
import numpy as np
from pathGen import genCommands, setParams

"""
GUI program for the HMI of the delta robot
"""

# need to adjust for image brightness and stuff for better potrace results

def main():
    sg.theme('Black')

    Button1Column = [[sg.Button('Take Picture', size=(10, 1), font='Helvetica 14')],
               [sg.Button('Clear Picture', size=(10, 1), font='Any 14')]]

    Button2Column = [[sg.Button('Draw Picture', size=(10, 1), font='Helvetica 14')],
               [sg.Button('Exit', size=(10, 1), font='Any 14')]]        

    # define the window layout
    layout = [[sg.VPush()], [sg.Column(Button1Column), sg.Image(filename='', key='image'), sg.Column(Button2Column)], [sg.VPush()]]

    # create the window and show it without the plot
    window = sg.Window('Delta Draw',
                       layout, location=(0, 0), no_titlebar=True, element_justification='c').Finalize()

    window.Maximize()

    # ---===--- Event LOOP Read and display frames, operate the GUI --- #
    cap = cv2.VideoCapture(0)
    preview = True
    snapShot = None

    while True:
        event, values = window.read(timeout=20)
        if event == 'Exit' or event == sg.WIN_CLOSED:
            return

        if event == 'Take Picture':
            ret, frame = cap.read()
            cv2.imwrite("snapShot.bmp", frame)
            snapShot = cv2.imencode('.png', frame)[1].tobytes()

        if event == 'Clear Picture':
            snapShot = None

        if event == 'Draw Picture':
            commands = genCommands()
            print(commands)

        if preview:
            ret, frame = cap.read()
            if snapShot == None:
                imgbytes = cv2.imencode('.png', frame)[1].tobytes()  # ditto
                window['image'].update(data=imgbytes)
            else:
                window['image'].update(data=snapShot)
        

if __name__ == "__main__":
    main()