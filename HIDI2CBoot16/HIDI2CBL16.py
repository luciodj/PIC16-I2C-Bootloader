#!usr/bin/python
#
# HID-I2C Bootloader for PIC16 
# 
# Author: Lucio Di Jasio
# url: blog.flyingpic24.com
#
import hid
import time
import sys
import subprocess
import intelhex
from Tkinter import *
from tkFileDialog import askopenfilename

__version__ = 0.1

DEVRead      = 0x91         # I2C address + read command
DEVWrite     = 0x90         # I2C address + write command
cmdI2CInit   = 0x20         # Clicker HIDAPI I2C init command
cmdI2CRead   = 0x21         # Clicker HIDAPI I2C read command
cmdI2CWrite  = 0x22         # Clicker HIDAPI I2C write command 

Microchip_vid = 0x04d8
Clicker_pid = 0x3f       # same as the Mikromedia

cmdSYNC     =  1
cmdINFO     =  2
cmdBOOT     =  3
cmdREBOOT   =  4
cmdWRITE    = 11
cmdERASE    = 21

"""
Protocol Description.

    USB protocol is a typical master-slave communication protocol, where
    master (PC) sends commands and slave (bootloader equipped device) executes
    them and acknowledges execution.

    * Command format.
    
    <CMD_CODE> <ADDRESS> <COUNT[0..1]> <DATA[0..COUNT-1]>
    ---- 2 ---|--- 2 ---|----- 2 ----|------ COUNT -----|

    CMD_CODE - Command index (TCmd).
               Length: 2 byte. Mandatory.
    ADDRESS  - Address field. Flash start address for
               CMD_CODE command operation.
               Length: 2 bytes. Optional (command specific).
    COUNT    - Count field. Amount of data/blocks for
               CMD_CODE command operation.
               Length: 2 bytes. Optional (command specific).
    DATA     - Data array.
               Length: COUNT bytes. Optional (command specific).

    Some commands do not utilize all of these fields.
    See 'Command Table' below for details on specific command's format.

    * Command Table.
     --------------------------+---------------------------------------------------
    |       Description        |                      Format                       |
    | Synchronize with PC tool |                  <STX><cmdSYNC>                   |
    | Send bootloader info     |                  <STX><cmdINFO>                   |
    | Go to bootloader mode    |                  <STX><cmdBOOT>                   |
    | Restart MCU              |                  <STX><cmdREBOOT>                 |
    | Write to MCU flash       | <STX><cmdWRITE><START_ADDR><DATA_LEN><DATA_ARRAY> |
    | Erase MCU flash.         |  <STX><cmdERASE><START_ADDR><ERASE_BLOCK_COUNT>   |
     ------------------------------------------------------------------------------ 
     
     * Acknowledge format.
   
    <CMD_CODE>
    |-- 2 ---|
   
    CMD_CODE - Index of command (TCmd) we want to acknowledge.
               Length: 2 byte. Mandatory.

    See 'Acknowledgement Table' below for details on specific command's 
    acknowledgement process.
    
    * Acknowledgement Table.
     --------------------------+---------------------------------------------------
    |       Description        |                   Acknowledgement                 |
    |--------------------------+---------------------------------------------------|
    | Synchronize with PC tool |                  upon reception                   |
    | Send bootloader info     |          no acknowledge, just send info           |
    | Go to bootloader mode    |                  upon reception                   |
    | Restart MCU              |                  no acknowledge                   |
    | Write to MCU flash       | upon each write of internal buffer data to flash  |
    | Erase MCU flash.         |                  upon execution                   |
   
"""
# Supported MCU families/types.
dMcuType = { "PIC16" : 1, 'PIC18':2, 'PIC18FJ':3, 'PIC24':4, 'dsPIC':10, 'PIC32': 20}

#define an INFO record
class info:
    McuType = ''
    McuId = 0
    McuSize = 0
    WriteBlock = 0
    EraseBlock = 0
    BootloaderRevision = 0
    DeviceDescription = ''
    BootStart = 0
    # additional fields 
    dHex = None

def getMCUtype( list, i):
    for item in dMcuType.items():
        if item[1] == list[i]:
            info.McuType = item[0]
            print "MCU type is:", info.McuType
            return i
    print "MCU type (%d) not recognized" % list[i]
    return i

def getMCUid( list, i):
    # MCUId appears not to be used anymore, report error
    print 'MCUId Info field found!?'
    exit(1)   

