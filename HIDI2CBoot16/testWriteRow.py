from intelhex import *


def getIntelFromWords( waddr):
    return waddr*2

def getIntelFromBytes( bytes):
    return (bytes/3) * 4

if __name__ == '__main__':
    d = IntelHex( 'Alarm.hex')

    # for x in xrange( 256):
        # d[x] = x

    cmd = []
    iaddr = getIntelFromWords( 0)
    count = 192         # number of bytes

    # test write sequential values
    # cmd.extend( range( count))

    for x in xrange( iaddr, iaddr+getIntelFromBytes(count)):
        d[x] = x & 0xff


    # for x in xrange( )

    # pick values out of the hex array
    # d = info.dHex
    for x in xrange( iaddr, iaddr+getIntelFromBytes(count), 4):
        cmd.extend( [ d[x], d[x+1], d[x+2]])

    for i, x in enumerate(cmd):
        if i % 16 == 0:
            print
        print '%02X' % x,

    while cmd:
        print cmd[:8]
        cmd = cmd[8:]