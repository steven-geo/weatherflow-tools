from .core import *
import time

alert_json = {
    "devices": []
}

class Notifications():

    def open(self, savestatefile):
        self.starttime = int(time.time())
        self.savestatefile = savestatefile
        devices = alert_fileread(self.savestatefile)
        return devices

    def monitor(self):
        pass

    def offline(self,timeout = 360):
        """ Offline Device Status Check """
        notify_type = False
        notify_device = ''
        notify_event = ''
        notify_json = {}
        # Do not call for at least 2 minutes after startup to prevent false offline messages
        if int(time.time()) > ( self.starttime + 120):
            notify_type, notify_device, notify_event, notify_json = check_offline(timeout)
        return notify_type, notify_device, notify_event, notify_json

    def get_status(self, evt_json):
        return status(evt_json)

    def save_status(self):
        alert_filewrite(self.savestatefile)

    def close(self):
        if __debug__: print(json.dumps(alert_json, sort_keys=True, indent=4))
        alert_filewrite(self.savestatefile)

    def readconfig(self, filename):
        return alert_configread(filename)


def alert_configread(filename):
    saved_devices = 0
    config = {}
    try:
        with open(filename, "r") as jsonfile:
            config = json.load(jsonfile)
    except:
        pass
    return config

def alert_fileread(filename):
    global alert_json
    alert_json = {
        "devices": []
    }
    saved_devices = 0
    try:
        with open(filename, "r") as jsonfile:
            alert_json = json.load(jsonfile)
        if 'devices' in alert_json:
            saved_devices = len(alert_json['devices'])
    except:
        pass
    return saved_devices

def alert_filewrite(filename):
    global alert_json
    with open(filename, "w") as jsonfile:
        json.dump(alert_json, jsonfile, indent=4, sort_keys=True)
    return False


def is_json(myjson):
    """ Return True if source string is valid json """
    jsontype = 0
    try:
        json_object = json.loads(myjson)
        del json_object
        jsontype = 1  # Return Type of JSON
    except:
        pass
    try:
        json_object = json.loads(myjson.decode("utf-8"))
        del json_object
        jsontype = 2  # Return Type of JSON
    except:
        pass
    return json

def status(evt_json):
    notify_type = False
    notify_device = ''
    notify_event = ''
    notify_json = {}
    if 'type' in evt_json:
        if evt_json['type'] == 'device_status':
            notify_type, notify_device, notify_event, notify_json = station_alerts(evt_json)
        if evt_json['type'] == 'hub_status':
            notify_type, notify_device, notify_event, notify_json = hub_alerts(evt_json)
        if evt_json['type'] == 'evt_precip':
            notify_type, notify_device, notify_event, notify_json = precip_alerts(evt_json)
        if evt_json['type'] == 'evt_strike':
            notify_type, notify_device, notify_event, notify_json = strike_alerts(evt_json)
    return notify_type, notify_device, notify_event, notify_json


def get_battmode(volts, bm = 255):
    """ Weatherflow Battery Power Modes """
    if not 0 <= bm <= 3: bm = 255
    bmn = bm
    bv = float(volts)
    if bm == 255:
        if bv >= 2.455:
            bmn = 0
        elif bv >= 2.41:
             bmn = 1
        elif bv >= 2.375:
             bmn = 2
        else:
             bmn = 3
    else:
        if bm == 0 and bv <= 2.415:  # Mode 0 to Mode 1
            bmn = 1
        elif bm == 1 and bv <= 2.39:  # Mode 1 to Mode 2
            bmn = 2
        elif bm == 2 and bv <= 2.355:  # Mode 2 to Mode 3
            bmn = 3
        elif bm == 3 and bv < 2.375:  # Mode 3 to Mode 3
            bmn = 3
        elif bm >= 2 and bv >= 2.375:  # Mode 2/3 to Mode 2
            bmn = 2
        elif bm >= 1 and bv >= 2.41:  # Mode 1/2/3 to Mode 1
            bmn = 1
        elif bm >= 0 and bv >= 2.455:  # Mode 0/1/2/3 to Mode 0
            bmn = 0
        elif bm == 0 and bv > 2.415:  # Stay on Mode 0
            bmn = 0
        elif bm == 1 and bv > 2.39:  # Stay on Mode 1
            bmn = 1
        elif bm == 2 and bv > 2.355:  # Stay on Mode 2
            bmn = 2
        else:
            bmn = 5  # Battery Mode 5 - Invalid
    return bmn

