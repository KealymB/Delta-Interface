import serial
from enum import Enum

# State Variables
buffer = ""     #Line buffer saving latest com
homed = False   #Flag of if the motors have been homed
moving = False  #Flag if motors are currently moving
error = False   #Flag if there is an error
command = ""

# Serial communication
try: 
    ser = serial.Serial('COM3', 115200)
except:
    ser = None
    print("Error opening serial")

def readComs():
    global buffer, ser
    if ser is None: 
        return 0
    if ser.in_waiting > 0:
        buffer = ser.readline().decode().rstrip()
        print(buffer)
        return handleComs()
    return 0 # return 0 if there is nothing in the serial buffer

def handleComs(instruction = None):
    global ser, command, moving
    if ser is None: 
        return 0
    if not homed and buffer.split("-")[0] == "I2": 
        homed = True
        clearBuffer()
        return 2 # Return idle state
    if homed and not error and not moving:
        if buffer.split("-")[0] == "E1":
            #repeat command if command is incorrectly received 
            ser.write(command)
            clearBuffer()
            return 0
        else:
            #if there is an instruction send it over comms
            if instruction is not None:
                if instruction != command:
                    command = instruction #save command to buffer if there is an error
                    ser.write(command)
                    moving = True
                    clearBuffer()
                    return 0
                else: 
                    return -1
    if moving and buffer.startswith("A"): # Move has been completed, A2 returned from serial
        moving = False
        clearBuffer()
        return 1 # return waiting for instruction state
    return 0
    

def clearBuffer(): 
    global buffer
    #clears line buffer
    buffer = ""