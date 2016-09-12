"""
stethoscopeProtocol.py

The following module has been created to manage the device-specific interface between the stethoscope and the control system modules

Michael Xynidis
Fluvio L Lobo Fenoglietto
09/01/2016

List of functions ::




List of commands ::

Command Type    Definition
------------------------------------------------------------------------
SAREC     {string} Start Recording
SOREC     {string} Stop Recording


"""

# Import Libraries and/or Modules
import os
import serial
from timeStamp import *
from configurationProtocol import *
from bluetoothProtocol import *

# Begin Recording
#       This function will trigger the recording and storing of an audio signal by the Teensy board
#       Input   ::      None
#       Output  ::      None
def beginRecord(rfObject):
        outString = "REC"
        