def batt_modetext(batt_mode):
    if batt_mode == 0:
        text = "* All sensors enabled and operating at full performance\n* Wind sampling interval every 3 seconds"
    elif batt_mode == 1:
        text = "* Wind sampling interval set to 6 seconds"
    elif batt_mode == 2:
        text = "* Wind sampling interval set to one minute"
    elif batt_mode == 3:
        text = "* Wind sampling interval set to 5 minutes\n* All other sensors' sampling interval set to 5 minutes\n* Haptic Rain sensor disabled from active listening"
    else:
        text = "* ERROR - Invalid Battery Mode"
    return text

def add_device(serial):
    global alert_json
    if serial not in alert_json['devices']:
        alert_json['devices'].append(serial)
    return False

def create_barcode(serial):
    serial_number = serial[:-3]
    try:
        import treepoem
        image = treepoem.generate_barcode(barcode_type="datamatrix",data="00016063")
        # image.convert("1").save("barcode.png")
        return image
    except ImportError:
        return False

def precip_alerts(status_json):
    serial = status_json['Station Serial']
    notify_type = 'station'
    notify_device = serial
    notify_event = 'precip'
    notify_json = {}
    return notify_type, notify_device, notify_event, notify_json

def strike_alerts(status_json):
    serial = status_json['Station Serial']
    notify_type = 'station'
    notify_device = serial
    notify_event = 'strike'
    notify_json = {}
    try:
        notify_json['strike_distance'] = status_json['Distance (km)']
        notify_json['strike_energy'] = status_json['Energy']
    except:
        pass
    return notify_type, notify_device, notify_event, notify_json


def station_alerts(status_json):
    global alert_json
    serial = status_json['Device Serial']
    notify_type = False
    notify_device = serial
    notify_event = ''
    notify_json = {}

    # New Station Identified
    if serial not in alert_json:
        notify_event = 'new_ok'
        alert_json[serial] = {}  # Create new device in our status
        add_device(serial)
        if 'Station Firmware' in status_json:
            alert_json[serial]['firmware'] = int(status_json['Station Firmware'])
        else:
            notify_event = 'new_error'
            alert_json[serial]['station_fw'] = 0
        if 'Uptime (seconds)' in status_json:
            alert_json[serial]['uptime'] = int(status_json['Uptime (seconds)'])
        else:
            notify_event = 'new_error'
            alert_json[serial]['station_uptime'] = 0
        if 'Sensor Status' in status_json:
            alert_json[serial]['station_sensors'] = status_json['Sensor Status']
            if status_json['Sensor Status'] != "OK": notify_event = 'new_error'
        else:
            notify_event = 'new_error'
            alert_json[serial]['station_sensors'] = "Unknown"
        if 'Battery Voltage' in status_json:
            pass
        alert_json[serial]['type'] = 'station'
        alert_json[serial]['last_seen'] = int(time.time())
        alert_json[serial]['status'] = 'online'
        notify_type = 'hub'
        notify_type = 'station'
        notify_json = alert_json[serial]
        notify_json['Battery Health (%)'] = status_json['Battery Health (%)']
        return notify_type, notify_device, notify_event, notify_json

    # Update last seen value - time in epoch
    alert_json[serial]['last_seen'] = int(time.time())

    # Check if device was offline
    if alert_json[serial]['status'] != 'online':
        alert_json[serial]['status'] = 'online'
        notify_type = 'station'
        notify_event = 'online'
        alert_json[serial]['uptime'] = int(status_json['Uptime (seconds)'])
        notify_json = alert_json[serial]
        return notify_type, notify_device, notify_event, notify_json

    # Station Uptime Monitoring
    if 'Uptime (seconds)' in status_json:
        station_now = int(status_json['Uptime (seconds)'])
        if 'uptime' in alert_json[serial]:
            station_log = int(alert_json[serial]['uptime'])
            alert_json[serial]['uptime'] = station_now
            if station_log > station_now:
                notify_type = 'station'
                notify_event = 'reboot'
                notify_json = status_json
                notify_json['old_uptime'] = station_log
                return notify_type, notify_device, notify_event, notify_json

    # Station Firmware Monitoring
    if 'Station Firmware' in status_json:
        station_now = int(status_json['Station Firmware'])
        if 'firmware' in alert_json[serial]:
            station_log = int(alert_json[serial]['firmware'])
            if station_log != station_now:
                alert_json[serial]['firmware'] = station_now
                notify_type = 'station'
                notify_event = 'firmware'
                notify_json = status_json
                notify_json['old_firmware'] = station_log
                return notify_type, notify_device, notify_event, notify_json

    # Station Sensor Status Changes (on change)
    if 'Sensor Status' in status_json:
        station_now = status_json['Sensor Status']
        if 'station_sensors' in alert_json[serial]:
            station_log = alert_json[serial]['station_sensors']
            if station_log != station_now:
                alert_json[serial]['station_sensors'] = station_now
                alert_json[serial]['old_station_sensors'] = station_log
                notify_type = 'station'
                notify_json = alert_json[serial]
                if station_now == "OK":
                    notify_event = 'sensors_ok'
                else:
                    notify_event = 'sensors_error'
                return notify_type, notify_device, notify_event, notify_json
        else:
            alert_json[serial]['station_sensors'] = station_now

    # Station Battery Voltage Monitoring
    if 'Battery Voltage' in status_json:
        station_volts = float(status_json['Battery Voltage'])
        alert_json[serial]['battvolts'] = station_volts
        if 'battmode' in alert_json[serial]:
            station_log = float(alert_json[serial]['battmode'])
            batts = get_battmode(station_volts, station_log)
            if station_log != batts:
                alert_json[serial]['battmode'] = batts
                notify_json = alert_json[serial]
                notify_json['battvolts'] = station_volts
                notify_type = 'station'
                notify_event = 'batt_critical'
                if batts == 0:
                    notify_event = 'batt_ok'
                elif batts == 1:
                    notify_event = 'batt_low'
                elif batts == 2:
                    notify_event = 'batt_low'
                return notify_type, notify_device, notify_event, notify_json
        else:
            # If battmode doesnt exist in our status dictionary - add it
            alert_json[serial]['battmode'] = get_battmode(station_volts)

    return notify_type, notify_device, notify_event, notify_json

