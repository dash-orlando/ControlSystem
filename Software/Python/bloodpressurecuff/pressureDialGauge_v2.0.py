'''
*
* CUSTOMIZED VERSION FOR DEMO PURPOSES
*
* Read pressure sensor and display readings on a dial gauge
*
* Adapted from: John Harrison's original work
* Link: http://cratel.wichita.edu/cratel/python/code/SimpleVoltMeter
*
* VERSION: 0.5
*   - MODIFIED: This iteration of the pressureDialGauge is not intended
*               as a standalone program. It is meant to work in conjunction
*               with the appJar GUI. Attempting to run this program as a
*               standalone will throw so many errors at you you will regret it!!!
*
* KNOWN ISSUES:
*   - Nada so far.
* 
* AUTHOR                    :   Mohammad Odeh
* DATE                      :   Mar. 07th, 2017 Year of Our Lord
* LAST CONTRIBUTION DATE    :   Feb. 16th, 2018 Year of Our Lord
*
'''

# ========================================================================================= #
# Import Libraries and/or Modules
# ========================================================================================= #

# Python modules
import  sys, time, bluetooth, serial, argparse                                              # 'nuff said
import  Adafruit_ADS1x15                                                                    # Required library for ADC converter
from    PyQt4                                   import QtCore, QtGui, Qt                    # PyQt4 libraries required to render display
from    PyQt4.Qwt5                              import Qwt                                  # Same here, boo-boo!
from    numpy                                   import interp                               # Required for mapping values
from    threading                               import Thread                               # Run functions in "parallel"
from    os                                      import getcwd, path, makedirs               # Pathname manipulation for saving data output

# PD3D modules
from    dial_v2                                 import Ui_MainWindow
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

from    timeStamp                               import fullStamp
from    bluetoothProtocol_teensy32              import *
from    stethoscopeProtocol                     import *
import  stethoscopeDefinitions                  as     definitions


# ========================================================================================= #
# Variables
# ========================================================================================= #

executionTimeStamp = fullStamp()                                                            # generating execution time stamp 

# ----------------------------------------------------------------------------------------- #
# Constructing argument parser
# ----------------------------------------------------------------------------------------- #

ap = argparse.ArgumentParser()

ap.add_argument( "-f", "--frequency", type=int, default=0.25,                               # sampling frequency for pressure measurement
                help="Set sampling frequency (in secs).\nDefault=1" )
ap.add_argument( "-d", "--debug", action='store_true',                                      # debug mode --mo
                help="Invoke flag to enable debugging" )
#ap.add_argument( "--directory", type=str, default='output',                                # directory --will remove
#                help="Set directory" )
#ap.add_argument( "--destination", type=str, default="output.txt",
#                help="Set destination" )
#ap.add_argument( "--stethoscope", type=str, default="00:06:66:8C:D3:F6",
#                help="Choose stethoscope" )
ap.add_argument( "-m", "--mode", type=str, default="REC",                                   # reconrding or simulation mode
                help="Mode to operate under; SIM: Simulation || REC: Recording" )
ap.add_argument( "-lp", "--lower_pressure", type=str, default=75,                           # set lower pressure limit as an input (for SIM only)
                help="Lower Pressure Limit (only for SIM)" )
ap.add_argument( "-hp", "--higher_pressure", type=str, default=125,                         # set higher pressure limit as an input (for SIM only)
                help="Higher Pressure Limit (only for SIM)" )
args = vars( ap.parse_args() )


# ========================================================================================= #
# Program Configuration
# ========================================================================================= #

class MyWindow(QtGui.QMainWindow):

    pressureValue = 0
    lastPressureValue = 0
    
    def __init__( self, parent=None ):

        # Initialize program and extract dial GUI
        QtGui.QWidget.__init__( self, parent )
        self.ui = Ui_MainWindow()
        self.ui.setupUi( self )
        self.thread = Worker( self )

        # Close rfObject socket on exit
        #self.ui.pushButtonQuit.clicked.connect( self.cleanUp )

        # Setup gauge-needle dimensions
        self.ui.Dial.setOrigin( 90.0 )
        self.ui.Dial.setScaleArc( 0.0, 340.0 )
        self.ui.Dial.update()
        self.ui.Dial.setNeedle( Qwt.QwtDialSimpleNeedle(
                                                        Qwt.QwtDialSimpleNeedle.Arrow,
                                                        True, Qt.QColor(Qt.Qt.red),
                                                        Qt.QColor(Qt.Qt.gray).light(130)
                                                        )
                                )

        self.ui.Dial.setScaleOptions( Qwt.QwtDial.ScaleTicks |
                                      Qwt.QwtDial.ScaleLabel | Qwt.QwtDial.ScaleBackbone )

        # Small ticks are length 5, medium are 15, large are 20
        self.ui.Dial.setScaleTicks( 5, 15, 20 )
        
        # Large ticks show every 20, put 10 small ticks between
        # each large tick and every 5 small ticks make a medium tick
        self.ui.Dial.setScale( 10.0, 10.0, 20.0 )
        self.ui.Dial.setRange( 0.0, 300.0 )
        self.ui.Dial.setValue( 0 )

        # Unpack argumnet parser parameters as attributes
        # self.directory      = args["directory"]
        # self.destination    = args["destination"]
        # self.address        = args["stethoscope"]
        self.mode           = args["mode"]
        self.lp             = args["lower_pressure"]
        self.hp             = args["higher_pressure"]

        # Boolean to control recording function
        #self.init_rec = True

        # List all available BT devices
        self.ui.Dial.setEnabled( True )
        #self.ui.pushButtonPair.setEnabled( False )
        #self.ui.pushButtonPair.setText(QtGui.QApplication.translate("MainWindow", "Paired", None, QtGui.QApplication.UnicodeUTF8))
        
        # set timeout function for updates
        self.ctimer = QtCore.QTimer()
        self.ctimer.start( 10 )
        QtCore.QObject.connect( self.ctimer, QtCore.SIGNAL( "timeout()" ), self.UpdateDisplay )

        # Create logfile
        self.setup_log()

