import sys
import time
import argparse
import struct
import json
import serial
import paho.mqtt.client as mqttClient

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
    	    "icon": "mdi:battery-charging-wireless-50",
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
    except:
        return False

#
#   Read from serial port 
#
def readFromPort(ser):
    try:
        if not ser.isOpen():
            ser.open()
        

        if ser.write (bytearray.fromhex('DBDB00000000')) != 6:
            print("did not write command to bms")

        l = 0
        #wait for 140 bytes to be ready (max 100 x 0.2 sec)
        while l < 100 and ser.in_waiting < 140:
            l = l + 1
            time.sleep(0.3)

        if ser.in_waiting != 140:
            print('bms did not return date, size = %i' % (ser.in_waiting))
        return ser.read(140)
    except:
        return False


#
#   Main program 
#
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--port', nargs='?', 
        help='the comm port to the bms (default: %(default)s)', default='/dev/rfcomm2')
    args = parser.parse_args()
    ser = openCommPort(args.port)
    if not ser:
        print('cannot open serial port %s, terminating' % (args.port))
        exit(1)

    mqttc = initMqttClient()
    if not mqttc:
        print('cannot initialize mqtt client, terminating')
        exit(2)
    
    print('start sending data to the mqtt broker')
    error = False
    while not error:
        resp = readFromPort(ser)
        if not resp or len(resp) != 140:
            #something went wrong
            print('reading from port failed, try again in 5 seconds')
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

    print('all is ok')
    exit(0)