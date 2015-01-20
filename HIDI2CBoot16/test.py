from intelhex import *


def EmptyRow( addr, dHex):
    for x in xrange(256):
        if dHex[ addr+x] != 0xff: return False
    return True


if __name__ == '__main__':
    d = IntelHex( 'Alarm.hex')

    for x in xrange( 0, 256):
        print d[0x20428*2 + x],
    print

    print EmptyRow( 0x20428*2, d)
    print hex(0x20428*2)

    for x in xrange( 0, 0x29800*2/128):        # write all  rows starting from second erase block
        if EmptyRow( x * 256, d):           # skip empty rows
            print "WriteRow( %X)" % (x * 256)
            pass