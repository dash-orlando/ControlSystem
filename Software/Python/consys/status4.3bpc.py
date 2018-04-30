"""
status4.3bpc.py

...
            
Fluvio L. Lobo Fenoglietto 04/29/2018
"""

# ========================================================================================= #
# Import Libraries and/or Modules
# ========================================================================================= #
# Python modules
import  sys
import  os
import  serial
import  time
import  pexpect
from    os.path                     import expanduser
from    os                          import getcwd, path, makedirs
from    threading                   import Thread
from    Queue                       import Queue

# PD3D modules
from    configurationProtocol                   import *
cons    = "consys"
shan    = "smarthandle"
shol    = "smartholder"
stet    = "stethoscope"
bpcu    = "bloodpressurecuff"

homeDir, pythonDir, consDir = definePaths(cons)
homeDir, pythonDir, shanDir = definePaths(shan)
homeDir, pythonDir, sholDir = definePaths(shol)
homeDir, pythonDir, stetDir = definePaths(stet)
homeDir, pythonDir, bpcuDir = definePaths(bpcu)

response = addPaths(pythonDir)
response = addPaths(consDir)
response = addPaths(shanDir)
response = addPaths(sholDir)
response = addPaths(stetDir)
response = addPaths(bpcuDir)

from    timeStamp                   import fullStamp
from    bluetoothProtocol_teensy32  import *
from    usbProtocol                 import *
from    smarthandleProtocol         import *
from    stethoscopeProtocol         import *


executionTimeStamp  = fullStamp()

# ========================================================================================= #
# Variables
# ========================================================================================= #

# ----------------------------------------------
# Devices
# ----------------------------------------------
stethoscope_name        = "Stethoscope"
stethoscope_bt_address  = (["00:06:66:8C:D3:F6"])


SOH             			= chr(0x01)                                         # Start of Header
ENQ					= chr(0x05)                                         # Enquiry
ACK             			= chr(0x06)                                         # Positive Acknowledgement
NAK             			= chr(0x15)                                         # Negative Acknowledgement


# ========================================================================================= #
# Operation
# ========================================================================================= #

# ----------------------------------------------------------------------------------------- #
# Device Configuration, Connection and Activation
# ----------------------------------------------------------------------------------------- #
print fullStamp() + " OPERATION "
print fullStamp() + " Begin device configuration "

# connecting to panel devices
print( fullStamp() + " Connecting to panel devices " )

# connecting to stethoscope --------------------------------------------------------------- #
print( fullStamp() + " Connecting to stethoscope " )
try:
    stethoscope_bt_object = createBTPort( stethoscope_bt_address[0], 1 )                        # using bluetooth protocol commands
except e:
    print(e)

# connecting to smart holders ------------------------------------------------------------- #
print( fullStamp() + " Connecting to smart holders " )
port = 0
baud = 115200
timeout = 1
notReady = True

try:
    smartholder_usb_object  = createUSBPort( port, baud, timeout )                          # test USB vs ACM port issue
except:
    smartholder_usb_object  = createACMPort( port, baud, timeout )

if smartholder_usb_object.is_open:
    pass
else:
    smartholder_usb_object.open()

while( notReady ):                                                                          # Loop until we receive SOH
    inData = smartholder_usb_object.read( size=1 )                                          # ...
    if( inData == SOH ):                                                                    # ...
        print( "{} [INFO] SOH Received".format( fullStamp() ) )                             # [INFO] Status update
        break                                                                               # ...

time.sleep(0.50)                                                                            # Sleep for stability!


# start blood pressure cuff and digital dial ---------------------------------------------- #
"""
print( fullStamp() + " Connecting to blood pressure cuff " )
q_pressure_meter = Queue( maxsize=0 )                                                   # Define queue
t_pressure_meter = Thread( target=readGauge, args=( True, q_pressure_meter, ) )# Define thread
t_pressure_meter.daemon = True
t_pressure_meter.start()                                                                # Start thread

pexpectChild = q_pressure_meter.get()
"""
# ----------------------------------------------------------------------------------------- #
# Data Gathering
# ----------------------------------------------------------------------------------------- #
# Variables
scenario            = 0                                                                     # scenario type

# ----------------------------------------------------------------------------------------- #
# Device Deactivation
# ----------------------------------------------------------------------------------------- #
#print( fullStamp() + " Closing blood pressure cuff connection " )
#pexpectChild.close()

print( fullStamp() + " Disconnecting bluetooth devices " )
if( scenario == 0 ):
    statusEnquiry( stethoscope_bt_object ) # replace with stop recording
elif( scenario == 1 ):
    statusEnquiry( stethoscope_bt_object ) # replace with stop recording and blending
elif( scenario == 2 ):
    statusEnquiry( stethoscope_bt_object )

stethoscope_bt_object.close()

print( fullStamp() + " Disconnecting usb devices " )
if( smartholder_usb_object.is_open ):
    smartholder_usb_object.close()

# ========================================================================================= #
# Output
# ========================================================================================= #
"""
print( fullStamp() + " Writting data to file " )

outDir = consDir + "output/"
if( path.exists( outDir ) == False ):
    print( fullStamp() + " Output directory not present " )
    print( fullStamp() + " Generating output directory " )
    makedirs( outDir )
else:
    print( fullStamp() + " Found output directory " )

stampedDir = outDir + executionTimeStamp + "/"
if( path.exists( stampedDir ) == False ):
    print( fullStamp() + " Time-stamped directory not present " )
    print( fullStamp() + " Generating time-stamped directory " )
    makedirs( stampedDir )
else:
    print( fullStamp() + " Found time-stamped directory " )
"""
# ----------------------------------------------------------------------------------------- #
# END
# ----------------------------------------------------------------------------------------- #
print( fullStamp() + " Program completed " )