# ------------------------------------------------------------------------
    """
    --- v1.0
    --- Removed as this will be done externally
    
    def connectStethoscope( self ):
        
        #Connects to stethoscope.
        
        self.thread.deviceBTAddress = str( self.address )
        self.ui.Dial.setEnabled( True )
        self.ui.pushButtonPair.setEnabled( False )

        # Create logfile
        self.setup_log()
        
        # set timeout function for updates
        self.ctimer = QtCore.QTimer()
        self.ctimer.start( 10 )
        QtCore.QObject.connect( self.ctimer, QtCore.SIGNAL( "timeout()" ), self.UpdateDisplay )
    """
# ------------------------------------------------------------------------
 
    def UpdateDisplay(self):
        """
        Updates DialGauge display with the most recent pressure readings.
        """
        
        if self.pressureValue != self.lastPressureValue:
            self.ui.Dial.setValue( self.pressureValue )
            self.lastPressureValue = self.pressureValue

# ------------------------------------------------------------------------
    """
    --- v1.0
    --- Removed as this will be done externally
    
    def scan_rfObject( self ):
        
        Scan for available BT devices.
        Returns a list of tuples (num, name)
        
        available = []
        BT_name, BT_address = findSmartDevice( self.address )
        if BT_name != 0:
            available.append( (BT_name[0], BT_address[0]) )
            return( available )
    """
# ------------------------------------------------------------------------

    def setup_log( self ):
        """
        Setup directory and create logfile.
        """
        
        # Create data output folder/file
        outDir = consDir + "output/"                                                        # find or generate the main output directory
        if( path.exists( outDir ) == False ):
            #print( fullStamp() + " Output directory not present " )
            #print( fullStamp() + " Generating output directory " )
            makedirs( outDir )
        #else:
            #print( fullStamp() + " Found output directory " )                          

        stampedDir = outDir + executionTimeStamp + "/"                                      # find or generate the time-stamped output directory
        if( path.exists( stampedDir ) == False ):
            #print( fullStamp() + " Time-stamped directory not present " )
            #print( fullStamp() + " Generating time-stamped directory " )
            makedirs( stampedDir )
        #else:
            #print( fullStamp() + " Found time-stamped directory " )
        
        self.dataFileDir = stampedDir
        self.dataFileName = stampedDir + "bpcu.txt"

        # Write basic information to the header of the data output file
        with open( self.dataFileName, "w" ) as f:
            f.write( "Date/Time: " + executionTimeStamp + "\n" )
            f.write( "Device Name: " + deviceName + "\n" )
            f.write( "Units: seconds, kPa, mmHg, SIM" + "\n" )
            f.close()
            #print( fullStamp() + " Created data output .txt file" )

# ------------------------------------------------------------------------

    def cleanUp( self ):
        """
        Clean up at program exit.
        Stops recording and closes communication with device
        """
        
        #print( fullStamp() + " Goodbye!" )
        QtCore.QThread.sleep( 2 )                               # this delay may be essential


# ========================================================================================= #
# Class for optional, independent thread
# ========================================================================================= #

class Worker( QtCore.QThread ):

    # Create flags for what mode we are running
    normal      = True                                                                      # normal state, out of the simulated pressure range
    playback    = False                                                                     # simulated state, within the simulated pressure range
    recent      = playback                                                                  # most recent state                                                                  
    
    # Define sasmpling frequency (units: sec) controls writing frequency
    wFreq = args["frequency"]
    wFreqTrigger = time.time()
    
    def __init__( self, parent = None ):
        QtCore.QThread.__init__( self, parent )
        # self.exiting = False # not sure what this line is for
        #print( fullStamp() + " Initializing Worker Thread" )
        self.owner = parent
        self.start()