def getMCUSIZE( list, i):
    info.McuSize   = int(list[i+0]) + int(list[i+1])*256
    print "MCU size = %d" % info.McuSize
    return i+2

def getERASEB( list, i):
    info.EraseBlock = (int(list[i+0])+int( list[i+1])*256)
    print "ERASE Block = %d" % info.EraseBlock
    return i+2

def getWRITEB( list, i):
    info.WriteBlock = ( int(list[i+0])+int(list[i+1])*256)
    print "WRITE Block = %d" % info.WriteBlock
    return i+2

def getBOOTR( list, i):
    info.BootloaderRevision = ( int(list[i+0])+int(list[i+1])*256)
    print "Bootloader Revision = %x" % info.BootloaderRevision
    return i+2

def getBOOTS( list, i):
    info.BootStart = int(list[i+0]) + int(list[i+1])*256
    print "BOOT Start = 0x%x" % info.BootStart
    return i+2

def getDEVDSC( list, i):
    info.DeviceDescription = "".join(map( lambda x: chr(x), list[i : i+10]))
    print "Device Description: %s" % info.DeviceDescription
    return i+10

# Bootloader info field ID's enum 
dBIF = { 
        1: ('MCUTYPE', getMCUtype),   # MCU type/family (byte)
        2: ('MCUID',   getMCUid  ),   # MCU ID number ()
        3: ('ERASEBLOCK', getERASEB), # MCU flash erase block size (int)
        4: ('WRITEBLOCK', getWRITEB), # MCU flash write block size (int)
        5: ('BOOTREV',    getBOOTR),  # Bootloader revision (int)
        6: ('BOOTSTART',  getBOOTS),  # Bootloader start address (long)
        7: ('DEVDSC',     getDEVDSC), # Device descriptor (string[20])
        8: ('MCUSIZE',    getMCUSIZE) # MCU flash size (long)
        }
   
def DecodeINFO( list):
    print list
    size = list[2]
    index = 4
    while index<size:
        # print "index:",index
        try:
            f = dBIF[list[index]]   # find in the dictionary of valid fields
        except:
            print "Field %d at location %d not recognized!" % (list[index], index)
            return
        
        index = f[1](list, index+2)   # call decoding function

#--I2C layer--------------------------------------------------------------------
def InitI2C():
    # configure I2C 
    h.write( [ cmdI2CInit])
#    print "I2C port configured: ", h.read(1)[0] == 0x20
    # return true if successful
    return (h.read(1)[0] == cmdI2CInit)

def GetI2C():
    h.write( [ cmdI2CRead, DEVRead, 50])
    r = h.read(64)  # read the data back
#    if r[0] == cmdI2CRead:      #successful
    return r 


def SendI2C( cmd, largs):
    #           API           address   length      
    h.write( [ cmdI2CWrite, DEVWrite, 2+ len(largs), cmd, 0] + largs)
    # return true if successful
    return (h.read(1)[0] == cmdI2CWrite)

#-HID layer---------------------------------------------------------------------
def Enumerate():
    for d in hid.enumerate(0, 0):
        keys = d.keys()
        print 'manufacturer_string:',d['manufacturer_string']
        print 'vendor_id', d['vendor_id']
        print 'product_id:', d['product_id']
        print

def Check():
    try:
        hid.device( Microchip_vid, Clicker_pid)
    except( IOError):
        exit(1)
    exit(0)

def Connect():
    global h
    h = hid.device( Microchip_vid, Clicker_pid)
    Boot()              # RST and enter into boot mode 
    if InitI2C():       # access the I2C port
        print "I2C port initialized"
    Info()          # get the device infos

def ConnectLoop():
    print "Connecting..."
    for x in xrange(20): 
        if subprocess.call( ['python', 'HIDI2CBL16.py', '-check']):
            time.sleep(1)
        else:
            break;
        if x == 19: raise Timeout
        print "Reset board and keep checking ..."

    # check succeeded, obtain a handle 
    print "I2CBootloader found!"
    Connect()

#------Bootloader layer -----------------------------------------
def Boot():
    print "Enter BOOT mode ..", 
    h.write( [0x10])  # cmdRSTConfigure
    if h.read( 1)[0] != 0x10: return False
    h.write( [0x14])  # cmdCSConfigure
    if h.read( 1)[0] != 0x14: return False
    h.write( [0x16, 0]) #cmdCSWrite( 0)
    if h.read( 1)[0] != 0x16: return False
    h.write( [0x11])  # cmdRSTPulse
    if h.read( 1)[0] != 0x11: return False
    return True

