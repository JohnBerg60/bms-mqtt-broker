#!/bin/bash

# bind rfcomm1 to the odb2 adapter
/usr/bin/rfcomm bind /dev/rfcomm1 00:1D:A5:07:E8:60

# bind rfcomm2 to ant-bms
/usr/bin/rfcomm bind /dev/rfcomm2 AA:BB:CC:A1:23:45