# ------------------------------------------------------------------------

    def __del__(self):
        print( fullStamp() + " Exiting Worker Thread" )

# ------------------------------------------------------------------------

    def run(self):
        """
        This method is called by self.start() in __init__()
        """
        
        try:
            
            self.startTime = time.time()                                            # Time since the initial reading
            
            while True:
                self.owner.pressureValue = self.readPressure()                      # 

        except Exception as instance:
            print( fullStamp() + " Failed to connect" )                             # Indicate error
            print( fullStamp() + " Exception or Error Caught" )                     # ...
            print( fullStamp() + " Error Type " + str(type(instance)) )             # ...
            print( fullStamp() + " Error Arguments " + str(instance.args) )         # ...

# ------------------------------------------------------------------------

    def readPressure(self):

        # Compute pressure
        V_analog  = ADC.read_adc( 0, gain=GAIN )                                    # Convert analog readings to digital
        V_digital = interp( V_analog, [1235, 19279.4116], [0.16, 2.41] )            # Map the readings
        P_Pscl  = ( V_digital/V_supply - 0.04 )/0.018                               # Convert voltage to SI pressure readings
        P_mmHg = P_Pscl*760/101.3                                                   # Convert SI pressure to mmHg
        
        # Check if we should write to file or not yet
        if( time.time() - self.wFreqTrigger ) >= self.wFreq:
            
            self.wFreqTrigger = time.time()                                         # Reset wFreqTrigger

            if( self.playback is not self.recent ):
                if( self.playback == True ):
                    print( "SIM, 1")                                                # within simulated pressure range
                elif( self.playback == False ):
                    print( "SIM, 0")                                                # outside simulated pressure range
                #print( "SIM %r" %(self.playback) )
                self.recent = self.playback
            
            # Write to file
            dataStream = "%.02f, %.2f, %.2f, %r\n" %( time.time()-self.startTime,       # Format readings
                                                      P_Pscl,
                                                      P_mmHg,
                                                      self.playback )
            with open( self.owner.dataFileName, "a" ) as f:
                f.write( dataStream )                                               # Write to file
                f.close()                                                           # Close file

        if( self.owner.mode == "SIM" ): self.sim_mode( P_mmHg )                     # Trigger simulations mode (if --mode SIM)
        else: self.rec_mode()                                                       # Trigger recording   mode (if --mide REC)
        
        return( P_mmHg )                                                            # Return pressure readings in mmHg

# ------------------------------------------------------------------------

    def sim_mode( self, P ):
        """
        In charge of triggering simulations
        """
        lp = float( args["lower_pressure"] )
        hp = float( args["higher_pressure"] )
        
        # Error handling (1)
        try:
            # Entering simulation pressure interval
            if (P >= lp) and (P <= hp) and (self.playback == False):
                self.normal = False                                                 # Turn OFF normal playback
                self.playback = True                                                # Turn on simulation

            # Leaving simulation pressure interval
            elif ((P < lp) or (P > hp)) and (self.normal == False):
                self.normal = True                                                  # Turn ON normal playback
                self.playback = False                                               # Turn OFF simulation

        # Error handling (2)        
        except Exception as instance:
            print( "" )                                                             # ...
            print( fullStamp() + " Exception or Error Caught" )                     # ...
            print( fullStamp() + " Error Type " + str(type(instance)) )             # Indicate the error
            print( fullStamp() + " Error Arguments " + str(instance.args) )         # ...

# ------------------------------------------------------------------------
    """
    --- v1.0
    --- Removed as this will be done externally

    def rec_mode( self ):
        
        #In charge of triggering recordings
        
        
        if( self.owner.init_rec == True ):
            self.owner.init_rec = False
            #statusEnquiry( self.rfObject )
            #startCustomRecording( self.rfObject, self.owner.destination )           # If all is good, start recording

        else: pass
    """   
            
# ========================================================================================= #
# SETUP
# ========================================================================================= #
port = 1                                                                                    # Port number to use in communication
deviceName = "Blood Pressure Cuff"                                                          # Designated device name
scenarioNumber = 1                                                                          # Device number

V_supply = 3.3                                                                              # Supply voltage to the pressure sensor

ADC = Adafruit_ADS1x15.ADS1115()                                                            # Initialize ADC
GAIN = 1                                                                                    # Read values in the range of +/-4.096V

# ========================================================================================= #
# MAIN
# ========================================================================================= #

def main():
    
    print( fullStamp() + " Booting DialGauge" )
    app = QtGui.QApplication(sys.argv)
    MyApp = MyWindow()
    MyApp.show()
    sys.exit(app.exec_())
    
if __name__ == "__main__":
    sys.exit( main() )