def hub_alerts(status_json):
    global alert_json
    serial = status_json['Hub Serial']
    notify_type = False
    notify_device = serial
    notify_event = ''
    notify_json = {}

    # New Hub Identified
    if serial not in alert_json:
        alert_json[serial] = {}  # Create new device in our status
        add_device(serial)
        if 'Hub Firmware' in status_json:
            alert_json[serial]['firmware'] = int(status_json['Hub Firmware'])
        else:
            alert_json[serial]['station_fw'] = 0
        if 'Uptime (seconds)' in status_json:
            alert_json[serial]['uptime'] = int(status_json['Uptime (seconds)'])
        else:
            alert_json[serial]['uptime'] = 0
        alert_json[serial]['type'] = 'hub'
        alert_json[serial]['last_seen'] = int(time.time())
        alert_json[serial]['status'] = 'online'
        notify_type = 'hub'
        notify_event = 'new_ok'
        notify_json = alert_json[serial]
        return notify_type, notify_device, notify_event, notify_json

    # Update last seen value - time in epoch
    alert_json[serial]['last_seen'] = int(time.time())

    # Check if device was offline
    if alert_json[serial]['status'] != 'online':
        alert_json[serial]['status'] = 'online'
        notify_type = 'hub'
        notify_event = 'online'
        notify_json = alert_json[serial]
        alert_json[serial]['uptime'] = int(status_json['Uptime (seconds)'])
        return notify_type, notify_device, notify_event, notify_json

    # Hub Uptime Monitoring
    if 'Uptime (seconds)' in status_json:
        station_now = int(status_json['Uptime (seconds)'])
        if 'uptime' in alert_json[serial]:
            station_log = int(alert_json[serial]['uptime'])
            alert_json[serial]['uptime'] = station_now
            if station_log > station_now:
                notify_type = 'hub'
                notify_event = 'reboot'
                notify_json = status_json
                notify_json['old_uptime'] = station_log
                return notify_type, notify_device, notify_event, notify_json

    # Hub Firmware Monitoring
    if 'Hub Firmware' in status_json:
        station_now = int(status_json['Hub Firmware'])
        if 'firmware' in alert_json[serial]:
            station_log = int(alert_json[serial]['firmware'])
            if station_log != station_now:
                alert_json[serial]['firmware'] = station_now
                notify_type = 'hub'
                notify_event = 'firmware'
                notify_json = status_json
                notify_json['old_uptime'] = station_log
                return notify_type, notify_device, notify_event, notify_json

    # TODO Hub Wifi RSSI Monitoring
    # "WiFi RSSI (dBm)": -41,
    # "WiFi RSSI Quality": "Excellent",

    return notify_type, notify_device, notify_event, notify_json

# device_status scheduled monitor
def check_offline(timeout):
    """ Check if something has gone offline by checking the last_seen agains current time """
    global alert_json
    notify_type = False
    notify_device = ''
    notify_event = ''
    notify_json = {}
    for device in alert_json['devices']:
        wf_now = int(time.time())
        wf_device = alert_json[device]['last_seen']
        wf_status = alert_json[device]['status']
        if wf_status == 'online' and (wf_device + timeout) < wf_now:
            print("Device is Offline: " + str(device))
            alert_json[device]['status'] = 'offline'
            notify_type = alert_json[device]['type']
            notify_device = device
            notify_event = 'offline'
            notify_json = alert_json[device]
            break
    return notify_type, notify_device, notify_event, notify_json

