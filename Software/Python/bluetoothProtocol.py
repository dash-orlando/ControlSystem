"""
bluetoothProtocol.py

The following module has been created to manage the bluetooth interface between the control system and the connected devices

Michael Xynidis
Fluvio L Lobo Fenoglietto
09/01/2016


List of functions ::

X - Look for bluetooth device
X - Pair bluetooth device
X - Add paired device to the instrument list
X.X - Connect to paired device
    X.X - Create RFComm Port
    X.X - Release RFComm Port

"""

# Import Libraries and/or Modules
import os
import serial
from timeStamp import *

# Create RFComm Ports
#   This function creates radio-frquency (bluetooth) communication ports for specific devices, using their corresponding address
#   Input   ::  {array/list} "deviceName", "deviceBTAddress"
#   Output  ::  {array/list} "btObjects"
def createPort(deviceName, deviceBTAddress):
    Ndevices = len(deviceName)                                                              # Determines the number of devices listed
    RFObject = []                                                                           # Create RF object variable/list (in case of multiple devices)
    for i in range(0,Ndevices):     
        portRelease("rfcomm",i)                                                             # Release the RFComm port of interest
        print fullStamp() + " Connecting device to RFCOMM" + str(i)                         # Terminal message, program status
        os.system("sudo rfcomm bind /dev/rfcomm" + str(i) + " " + deviceBTAddress[i])       # Bind bluetooth device to control system
        RFObject.append(serial.Serial("/dev/rfcomm" + str(i),115200))                       # Create and append RFComm port to the RFObject structure
        #triggerRFInstrument(arduRFObj[i], instrumentNames[i])                              # Trigger data collection on instruments
    return RFObject                                                                         # Return RFObject or list of objects


# Port Release
#   This function releases the specified communication port (serial) given the type and the number
#   Input   ::  {string} "portType", {int} "portNumber"
#   Output  ::  None -- Terminal messages
def portRelease(portType, portNumber):
    print fullStamp() + " Releasing RFCOMM" + str(portNumber)                               # Terminal message, program status
    os.system("sudo " + portType + " release " + str(portNumber))                           # Releasing port through terminal commands

# Connect to paired device
#   Connects to the bluetooth devices specified by the scenario configuration file
#   Input   ::  {array/list} "deviceName", "deviceBTAddress"
#   Output  ::  {array/list} "btObjects"

