import serial
from enum import Enum

# State Variables
buffer = ""     #Line buffer saving latest com
prevInstruction = ""

# Serial communication
try: 
    ser = serial.Serial('/dev/ttyUSB0', 115200)
except:
    ser = None
    print("Error opening serial")

def readComs():
    global buffer, ser
    if ser is None: 
        return 0
    if ser.in_waiting > 0:
        buffer = ser.readline().decode().rstrip()
        return bufferHandler()
    return 0 # return 0 if there is nothing in the serial buffer

def writeComs(instruction):
    global ser, prevInstruction
    if ser is None: 
        return
    prevInstruction = instruction
    ser.write(instruction)

def bufferHandler():
    # Handles the buffer.
    # Returns -1 for serious error, 0 for idle, 1 for go for next command, 2 for motors homed
    global buffer
    print(buffer)
    if buffer.startswith("E1"): # repeat last command
        writeComs(prevInstruction)
    if buffer.startswith("E5") or buffer.startswith("E0"): # over heating error
        return -1
    if buffer.startswith("A"):
        return 1
    if buffer.startswith("I2"):
        return 2
    return 0
    