def notification(alert_type, alert_device, alert_event, alert_json):
    """ Turn the Raw data into a human readable notification with Status Types """
    # types can be - hub, station
    d_name = str(alert_type).capitalize()
    # events can be - new, firmware, reboot, offline, online, battery, lightning
    if alert_event in ['new_ok', 'online', 'batt_ok', 'sensors_ok']:
        msgstatus = 'ok'
    elif alert_event in ['firmware', 'reboot', 'batt_low']:
        msgstatus = 'warning'
    elif alert_event in ['new_error', 'offline', 'battery_critical', 'sensors_error']:
        msgstatus = 'error'
    elif alert_event in ['strike', 'precip']:
        msgstatus = 'info'
    else:
        msgstatus = 'error'
    # Process Messages for each Alert
    msgtitle = d_name + " " + str(alert_device) + " "
    msgtext = json.dumps(alert_json, sort_keys=True, indent=4)
    if alert_event == 'firmware':
        msgtitle += "Firmware has Changed"
        msgtext = "*Old Firmware:* " + str(alert_json['old_firmware']) + "\n*New Firmware:* " + str(alert_json['Station Firmware'])
    elif alert_event == 'reboot':
        msgtitle += "Has Rebooted"
        msgtext = "Uptime was: " + str(alert_json['old_uptime']) + " seconds (" + get_secondstext(alert_json['old_uptime']) + ")"
        if 'Reset Reasons' in alert_json:
            msgtext += "\nReset Reason: " + str(alert_json['Reset Reasons'])
    elif alert_event == 'offline':
        msgtitle += "Has Gone Offline"
        msgtext = "Uptime was: " + str(alert_json['uptime']) + " seconds (" + get_secondstext(alert_json['uptime']) + ")"
    elif alert_event == 'online':
        msgtitle += "Is Now Back Online"
        msgtext = "Uptime is: " + str(alert_json['uptime']) + " seconds (" + get_secondstext(alert_json['uptime']) + ")"
    elif alert_event == 'batt_ok':
        msgtitle += "Battery is now OK - Mode 0"
        msgtext = "Battery Voltage is: " + str(alert_json['battvolts']) + "\n" + batt_modetext(alert_json['battmode'])
    elif alert_event == 'batt_low':
        msgtitle += "Battery is Low - Mode " + str(alert_json['battmode'])
        msgtext = "Battery Voltage is: " + str(alert_json['battvolts']) + "\n" + batt_modetext(alert_json['battmode'])
    elif alert_event == 'batt_critical':
        msgtitle += "Battery is Critical - Mode " + str(alert_json['battmode'])
        msgtext = "Battery Voltage is: " + str(alert_json['battvolts']) + "\n" + batt_modetext(alert_json['battmode'])
    elif alert_event == 'strike':
        msgtitle += "Lightning has Been Detected"
        if ('strike_distance' in alert_json) and ('strike_energy' in alert_json):
            msgtext = "Lightning @ " + str(alert_json['strike_distance']) + " km\nEnergy Level is " + str(alert_json['strike_energy'])
    elif alert_event == 'precip':
        msgtitle += "Rain has Been Detected"
        msgtext = "It is Raining"
    elif alert_event == 'sensors_ok':
        msgtitle += "Sensor Status is now OK"
        msgtext = "Was: " + str(alert_json['old_station_sensors'])
        msgtext += "\nBattery Status: " + str(alert_json['battvolts'])
        msgtext += "\nBattery Mode: " + str(alert_json['battmode'])
    elif alert_event == 'sensors_error':
        msgtitle += "Sensor Status has changed - FAILURE"
        msgtext = "Sensor Status is: " + str(alert_json['station_sensors'])
        msgtext += "\nSensor Status Was: " + str(alert_json['old_station_sensors'])
        msgtext += "\nBattery Status: " + str(alert_json['battvolts'])
        msgtext += "\nBattery Mode: " + str(alert_json['battmode'])
    elif alert_event == 'new_ok' or alert_event == 'new_error':
        msgtitle += "has been Identified"
        msg_image = create_barcode(str(alert_device))
        msgtext = "*Serial*: " + str(alert_device) + \
                  "\n*Firmware*: " + str(alert_json['firmware']) + \
                  "\n*Uptime*: " + get_secondstext(alert_json['uptime'])
        if alert_type == 'station':
            msgtext += "\n*Sensor Status*: " + alert_json['station_sensors']
            msgtext += "\n*Battery Status*: " + str(alert_json['battvolts'])
            msgtext += "\n*Battery Health*: " + str(alert_json['Battery Health (%)']) + "%"
    else:
        msgtitle += "Unknown Event"
        msgtext = "type:" + str(alert_type) + " - topic:" + str(alert_event)
    return msgtitle, msgtext, msgstatus
