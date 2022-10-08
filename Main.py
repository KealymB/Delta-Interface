import queue
import logging
import threading
import time
from tracemalloc import Snapshot
from PIL import Image
import PySimpleGUI as sg
import cv2
import numpy as np
from enum import Enum
from pathGen import genSVG, genCommands
from serialComs import readComs, writeComs, setupComs
from svg2png import renderProgress
from bgRemover import removeBG
from imgAdjuster import automatic_brightness_and_contrast

"""
GUI program for the HMI of the delta robot
"""
def main(logger):
    logger.info("Init")

    gui_queue = queue.Queue()  # queue used to communicate between the gui and long-running code

    # Params
    imgSize = (450, 450)
    windowSize = (800, 480)

    # GUI Theme
    sg.theme('Black')

    # define the window layout
    input_bar = sg.Column([[Button("B_Capture", "Capture", False)], [Button("B_Draw", "Draw", False)], [Button("B_Cancel", "Cancel", False)], [Button("B_Clear", "Clear", False)], [Button("B_Setup", "Setup", True)]])
    layout = [[input_bar, sg.pin(sg.Image(size=imgSize, filename='', key='image', visible=False)), sg.pin(sg.Output(size=(60, 30), key='Debug', visible=False)), sg.vtop(sg.Column([[Button("B_Exit", "Exit")],  [sg.ProgressBar(max_value=100, orientation='v', size=(20, 20), key='drawing_progress', visible=False)]], element_justification="c"))]]

    # create the window and show it without the plot
    window = sg.Window('Delta Draw',
                       layout, location=(0, 0), no_titlebar=False, element_justification='c', size=windowSize, keep_on_top=True).Finalize()

    window.Maximize()

    logger.info("GUI Setup complete")

    # --- Setup of params --- #

    global snapShot, commands, index
    work_id = 0
    cap = cv2.VideoCapture(0)
    preview = True
    snapShot = None
    commands = []           # Command buffer for path commands
    index = 0               # Current position in command buffer
    numPaths = 0
    States = Enum('State', 'SETUP IDLE PREVIEW DRAWING ERROR')
    State = States.IDLE    # Set initial state
    homed = False           # Flag of if the motors have been homed
    ready = False           # Flag if motors are currently moving test

    setupComs()             # Init coms module

    # --- Event Loop --- #
    while True:
        # Serial Handling
        comBuffer = readComs()
        if comBuffer == -1:
            logger.error("Error returned from com read: {}".format(comBuffer))
            State = States.ERROR
        if comBuffer == 1:
            ready = True
        if comBuffer == 2:
            window['Capture'].update(visible = True)
            window['Setup'].update(visible = False)
            window['Debug'].update(visible = False)
            window['Exit'].update(visible = True)
            State = States.IDLE
            homed = True
            ready = True

        # GUI Handling
        event, values = window.read(timeout=100)
        if event == 'Exit' or event == sg.WIN_CLOSED:
            return

        if event == 'Capture':
            logger.info("Capture Pressed")

            ret, frame = cap.read() # Read web cam

            thread_id = threading.Thread(target=generatePreview, args=(work_id, gui_queue, frame, imgSize), daemon=True) # Start Loader
            thread_id.start()
            work_id = work_id + 1 if work_id < 19 else 0
            
            State = States.PREVIEW

        if event == 'Cancel':
            logger.info("Cancel Pressed")

            Snapshot = None
            commands = []
            window['drawing_progress'].update(visible=False)
            window['Draw'].update(visible = False)               # hide draw button
            window['Clear'].update(visible = False)              # hide clear button
            window['Cancel'].update(visible = False)             # hide cancel button

            State = States.IDLE

        if event == 'Clear':
            logger.info("Clear Pressed")
            window['Capture'].update(visible = True)             # show capture button
            window['Draw'].update(visible = False)               # hide draw button
            window['Clear'].update(visible = False)              # hide clear button
            window['Cancel'].update(visible = False)             # hide cancel button
            State = States.IDLE

        if event == 'Draw':
            logger.info("Draw Pressed")
            
            window['Clear'].update(visible = False)              # hide clear button
            window['Cancel'].update(visible = True)              # hide clear button

            thread_id = threading.Thread(target=generateDrawing, args=(work_id, gui_queue), daemon=True) # Start Loader
            thread_id.start()
            work_id = work_id + 1 if work_id < 19 else 0

            State = States.DRAWING

        if event == 'Setup':
            logger.info("Setup Pressed")
            writeComs("HS !") # send home stepper command

        # Drawing
        if State == States.DRAWING:
            totCommands = len(commands) 
            window['drawing_progress'].update(visible=True)
            # TODO: Update progress image evert few frames
            if ready: # if it is a new instruction and a move has been competed, send next command
                prevIndex = None
                logger.info("Sending next Command")
                writeComs(commands[index])
                index += 1
                progress_normalized = round(index/totCommands)*100
                window['drawing_progress'].update(progress_normalized)

                time_per_command = 2 # Seconds
                time_remaining = (totCommands - index) * time_per_command 

                if progress_normalized % 2 == 0 and prevIndex is not progress_normalized:
                    logger.info("Updated preview")

                    prevIndex = progress_normalized
                    renderProgress(imgSize, progress=index) # render the svg to a file
                    snapShot = Img2Byte("progress.png")     # render svg to screen

                ready = False
                

        if State == States.SETUP:
            window['image'].update(visible = False)
            window['Debug'].update(visible = True)

        if State == States.PREVIEW:
            window['Capture'].update(visible = False)           # hide capture button
            window['Draw'].update(visible = True)               # show draw button
            window['Clear'].update(visible = True)              # show clear button
            window['image'].update(data=snapShot, size=imgSize) # show the final image

        if State == States.IDLE:
            ret, frame = cap.read()
            croped_img = frame[0:imgSize[0], 0:imgSize[1]]
            imgbytes = cv2.imencode('.png', croped_img)[1].tobytes()
            window['image'].update(data=imgbytes, size=imgSize, visible = True)
            window['Capture'].update(visible = True)
            window['Setup'].update(visible = False)
            window['Debug'].update(visible = False)
            window['Exit'].update(visible = True)

         # --------------- Read next message coming in from threads ---------------
        try:
            message = gui_queue.get_nowait()  # see if something has been posted to Queue
        except queue.Empty:  # get_nowait() will get exception when Queue is empty
            message = None  # nothing in queue so do nothing
        # if message received from queue, then some work was completed
        if message is not None:
            # Run at the end of a long process, can add pop up text when a process is completed (drawing? )
            completed_work_id = int(message[:message.index(' :::')])
            #window.Element('_OUTPUT2_').Update('Finished long work %s' % completed_work_id)
            work_id -= 1
            if not work_id:
                sg.PopupAnimated(None)
        if work_id:
            sg.PopupAnimated(sg.DEFAULT_BASE64_LOADING_GIF, background_color='white', time_between_frames=100, location = tuple(ti/2 for ti in windowSize))

