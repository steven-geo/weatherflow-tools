import socket
from datetime import datetime
import time
import sys
import json

# Update these Values to suit
WEATHERFLOW_PORT = 50222
WEATHERFLOW_IP = "255.255.255.255"
WEATHERFLOW_STN_SERIAL = 'ST-99999123'
WEATHERFLOW_HUB_SERIAL = 'HB-99998234'
TEST_DEVICE_STATUS = '{"hub_rssi": 0, "debug": 0, "type": "device_status", "sensor_status": 0, "uptime": 0, "rssi": -51, "hub_sn": "", "voltage":  2.58, "serial_number": "", "firmware_revision": 0, "timestamp": 0}'

def create_station_test(firmware = 100, uptime = 1000, battery = 2.666, sensors = 0):
    wf_pkt = json.loads(TEST_DEVICE_STATUS)
    wf_pkt['timestamp'] = int(time.time())
    wf_pkt['hub_sn'] = WEATHERFLOW_HUB_SERIAL
    wf_pkt['serial_number'] = WEATHERFLOW_STN_SERIAL
    wf_pkt['uptime'] = int(uptime)
    wf_pkt['voltage'] = float(battery)
    wf_pkt['firmware_revision'] = int(firmware)
    wf_pkt['sensor_status'] = sensors
    print(json.dumps(wf_pkt, sort_keys=True, indent=4))
    return bytes(json.dumps(wf_pkt), encoding="utf8")

def wfsend(socket, send_pkt):
    socket.sendto(send_pkt, (WEATHERFLOW_IP, WEATHERFLOW_PORT))
    time.sleep(3)
    return False

def station_test_battery(weatherflow):
    wfsend(weatherflow, create_station_test(battery = 2.59))
    wfsend(weatherflow, create_station_test(battery = 2.59))
    print("Test OK -> Low Battery Notification")
    print("Message: ")
    wfsend(weatherflow, create_station_test(battery = 2.39))
    print("Test Low -> Critical Battery Notification")
    print("Message: ")
    wfsend(weatherflow, create_station_test(battery = 2.29, firmware = 102))
    print("Test Critical -> Low Battery Notification")
    print("Message: ")
    wfsend(weatherflow, create_station_test(battery = 2.37, firmware = 102))
    print("Test Low -> OK Battery Notification")
    print("Message: ")
    wfsend(weatherflow, create_station_test(battery = 2.48, firmware = 102))
    print("Test OK -> Critical Battery Notification")
    print("Message: ")
    wfsend(weatherflow, create_station_test(battery = 2.28, firmware = 102))
    print("Test Critical -> OK Battery Notification")
    print("Message: ")
    wfsend(weatherflow, create_station_test(battery = 2.66, firmware = 102))

def station_test_sensors(weatherflow):
    print("Message: New Station or no notification if already exists")
    wfsend(weatherflow, create_station_test())
    print("Message: New Station or no notification if already exists")
    wfsend(weatherflow, create_station_test())
    print("Message: Station Sensors Failed")
    wfsend(weatherflow, create_station_test(sensors = 328))
    print("Message: Station Sensors are OK")
    wfsend(weatherflow, create_station_test(sensors = 0))

def station_test_new(weatherflow):
    print("test New/Start - should only notify if device hasn't been online before")
    wfsend(weatherflow, create_station_test())

def station_test_firmware(weatherflow):
    print("test Status report - Should not raise a notification")
    print("Message: New Station or no notification if already exists")
    wfsend(weatherflow, create_station_test())
    print("Test Firmware Updated notification")
    print("Message: Firmware has changed")
    wfsend(weatherflow, create_station_test(firmware = 101))

def station_test_reboot(weatherflow):
    print("Test Reboot Notification")
    print("Message: Has Rebooted")
    wfsend(weatherflow, create_station_test(uptime = 600, firmware = 101))
    print("Test Uptime is lower and Firmware has incrememented")
    print("Message: Has Rebooted")
    wfsend(weatherflow, create_station_test(uptime = 30, firmware = 102))
    print("Repeated Message Above")
    print("Message: Firmware has Changed")
    wfsend(weatherflow, create_station_test(uptime = 30, firmware = 102))
    wfsend(weatherflow, create_station_test(uptime = 30, firmware = 102))

def station_test_offline(weatherflow):
    wfsend(weatherflow, create_station_test(firmware = 102, uptime = 100))
    print("Test Device Offline - Waiting 130 seconds")
    print("Message: ")
    time.sleep(140)
    print("Test Device Online")
    wfsend(weatherflow, create_station_test(firmware = 102, uptime = 100))


def main():
    """ Main Service Loop """
    # Open Weatherflow Socket so we can send UDP Packets
    weatherflow = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
    weatherflow.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    weatherflow.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    station_test_sensors(weatherflow)

    weatherflow.close()
    return False

main()
