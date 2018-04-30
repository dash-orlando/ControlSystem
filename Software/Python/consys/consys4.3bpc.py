"""
consys4.py

Latest version of the control system execution software
            
Fluvio L. Lobo Fenoglietto 04/18/2018
"""

# ========================================================================================= #
# Import Libraries and/or Modules
# ========================================================================================= #
# Python modules
import  sys
import  os
import  serial
import  time
import  argparse
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

# ========================================================================================= #
# Variables
# ========================================================================================= #

executionTimeStamp  = fullStamp()

# ----------------------------------------------------------------------------------------- #
# Constructing argument parser
# ----------------------------------------------------------------------------------------- #

ap = argparse.ArgumentParser()

ap.add_argument( "-s", "--scenario", type=int, default=0,                               # sampling frequency for pressure measurement
                help="Select scenario.\nDefault=1" )
ap.add_argument( "-st", "--simulation_time", type=int, default=45,                                      # debug mode --mo
                help="Simulation time" )
args = vars( ap.parse_args() )

print( fullStamp() + " Scenario = " + str( args["scenario"] ) )
print( fullStamp() + " Simulation Time = " + str( args["simulation_time"] ) )

# ========================================================================================= #
# Functions
# ========================================================================================= #

def readGauge( initialCall, Q ):
    # start blood pressure cuff and digital dial ---------------------------------------------- #
    print( fullStamp() + " Connecting to blood pressure cuff " )
    mode            = "SIM"
    lower_pressure  = 85.0                                                                      # units in mmHg
    higher_pressure = 145.0                                                                     # ...

    #pexpect.run("DISPLAY:=0")
    #print( bpcuDir )
    cmd = "python " + bpcuDir + "pressureDialGauge_v2.0.py --destination " + executionTimeStamp + " --mode SIM --lower_pressure " + str(lower_pressure) + " --higher_pressure " + str(higher_pressure)
    pressure_meter = pexpect.spawn( cmd, timeout=None )

    if( initialCall ):
        Q.put( pressure_meter )                                                                 # Place variable in queue for retrival
        initialCall = False
        
    for line in pressure_meter:
        out = line.strip('\n\r')
        Q.put( out )
        #print( out )

    #pressure_meter.close()

# ----------------------------------------------
# Devices
# ----------------------------------------------
stethoscope_name = "Stethoscope"
stethoscope_bt_address = (["00:06:66:D0:E4:94"])


SOH             			= chr(0x01)                                         			# Start of Header
ENQ							= chr(0x05)                                         			# Enquiry
ACK             			= chr(0x06)                                         			# Positive Acknowledgement
NAK             			= chr(0x15)                                         			# Negative Acknowledgement


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
stethoscope_bt_object = createBTPort( stethoscope_bt_address[0], 1 )                        # using bluetooth protocol commands

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
print( fullStamp() + " Connecting to blood pressure cuff " )
q_pressure_meter = Queue( maxsize=0 )                                                   # Define queue
t_pressure_meter = Thread( target=readGauge, args=( True, q_pressure_meter, ) )# Define thread
t_pressure_meter.daemon = True
t_pressure_meter.start()                                                                # Start thread

pexpectChild = q_pressure_meter.get()

# ----------------------------------------------------------------------------------------- #
# Data Gathering
# ----------------------------------------------------------------------------------------- #
# Variables
scenario            = args["scenario"]                                                                     # scenario type
"""
scenario            = 0         # Normal                --no simulation
scenario            = 1         # stethoscope aug.      --aug. of the stethoscope
scenario            = 2         # blood pressure aug.   --aug. of blood pressure
scenario            = 3         # All                   --aug. of all devices
"""
simStartTime        = time.time()
simCurrentTime      = 0                                                                     # seconds
simDuration         = args["simulation_time"]                                                                    # seconds
simStopTime         = simDuration                                                           # seconds

smartholder_data    = [] 								    # empty array for smart holder data
holder_flag         = 1                                          			    # single sensor flag
bpc_flag            = 0                                                                     # blood pressure sim region flag

print( fullStamp() + " " + str( simDuration ) + " sec. simulation begins now " )            # Statement confirming simulation start

while( simCurrentTime < simDuration ):

    # checking holder data ---------------------------------------------------------------- #
    holder_data = "{}".format( smartholder_usb_object.readline() )                          # Read until timeout is reached

    if( holder_data == '' ):                                                                # if the holder data is empty, do nothing
        pass
    else:
        split_line = holder_data.split()                                                    # Split incoming data
        formatted = ( "{} {} {}".format( fullStamp(), split_line[1], split_line[2] ) )      # Construct string
        #print( formatted.strip('\n') )                                                      # [INFO] Status update

        if( split_line[1] == '1:' and split_line[2] == '0' ):
            print( fullStamp() + " " + stethoscope_name + " has been removed " )
            holder_flag = 0

        elif( split_line[1] == '1:' and split_line[2] == '1' ):
            print( fullStamp() + " " + stethoscope_name + " has been stored " )
            holder_flag = 1

        smartholder_data.append( ["%.02f" %simCurrentTime,
                                  str( holder_flag ),
                                  '\n'])

    # checking pressure values ------------------------------------------------------------ #
    if( q_pressure_meter.empty() == False ):
        line = q_pressure_meter.get( block=False )
        split_line = line.split(" ")
        if( len( split_line ) <= 2 ):
            bpc_flag = int(split_line[1])
            if( bpc_flag == 1 ):
                print( fullStamp() + " Within simulated pressure range " )
            elif( bpc_flag == 0 ):
                print( fullStamp() + " Outside simulated pressure range " )

    # interaction ------------------------------------------------------------------------- #
    if( scenario == 0 ):
        if( holder_flag == 0 ):
            statusEnquiry( stethoscope_bt_object )

    elif( scenario == 1 ):
        if( holder_flag == 0 ):
            statusEnquiry( stethoscope_bt_object ) # replace for blending

    elif( scenario == 2 ):
        if( holder_flag == 0 and bpc_flag == 1):
            statusEnquiry( stethoscope_bt_object ) # replace for blending
            
        
    simCurrentTime = time.time() - simStartTime
											     
# ----------------------------------------------------------------------------------------- #
# Device Deactivation
# ----------------------------------------------------------------------------------------- #
print( fullStamp() + " Closing blood pressure cuff connection " )
pexpectChild.close()

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

smartholder_output_filename = stampedDir + "holder.txt"

N_lines = len( smartholder_data )

for i in range(0, N_lines):
        if( i == 0 ):
                with open(smartholder_output_filename, 'a') as dataFile:
                        dataFile.write( fullStamp() + " Smart Holder for = " + stethoscope_name + '\n' )
                        dataFile.write( fullStamp() + " COM Port = " + str( port ) + '\n')
        with open(smartholder_output_filename, 'a') as dataFile:
                dataFile.write( smartholder_data[i][0] + "," + smartholder_data[i][1] + '\n' )

if( t_pressure_meter.isAlive() ):
    print( "Closing thread" )
    t_pressure_meter.join(2.0)

# zipping output
print( fullStamp() + " Compressing data " )
os.system("cd " + consDir + "; sudo zip -r " + consDir + "output.zip output")

# ----------------------------------------------------------------------------------------- #
# END
# ----------------------------------------------------------------------------------------- #
print( fullStamp() + " Program completed " )


