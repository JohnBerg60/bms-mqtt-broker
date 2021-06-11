import sys
import argparse
import struct
import json
import serial

def openCommPort(port):
    try:    
        return serial.Serial(port=port, baudrate = 9600, parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS, timeout = 1)
    except:
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--port', nargs='?', 
        help='the comm port to the bms (default: %(default)s)', default='/dev/rfcomm3')
    args = parser.parse_args()
    ser = openCommPort(args.port)
    if not ser:
        print('cannot open serial port %s, terminating' % (args.port))
        exit(1)

    if ser.isOpen():
        ser.close()

    print('all is ok')