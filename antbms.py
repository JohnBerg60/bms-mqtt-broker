import sys
import time
import argparse
import struct
import json
import serial
import paho.mqtt.client as mqttClient

import logging

logging.basicConfig(
    level=logging.INFO,
    format="[%(name)s] %(message)s",
    handlers=[
        logging.FileHandler("/var/log/bms.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

log = logging.getLogger('bms')

MSG_LEN = 140

def openCommPort(port):
    try:    
        return serial.Serial(port=port, baudrate = 9600, parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS, timeout = 1)
    except:
        return False


def initMqttClient():
    try:
        mqttc = mqttClient.Client(client_id='BMS')
        mqttc.username_pw_set('johnberg', password='jsat1234')
        mqttc.connect('localhost', 1883, 60)
        mqttc.loop()

        volt_discover = {
	       "state_topic": "bms/battery_voltage",
	        "icon": "mdi:battery",
	        "name": "BMS Battery Voltage",
            "unique_id": "bms_battery_voltage",
	        "unit_of_measurement": "V",
        }

        amps_discover = {
	        "state_topic": "bms/battery_current",
	        "icon": "mdi:battery",
	        "name": "BMS Battery Current",
    	    "unique_id": "bms_battery_current",
	        "unit_of_measurement": "A",
        }

        remain_discover = {
	        "state_topic": "bms/battery_remain",
	        "icon": "mdi:battery-50",
	        "name": "BMS Battery Remaining AH",
	        "unique_id": "bms_battery_remain",
	        "unit_of_measurement": "AH",
        }

        power_discover = {
	        "state_topic": "bms/battery_power",
	        "icon": "mdi:power-plug-outline",
	        "name": "BMS Battery Power",
	        "unique_id": "bms_battery_power",
	        "unit_of_measurement": "W",
        }

        temp_discover = {
	        "state_topic": "bms/battery_temp",
    	    "icon": "mdi:thermometer",
	        "name": "BMS Battery Temperature",
	        "unique_id": "bms_battery_temp",
	        "unit_of_measurement": "°C",
        }

        mqttc.publish("homeassistant/sensor/bms/battery_voltage/config", json.dumps(volt_discover))
        mqttc.publish("homeassistant/sensor/bms/battery_current/config", json.dumps(amps_discover))
        mqttc.publish("homeassistant/sensor/bms/battery_remain/config", json.dumps(remain_discover))
        mqttc.publish("homeassistant/sensor/bms/battery_power/config", json.dumps(power_discover))
        mqttc.publish("homeassistant/sensor/bms/battery_temp/config", json.dumps(temp_discover))
        time.sleep(1)

        return mqttc
    except Exception as e:
        log.error('exception during mqtt publisch: '+ str(e))
        return False

#
#   Read from serial port 
#
def readFromPort(ser):
    try:
        if not ser.isOpen():
            ser.open()        

        bytesWritten = ser.write (bytearray.fromhex('DBDB00000000'))
        if  bytesWritten != 6:
            log.debug(f'did not write 6 bytes to bms, actually written {bytesWritten}')

        l = 0
        #wait for MSG_LEN bytes to be ready (max 100 x 0.2 sec)
        while l < 100 and ser.in_waiting < MSG_LEN:
            l = l + 1
            time.sleep(0.3)

        bytesWaiting = ser.in_waiting
        if bytesWaiting != MSG_LEN:
            log.debug(f'bms did not return {MSG_LEN} bytes, actually {bytesWaiting}')        
        return ser.read(MSG_LEN)
    except Exception as e:
        log.error('exception during read from port: '+ str(e))
        return False

#
#   Main program 
#
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--port', nargs='?', 
        help='the comm port to the bms (default: %(default)s)', default='/dev/rfcomm2')
    parser.add_argument("-v", "--verbose", help="increase output verbosity", action="store_true")
    args = parser.parse_args()

    # setup logging
    if args.verbose:
        log.setLevel(logging.DEBUG)

    ser = openCommPort(args.port)
    if not ser:
        log.error(f'cannot open serial port {args.port}, terminating')
        exit(1)

    mqttc = initMqttClient()
    if not mqttc:
        log.error('cannot initialize mqtt client, terminating')
        exit(2)
    
    log.info('start sending data to the mqtt broker')
    error = False
    while not error:
        resp = readFromPort(ser)
        if not resp or len(resp) != MSG_LEN:
            #something went wrong
            log.debug('reading from port failed, try again in 5 seconds')
            time.sleep(5)
        else:
            volt = struct.unpack('>H', resp[4:6])[0] / 10
            current = struct.unpack('>i', resp[70:74])[0] / 10
            remain = format(struct.unpack('>i', resp[79:83])[0] / 1000000, '.3f')
            power = format(struct.unpack('>i', resp[111:115])[0] / 1, '.0f')
            temp = struct.unpack('>h', resp[91:93])[0]            

            mqttc.publish("bms/battery_voltage", volt)
            mqttc.publish("bms/battery_current", current)
            mqttc.publish("bms/battery_remain", remain)
            mqttc.publish("bms/battery_power", power)
            mqttc.publish("bms/battery_temp", temp)

            time.sleep(1)

    if ser.isOpen():
        ser.close()

    log.debug('exit normaly')
    exit(0)