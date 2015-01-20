#
# testing the I2C response to the PIC16High Bootloader 
#
import hid

h = hid.device(1240, 0x3f)

h.write( [0x20])  #initialize the I2C port
if  (h.read( 64)[0] == 0x20):
    print "I2C init ok"

print "sending Info command"
h.write( [ 0x22, 0x90, 2, 2, 0])        # command 2 -> info
r =  h.read(64)
if (r[0] == 254):
    print "Nack"
elif (r[0] == 255):
    print "Stuck"
elif (r[0] == 0x22):
    print "Command OK"


# now send the read command to get the Info block
print "Sending a read command"
h.write( [ 0x21, 0x91, 60 ])
r = h.read(64)

if (r[0] == 0x21):
    print r
elif (r[0] == 254):
    print "Nack"
elif (r[0] == 255):
    print "Stuck"



