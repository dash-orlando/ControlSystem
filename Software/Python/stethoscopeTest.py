
# Import
import sys
import os
import serial
import stethoscopeDefinitions       as     definitions
from   os.path                      import expanduser
from   bluetoothProtocol_teensy32   import *
from   stethoscopeProtocol          import *

# =========
# OPERATION
# =========

deviceName = "SS"
portNumber = 0
deviceBTAddress = "00:06:66:7D:99:D9"
baudrate = 115200
attempts = 5
rfObject = createPort(deviceName,portNumber,deviceBTAddress,baudrate,attempts)

time.sleep(2)
if rfObject.isOpen() == False:
    rfObject.open()
startTrackingMicStream(rfObject)
rfObject.close()

time.sleep(30)

time.sleep(2)
if rfObject.isOpen() == False:
    rfObject.open()
stopTrackingMicStream(rfObject)
rfObject.close()

portRelease('rfcomm', 0)

