#
# read data from bms and sent to mqtt broker
#
# protocol: https://github.com/klotztech/VBMS/wiki/Serial-protocol?fbclid=IwAR3pigiLZZX0mqAzlmP-tSmURCAUn4wFb11SW8T9qkK7nVeStFZ_A9uX53Q
# mqtt: https://www.eclipse.org/paho/index.php?page=clients/python/docs/index.php

import sys
import time
import struct
import json
import serial
import paho.mqtt.client as mqttc
import logging

logger = logging.getLogger(__name__)

logging.basicConfig(filename='/var/log/bms.log',
                            filemode='a',
                            format='%(asctime)s  %(levelname)s %(message)s',
                            datefmt='%H:%M:%S',
                            level=logging.DEBUG)

logging.info("Starting bms mqtt broker")


mqttc = mqttc.Client(client_id='BMS')
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

comm_discover = {
	"state_topic": "bms/communication",
	"icon": "mdi:serial-port",
	"name": "BMS Serial communication",
	"unique_id": "bms_communication"
}

remain_discover = {
	"state_topic": "bms/battery_remain",
	"icon": "mdi:battery-50",
	"name": "BMS Battery Remaining AH",
	"unique_id": "bms_battery_remain",
	"unit_of_measurement": "AH",
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
mqttc.publish("homeassistant/sensor/bms/communication/config", json.dumps(comm_discover))
mqttc.publish("homeassistant/sensor/bms/battery_remain/config", json.dumps(remain_discover))
mqttc.publish("homeassistant/sensor/bms/battery_temp/config", json.dumps(temp_discover))
time.sleep(1)

ser = serial.Serial(
    port='/dev/rfcomm3',
    baudrate = 9600,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS,
    timeout = 1)

i = 0
comm = 0
while i < 1200:
    i = i + 1    
    mqttc.publish("bms/communication", comm)

    time.sleep(1)

    try:   
        if not ser.isOpen():
            ser.open()
    except:
        logger.exception('cannot open serial port')
        comm = 1
    else:
        try:
            l = ser.write (bytearray.fromhex('DBDB00000000'))
        except:
            logger.exception ('serial write failed')
            comm = 2
        else:
            l = 0
            #wait for 140 bytes to be ready (max 10 x 0.2 sec)
            while l < 20 and ser.in_waiting < 140:
                l = l + 1
                time.sleep(0.2)
    
            if ser.in_waiting < 140:
                logger.exception ('serial read failed')
                comm = 3
            else:
    
                resp = ser.read(140)

                comm = 0

                volt = struct.unpack('>H', resp[4:6])[0] / 10
                current = struct.unpack('>i', resp[70:74])[0] / 10
                remain = format(struct.unpack('>i', resp[79:83])[0] / 1000000, '.3f')
                power = struct.unpack('>i', resp[111:115])[0]
                temp = struct.unpack('>h', resp[91:93])[0]            

                mqttc.publish("bms/battery_voltage", volt)
                mqttc.publish("bms/battery_current", current)
                mqttc.publish("bms/battery_remain", remain)
                mqttc.publish("bms/battery_temp", temp)


if ser.isOpen():
    ser.close()