def Info():
    print "Send the INFO command"
    SendI2C(  cmdINFO, [])
    DecodeINFO( GetI2C())

def Erase( block):
    # print "Erase: 0x%x " % block
    largs = extend16bit( [], block)     # starting address
    largs = extend16bit( largs, 1)      # no of  blocks
    #print "cmdErase", largs
    SendI2C( cmdERASE, largs)               
    r = GetI2C()                        # check reply
    if r[1] != cmdERASE: raise ERASE_ERROR
    
def WriteHalfRow( waddr):
    iaddr = waddr*2
    count = 16         # hard coded!!! a whole row does not fit in a single HID transaction
    largs = extend16bit( [], waddr)
    largs = extend16bit( largs, count)

    d = info.dHex                   # pick values out of the hex array
    for x in xrange( iaddr, iaddr+count*2,2):
       largs.extend( [d[x], d[x+1]])
       # largs.extend( [ x%32, 0])
    
    SendI2C( cmdWRITE, largs)         # send the command
    r = GetI2C()
    if r[1] !=  cmdWRITE: raise WRITE_ERROR


def ReBoot():
    # global h
    print "Rebooting the MCU!"
    h.write( [0x16, 1]) # cmdCSWrite( 1)
    if h.read( 1)[0] != 0x16: print "failed!"
    SendI2C( cmdREBOOT, [])
    Close()

def Close():
    # global h
    if h:
        h.close()

def Load( name):
    # init and empty code dictionary 
    info.dHex = None
    try:
        info.dHex = intelhex.IntelHex( name)
        return True
    except:
        return False

def extend16bit( lista, word):
    lista.extend([ word%256, word/256])
    return lista


def EmptyHalfRow( waddr):
    iaddr = waddr*2
    for x in xrange( 32):           # hard coded! work in max 16 words
        if info.dHex[ iaddr+x] != 0xff: return False
    return True

def Execute():
    # 1. fix the App reset vector 
    d = info.dHex                               
    a = (info.BootStart*2)-4                # copy appReset => BootStart -4
    for x in xrange(4):                     
        d[a+x] = d[x]

    # 2. fix the reset vector to point to BootStart
    v = extend16bit( [], info.BootStart) 
    #     high              movlp           low                  goto
    d[0]=0x80+(v[1]);   d[1]=0x31;      d[2]=v[0];      d[3]=0x28+( v[1] & 0x7) 
    # print "Reset Vector ->", v[1], v[0]
    # d[0] = 0x8E;            d[1]=0x31;      d[2]=0x00;      d[3]=0x2E
    #print d[0], d[1], d[2], d[3]

    # 3. erase blocks 1..last
    eblk = info.EraseBlock                      # compute erase block size in word
    last = info.BootStart / eblk                # compute number of erase blocks excluding Bootloader    
    print "Erasing ..."
    for x in xrange( 1, last):
        Erase( x * eblk)                        # erase one at a time

    # 4. program blocks 1..last (if not FF)
    wwblk = 16                                  # hard coded! half write block size to fit in HID transaction 
    last = info.BootStart / wwblk               # compute number of write blocks excluding Bootloader
    print "writeBlock= %d, last block = %d" % ( wwblk, last)
    for x in xrange( eblk/wwblk, last):         # write all  rows starting from second erase block
        if not EmptyHalfRow( x * wwblk):        # skip empty half rows
            # print "WriteRow( %X)" % (x * wwblk)
            WriteHalfRow( x * wwblk)            # write to device

    # 5. erase block 0
    Erase( 0)

    # 6. program all rows of block 0 
    for x in xrange( eblk/wwblk):          
       WriteHalfRow( x * wwblk)
        # print "WriteRow( %X)" % (x * wwblk)

