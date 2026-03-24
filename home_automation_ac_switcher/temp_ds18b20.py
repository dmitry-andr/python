# Complete Project Details: https://RandomNerdTutorials.com/raspberry-pi-ds18b20-python/

# Based on the Adafruit example: https://github.com/adafruit/Adafruit_Learning_System_Guides/blob/main/Raspberry_Pi_DS18B20_Temperature_Sensing/code.py

import os
import glob
import time
from pathlib import Path
 
os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')


SENSOR_NOT_CONNECTED_STATUS = 'no_temperature_sensor_connected'
W1_DEVICES_BASE_DIR = '/sys/bus/w1/devices/'
#device_folder = glob.glob(base_dir + '28*')[0]
#device_file = device_folder + '/w1_slave'


def is_w1_thermo_data_available():
    counter = 0
    for path in Path(W1_DEVICES_BASE_DIR).glob('28*'):
        if path.exists():
            counter += 1
    return counter > 0
    
def get_device_file():
    if is_w1_thermo_data_available():
        device_folder = glob.glob(W1_DEVICES_BASE_DIR + '28*')[0]
        return device_folder + '/w1_slave'
    else:
        return None

def read_temp_raw():
    device_file = get_device_file()
    if device_file is None:
        return SENSOR_NOT_CONNECTED_STATUS
    f = open(device_file, 'r')
    lines = f.readlines()
    f.close()
    return lines

def read_temp():
    lines = read_temp_raw()
    if lines == SENSOR_NOT_CONNECTED_STATUS:
        return SENSOR_NOT_CONNECTED_STATUS
    while lines[0].strip()[-3:] != 'YES':
        time.sleep(0.2)
        lines = read_temp_raw()
    equals_pos = lines[1].find('t=')
    if equals_pos != -1:
        temp_string = lines[1][equals_pos+2:]
        temp_c = float(temp_string) / 1000.0
        return temp_c