def Button(img, event, visible=True):
    return sg.pin(sg.Button('', image_filename="GUI_Elements/{}.png".format(img), key=event, button_color=('black'), border_width=0, visible=visible))

def Img2Byte(imgPath):
    img = cv2.imread(imgPath)
    imgbytes = cv2.imencode('.png', img)[1].tobytes()
    return imgbytes


def generateDrawing(work_id, gui_queue):
    global commands

    commands, totalPaths = genCommands()
    gui_queue.put('{} ::: done'.format(work_id))

    return

def generatePreview(work_id, gui_queue, frame, imgSize):
    global snapShot

    croped_img = frame[0:imgSize[0], 0:imgSize[1]] # crop image to size
    cv2.imwrite("snapShot.bmp", croped_img) # write image to file

    automatic_brightness_and_contrast() # normalise image 
    removeBG(imgSize) # replace background with white
    genSVG() # generage the svg from the image
    renderProgress(imgSize) # render the svg to a file
    snapShot = Img2Byte("progress.png") # render svg to screen

    gui_queue.put('{} ::: done'.format(work_id))

    return

if __name__ == "__main__":
    filename="logs.txt"
    # clear logger file
    open(filename, 'w').close()

    # init logging
    logging.basicConfig(filename=filename,
                    filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.DEBUG)

    logger = logging.getLogger('main')

    main(logger)
