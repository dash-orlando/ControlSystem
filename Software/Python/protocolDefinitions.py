"""
protocolDefinitions.py

The following module consists of a list of commands or definitions to be used in the communication between devices and the control system

Michael Xynidis
Fluvio L Lobo Fenoglietto
09/26/2016
"""
                #       Name                        Value
                #       ----                        -----
CHK = chr(0x01) #       System Check                0x01
ENQ = chr(0x05) #       Enquiry                     0x05
EOT = chr(0x04) #       End of Transmission         0x04
ACK = chr(0x06) #       Positive Acknowledgement    0x06
NAK = chr(0x15) #       Negative Acknowledgement    0x15