###################################################################
# GUI window definition
#
class MainWindow():

    def __init__( self):
        global root
        bgc = 'light gray'
        bgd = 'ghost white'
        root = Tk()
        root.title( "PIC16 I2C HID Bootloader")
        #root.configure( bg=bgc)
        root.focus_set()
        root.geometry( '+400+100')
        root.protocol( 'WM_DELETE_WINDOW', root.quit) # intercept red button
        root.bind( sequence='<Command-q>', func= lambda e: e.widget.quit)

        root.grid_columnconfigure( 1, minsize=200)
        rowc = 0

        #------- top icon
        rowc += 1
        self.img = PhotoImage(file='mikroBootloader.png')
        Label( root, image=self.img).grid( padx=10, pady=5, columnspan=2, row=rowc, sticky=W)


        #---------- grid
        rowc += 1
        self.MCUType = StringVar()
        self.MCUType.set( 'None')
        Label( root, text="MCU Type:", width=10, bg=bgc).grid( padx=10, pady=5, row=rowc, sticky=W)
        Label( root, textvariable=self.MCUType, width=30, bg=bgd).grid( padx=10, pady=5, row=rowc, column=1, sticky=W)
        Button( root, text='1:Connect', width=15, bg=bgc, command=self.cmdInit).grid(
                padx=10, pady=5, row = rowc, column=2, sticky=N+W)

        rowc += 1
        self.Device = StringVar()
        self.Device.set( 'None')
        Label( root, text="Device:", width=10, bg=bgc).grid( padx=10, pady=5, row=rowc, sticky=W)
        Label( root, textvariable=self.Device, width=30, bg=bgd).grid( padx=10, pady=5, row=rowc, column=1, sticky=W)
        Button( root, text='2: Browse for HEX', width=15, command=self.cmdLoad).grid(
                padx=10, pady=5, row=rowc, column=2)

        rowc += 1
        self.fileHex = StringVar()
        Label( root, text="Hex:", width=10, bg=bgc).grid( padx=10, pady=5, row=rowc, sticky=W)
        Label( root, textvariable=self.fileHex, width=30, bg=bgd).grid( padx=10, pady=5, row=rowc, column=1, sticky=W)
        Button( root, text='3: Begin Uploading', width=15, command=self.cmdProgram).grid(
                padx=10, pady=5, row=rowc, column=2)
        
        #------- bottom row
        #------- status bar --------------------------------------
        rowc += 1
        self.Status = StringVar()
        self.Status.set( 'Uninitialized')
        Label( root, text="Status:", width=10, bg=bgc).grid( padx=10, pady=10, row=rowc, sticky=W)
        Label( root, textvariable=self.Status, width=30, bg=bgd).grid( padx=10, pady=10, row=rowc, column=1, columnspan=2, sticky=W)
        Button( root, text='Quit', width=15, command=root.quit).grid( padx=10, pady=10, row=rowc, column=2, sticky=E+S)

        # check if the file name is loadable
        global dHex
        name = ''
        if len(sys.argv) > 1:
            name = sys.argv[1]
            if not Load( name):
              self.Status.set( "File: %s not found!")
        self.fileHex.set( name)

    #------------------ main commands
    def cmdInit( self):
        if subprocess.call( ['python', 'HIDI2CBL16.py', '-check']):
            # failed to find 
            self.Status.set( "Reset board and try again...")
        else:
            # check succeeded, obtain a handle 
            try:
                Connect()
            except: 
                self.Status.set( "Clicker Not Found, connection failed")
            else:
                self.Status.set( "Clicker connected!")
                self.Device.set( info.DeviceDescription)
                self.MCUType.set( info.McuType)


    def cmdLoad( self):
        name = askopenfilename()
        if Load(name):
            self.Status.set( "Hex file loaded")
            self.fileHex.set( name)
        else:
            self.Status.set( "Invalid file name")
            self.fileHex.set( '')

    def cmdProgram( self):
        # Execute()
        # try:
            Execute()
        # except:
            # programming error 
            # self.Status.set( "Programming failed")
        # else:
            self.Status.set( "Programming successful")
            ReBoot()
            #root.destroy()

#----------------------------------------------------------------------------
# command line interface
#
if __name__ == '__main__':
    #discriminate if process is called with the check option
    if len(sys.argv) > 1:
        if sys.argv[1] == '-check':
            Check()

        if sys.argv[1] == '-gui':
            sys.argv.pop(1) # remove the option
            MainWindow()    
            mainloop()
            exit(0)

    # command line mode
    # if a file name is passed
    if len(sys.argv) == 1:
        print "Usage: %s (-gui) file.hex"
        exit(1)
    else:
        name = sys.argv[1]

    # load the hex file provided
    if not Load(name):
        print "File %s not found" % name
        exit(1)

    # loops until gets a connection
    ConnectLoop()

    # run the erase/program sequence
    Execute()

    # 
    ReBoot()


