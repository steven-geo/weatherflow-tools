""" Log Tempest Packets to Console """
import json
import logging
import datetime
import sys
import socket

# Timeout in seconds - recommend 10 seconds and should be < 60 seconds
# This ensures we don't block our main loop for too long waiting to Rx
WEATHERFLOW_UDP_TIMEOUT = 10

# This code is based off the WeatherFlow Tempest UDP Reference - v170
# https://weatherflow.github.io/Tempest/api/udp/v170/

# use for uptime text routine
INTERVALS = (
    ('weeks', 604800),  # 60 * 60 * 24 * 7
    ('days', 86400),    # 60 * 60 * 24
    ('hours', 3600),    # 60 * 60
    ('minutes', 60),
    ('seconds', 1),
    )

# map type 'obs_st' obs List Object
MAP_OBS_ST = [
    "Time (epoch)",
    "Wind Lull (m/s)",
    "Wind Average (m/s)",
    "Wind Gust (m/s)",
    "Wind Direction (degrees)",
    "Wind Sample Interval (seconds)",
    "Station Pressure (millibars)",
    "Air Temperature (C)",
    "Relative Humidity (%)",
    "Illuminance (Lux)",
    "UV Index",
    "Solar Radiation (W/m^2)",
    "Rain over passed minute (mm)",
    "Precipitation Type",
    "Lightning Strike Avg Distance (km)",
    "Lightning Strike Count",
    "Battery Voltage",
    "Report Interval"
]

# map type 'rapid_wind' obs List Object
MAP_RAPID_WIND = [
    'Time Epoch',
    'Wind Speed (m/s)',
    'Wind Direction (degrees)'
]

# map type 'evt_strike' obs List Object
MAP_EVT_STRIKE = [
    'Time Epoch',
    'Distance (km)',
    'Energy'
]

class Connect:
    def __init__(self, ip = '255.255.255.255', port = 50222, privacy = False, buffer = 4096):
        """ Initilise """
        self.tempest = opensocket(ip, port)
        self.privacy = privacy
        self.buffersize = buffer

    def close(self):
        """ Closing Resources """
        if self.tempest:
            self.tempest.close()
        if __debug__: print("Closing WeatherFlow Routines")

    def get_event(self):
        wf_type = False
        wf_serial = None
        wf_json = {
            "error": "Failure in Receiving/Decoding Packet",
            "value": ""
        }
        data = "{}".encode()
        try:
            data, addr = self.tempest.recvfrom(self.buffersize)
            if is_json(data.decode("utf-8")):
                wf_pkt = json.loads(data.decode("utf-8"))
                if 'type' in wf_pkt:
                    wf_type_pkt = str(wf_pkt['type'])
                    if 'serial_number' in wf_pkt:
                        wf_serial = get_serial(wf_pkt)
                    else:
                        wf_serial = None
                    if wf_type_pkt == 'obs_st':
                        wf_type, wf_json = msg_obs_st(wf_pkt, self.privacy)
                    elif wf_type_pkt == 'device_status':
                        wf_type, wf_json = msg_device_status(wf_pkt, self.privacy)
                    elif wf_type_pkt == 'rapid_wind':
                        wf_type, wf_json = msg_rapid_wind(wf_pkt, self.privacy)
                    elif wf_type_pkt == 'evt_strike':
                        wf_type, wf_json = msg_evt_strike(wf_pkt, self.privacy)
                    elif wf_type_pkt == 'evt_precip':
                        wf_type, wf_json = msg_evt_precip(wf_pkt, self.privacy)
                    elif wf_type_pkt == 'hub_status':
                        wf_type, wf_json = msg_hub_status(wf_pkt, self.privacy)
                else:
                    wf_json = {
                        "error": "Unknown Json Payload type",
                        "value": str(wf_pkt)
                    }
            else:
                wf_json = {
                    "error": "Non Json or invalid packet received",
                    "value": None
                }
        except socket.timeout:
            wf_json = {
                "error": "UDP Packet Timeout of " + str(WEATHERFLOW_UDP_TIMEOUT) + " seconds exceeded",
                "value": "This could be because no weather stations are online"
            }
            pass
        except ValueError as e:
            wf_json = {
                "error": "Exception Value Error",
                "value": str(e),
                "line": except_line()
            }
        except TypeError as e:
            wf_json = {
                "error": "Exception Type Error",
                "value": str(e),
                "line": except_line()
            }
        except KeyboardInterrupt as e:
            wf_type = False
            wf_json = {
                "error": "Interupt",
                "value": None
            }
            wf_serial = None
            raise
        except:
            wf_json = {
                "error": "Exception Error",
                "value": "unknown error",
                "line": except_line()
            }
            raise
        return wf_type, wf_serial, wf_json

def except_line():
    """ When an exception occurs retrieve the line number """
    exception_type, exception_object, exception_traceback = sys.exc_info()
    line_number = exception_traceback.tb_lineno
    return str(line_number)

def opensocket(wf_ip, wf_port):
    # Open WeatherFlow RX Socket - Normally on port 50222
    tempest = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) # UDP
    tempest.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    tempest.bind((wf_ip, wf_port))
    tempest.settimeout(WEATHERFLOW_UDP_TIMEOUT)  # Timeout in seconds - ensure main loop cycles every now and then for offline device check
    return tempest

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

# #########################################################################
# ######    WEATHERFLOW COMMON MESSAGE HANDLING DETAIL ROUTINES     #######
# #########################################################################

def get_uptime(myjson):
    """ Get uptime in Seconds and return human readable day, hours, min, seconds based on granularity """
    text = "Uptime Not Available"
    try:
        if 'uptime' in myjson:
            text = get_secondstext(int(myjson['uptime']),3)
    except:
        pass
    return text

def get_secondstext(seconds, granularity=3):
    seconds = int(seconds)
    text = "Uptime Not Available"
    result = []
    for name, count in INTERVALS:
        value = seconds // count
        if value:
            seconds -= value * count
            if value == 1:
                name = name.rstrip('s')
            result.append("{} {}".format(value, name))
    text = ', '.join(result[:granularity])
    return text

def epoch_text(epoch):
    return str(datetime.datetime.fromtimestamp(float(epoch)))

def get_serial(myjson,privacy=False):
    """ Serial Number of Tempest Station or HUB """
    serial_text = "Unknown"
    if 'type' in myjson:
        if 'serial_number' in myjson:
            serial_text = myjson['serial_number']
    if privacy:
        serial_text = serial_text[:-3] + "xxx"
    return str(serial_text)  # Return long String (Full Model and Serial)

def get_hub_sn(myjson,privacy=False):
    """ Serial Number of Tempest Station or HUB """
    serial_text = "Unknown"
    if 'type' in myjson:
        if 'serial_number' in myjson:
            serial_text = myjson['hub_sn']
    if privacy:
        serial_text = serial_text[:-3] + "xxx"
    return str(serial_text)  # Return long String (Full Model and Serial)

def get_firmware(myjson):
    """ Get Firmware version from Json Payload """
    firmware_text = "Unknown"
    if 'type' in myjson:
        if myjson['type'] == 'device_status' or myjson['type'] == 'hub_status':
            if 'firmware_revision' in myjson:
                firmware_text = "Firmware Ver " + str(myjson['firmware_revision'])
    return firmware_text

def get_rssi_text(rssi):
    """ Based on RSSI provide a Quality name """
    if rssi >= -50:
        rssi_text = "Excellent"
    elif rssi >= -60:
        rssi_text = "Very Good"
    elif rssi >= -70:
        rssi_text = "Good"
    elif rssi >= -80:
        rssi_text = "Low"
    elif rssi >= -90:
        rssi_text = "Very Low"
    elif rssi >= -100:
        rssi_text = "Poor"
    else:
        rssi_text = "Bad"
    return rssi_text


# #########################################################################
# ##############    HUB MESSAGE HANDLING DETAIL ROUTINES     ##############
# #########################################################################

def get_hub_reset_flags(flags):
    text = ""
    if 'BOR' in flags: text+="Brownout reset|"
    if 'PIN' in flags: text+="PIN reset|"
    if 'POR' in flags: text+="Power reset|"
    if 'SFT' in flags: text+="Software reset|"
    if 'WDG' in flags: text+="Watchdog reset|"
    if 'WWD' in flags: text+="Window watchdog reset|"
    if 'LPW' in flags: text+="Low-power reset|"
    return text[:-1]

def get_hub_radio_stats_status_text(status):
    status_int = int(status)
    if status_int & 1:
        text = "Radio On|"
    else:
        text = "Radio Off|"
    if status_int & 2:
        text += "Radio Active|"
    if status_int & 4:
        text += "BLE Connected|"
    return text[:-1]

def msg_hub_status(myjson, privacy = False, raw = False):
    """ Process JSON Packet from WeatherFlow Hub - hub_status """
    text = {}
    wf_type = False
    if 'type' in myjson:
        if myjson['type'] == 'hub_status':
            try:
                text['Hub Serial'] = get_serial(myjson, privacy)
                text['Hub Firmware'] = myjson['firmware_revision']
                text['Uptime (seconds)'] = myjson['uptime']
                text['Uptime (text)'] = get_uptime(myjson)
                text['WiFi RSSI (dBm)'] = myjson['rssi']
                text['WiFi RSSI Quality'] = get_rssi_text(myjson['rssi'])
                text['Reset Reasons'] = get_hub_reset_flags(myjson['reset_flags'])
                text['Sequence'] = myjson['seq']
                if 'radio_stats' in myjson:
                    radstat = myjson['radio_stats']
                    text['Radio Stats'] = json.dumps(radstat)
                    if len(radstat) >= 1: text['Radio Version'] = int(radstat[0])
                    if len(radstat) >= 2: text['Radio Reboot Count'] = int(radstat[1])
                    if len(radstat) >= 3: text['Radio I2C Bus Error Count'] = int(radstat[2])
                    if len(radstat) >= 4: text['Radio Status Text'] = get_hub_radio_stats_status_text(radstat[3])
                    if len(radstat) >= 4: text['Radio Status'] = int(radstat[3])
                    if len(radstat) >= 5: text['Radio Network ID'] = int(radstat[4])
                # text['fs'] = myjson['fs']  # Weatherflow Internal Use
                # text['mqtt_stats'] = myjson['mqtt_stats']  # Weatherflow Internal Use
                text['DateTime'] = epoch_text(myjson['timestamp'])
                text['type'] = myjson['type']
                if raw: text['raw'] = myjson
                wf_type = myjson['type']
            except ValueError as e:
                wf_json = {
                    "error": "Exception ValueError processing hub_status",
                    "value": str(e),
                    "line": except_line()
                }
            except TypeError as e:
                wf_json = {
                    "error": "Exception TypeError processing hub_status",
                    "value": str(e),
                    "line": except_line()
                }
            except:
                wf_json = {
                    "error": "Exception Error processing hub_status",
                    "value": None,
                    "line": except_line()
                }
    return wf_type, text




# #########################################################################
# ############    STATION MESSAGE HANDLING DETAIL ROUTINES     ############
# #########################################################################

def get_device_status_sensorbinary(sensor_status):
    sens_bin = "Unavailable"
    try:
        sens_bin = str(bin(int(sensor_status)).format(12))
    except:
        pass
    return sens_bin

def degrees2text(num):
    """ Convert Degrees 0-360 to Readable Text """
    val = int((num/22.5)+.5)
    arr = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    return arr[(val % 16)]

def get_batthealth(volts):
    """ Returns a Percentage 0-100 for battery charge, or 255 if unhealthy """
    # https://help.weatherflow.com/hc/en-us/articles/360048877194-Solar-Power-Rechargeable-Battery
    # 2.35 = 0%, 2.742 = 100%
    if 2.35 <= volts <= 2.9:
        health = (volts - 2.35) * 256
        if health > 100: health = 100
    elif volts > 2.1:
        health = 0
    else:
        health = 255  # Return an out of bounds for above safe voltage level, our too low
    return int(health)

def get_signal_station(myjson):
    """ Print Signal Level reported by the Station """
    if 'type' in myjson:
        if myjson['type'] == 'device_status':
            if 'rssi' in myjson:
                st_text = "Station=" + str(myjson['rssi']) + "(" + get_rssi_text(myjson['rssi']) + ")"
            if 'hub_rssi' in myjson:
                hub_text = "Hub=" + str(myjson['hub_rssi']) + "(" + get_rssi_text(myjson['hub_rssi']) + ")"
    return "RSSI " + st_text + ", " + hub_text

def get_device_status_sensortext(sensor_status):
    """ Get Text Information from Sensor Status int using Binary logic """
    sensor_int = int(sensor_status)
    sensor_text = str(sensor_status) + ", "
    if sensor_int == 0:
        sensor_text = "OK, "
    elif sensor_int == 4:  # "Lightning Disturber"
        sensor_text = "OK, "
        pass  # Don't fail a sensor because of lightning
    else:
        if sensor_int & 1:
            sensor_text += "Lightning failed, "
        if sensor_int & 2:
            sensor_text += "Lightning noise, "
        if sensor_int == 4:
            # sensor_text += "Lightning Disturber, "
            pass  # Don't fail a sensor because of lightning
        if sensor_int & 8:
            sensor_text += "Pressure Failed, "
        if sensor_int & 16:
            sensor_text += "Temperature Failed, "
        if sensor_int & 32:
            sensor_text += "Humidity Failed, "
        if sensor_int & 64:
            sensor_text += "Wind Failed, "
        if sensor_int & 128:
            sensor_text += "Precip failed, "
        if sensor_int & 256:
            sensor_text += "UV Failed, "
        if sensor_int & 512:
            sensor_text += "bit 10, "  # Considered 'Internal' Weatherflow
        if sensor_int & 1024:
            sensor_text += "bit 11, "  # Considered 'Internal' Weatherflow
        if sensor_int & 2048:
            sensor_text += "?Batt Mode 1, "  # Considered 'Internal' Weatherflow
        if sensor_int & 4096:
            sensor_text += "?Batt Mode 2, "  # Considered 'Internal' Weatherflow
        if sensor_int & 8192:
            sensor_text += "?Batt Mode 3, "  # Considered 'Internal' Weatherflow
        if sensor_int & 16384:
            sensor_text += "bit 15, "  # Considered 'Internal' Weatherflow
        if sensor_int & 32768:
            sensor_text += "Power Booster Depleted, " # 0x8000
        if sensor_int & 65536:
            sensor_text += "Power Booster Shore Power, " # 0x10000
    sensor_text = sensor_text[:-2]
    return sensor_text

def msg_rapid_wind(myjson, privacy = False, raw = False):
    """ Process JSON Packet from WeatherFlow Hub - rapid_wind """
    text = {}
    wf_type = False
    if 'type' in myjson:
        if myjson['type'] == 'rapid_wind':
            if 'ob' in myjson:
                try:
                    text = dict(zip(MAP_RAPID_WIND, myjson['ob']))
                    text['DateTime'] = epoch_text(myjson['ob'][0])
                    text['Station Serial'] = get_serial(myjson, privacy)
                    text['Hub Serial'] = get_hub_sn(myjson, privacy)
                    text['type'] = myjson['type']
                    if raw: text['raw'] = myjson
                    wf_type = myjson['type']
                except ValueError as e:
                    wf_json = {
                        "error": "Exception ValueError processing rapid_wind",
                        "value": str(e),
                        "line": except_line()
                    }
                except TypeError as e:
                    wf_json = {
                        "error": "Exception TypeError processing rapid_wind",
                        "value": str(e),
                        "line": except_line()
                    }
                except:
                    wf_json = {
                        "error": "Exception Error processing rapid_wind",
                        "value": None,
                        "line": except_line()
                    }
    return wf_type, text

def msg_evt_strike(myjson, privacy = False, raw = False):
    """ Process JSON Packet from WeatherFlow Hub - evt_strike """
    text = {}
    wf_type = False
    if 'type' in myjson:
        if myjson['type'] == 'evt_strike':
            if 'evt' in myjson:
                try:
                    text = dict(zip(MAP_EVT_STRIKE, myjson['evt']))
                    text['DateTime'] = epoch_text(myjson['evt'][0])
                    text['Station Serial'] = get_serial(myjson, privacy)
                    text['Hub Serial'] = get_hub_sn(myjson, privacy)
                    text['type'] = myjson['type']
                    if raw: text['raw'] = myjson
                    wf_type = myjson['type']
                except ValueError as e:
                    wf_json = {
                        "error": "Exception ValueError processing evt_strike",
                        "value": str(e),
                        "line": except_line()
                    }
                except TypeError as e:
                    wf_json = {
                        "error": "Exception TypeError processing evt_strike",
                        "value": str(e),
                        "line": except_line()
                    }
                except:
                    wf_json = {
                        "error": "Exception Error processing evt_strike",
                        "value": None,
                        "line": except_line()
                    }
    return wf_type, text

def msg_evt_precip(myjson, privacy = False, raw = False):
    """ Process JSON Packet from WeatherFlow Hub - evt_precip """
    text = {}
    wf_type = False
    if 'type' in myjson:
        if myjson['type'] == 'evt_precip':
            if 'evt' in myjson:
                try:
                    text['DateTime'] = epoch_text(myjson['evt'][0])
                    text['Station Serial'] = get_serial(myjson, privacy)
                    text['Hub Serial'] = get_hub_sn(myjson, privacy)
                    text['type'] = myjson['type']
                    if raw: text['raw'] = myjson
                    wf_type = myjson['type']
                except ValueError as e:
                    wf_json = {
                        "error": "Exception ValueError processing evt_precip",
                        "value": str(e),
                        "line": except_line()
                    }
                except TypeError as e:
                    wf_json = {
                        "error": "Exception TypeError processing evt_precip",
                        "value": str(e),
                        "line": except_line()
                    }
                except:
                    wf_json = {
                        "error": "Exception Error processing evt_precip",
                        "value": None,
                        "line": except_line()
                    }
    return wf_type, text

def msg_obs_st(myjson, privacy = False, raw = False):
    """ Process JSON Packet from WeatherFlow Hub - obs_st """
    text = {}
    wf_type = False
    if 'type' in myjson:
        if myjson['type'] == 'obs_st':
            if 'obs' in myjson:
                try:
                    obs_list = myjson['obs'][0]
                    text = dict(zip(MAP_OBS_ST, obs_list))
                    if 'firmware_revision' in myjson:
                        text['Station Firmware'] = int(myjson['firmware_revision'])
                    if 'hub_sn' in myjson:
                        text['Hub Serial'] = get_hub_sn(myjson, privacy)
                    if obs_list[4] is not None:
                        text['Wind Direction (text)'] = degrees2text(int(obs_list[4]))
                    if obs_list[16] is not None:
                        text['Battery Charge State (%)'] = get_batthealth(float(obs_list[16]))
                    if float(obs_list[7]) == float(-44.99):  # Check for Failed TEMP Sensor
                        text.update({'Air Temperature (C)': None})
                    text['Station Serial'] = str(get_serial(myjson, privacy))
                    text['DateTime'] = epoch_text(obs_list[0])
                    text['type'] = myjson['type']
                    if raw: text['raw'] = myjson
                    wf_type = myjson['type']
                except ValueError as e:
                    wf_json = {
                        "error": "Exception ValueError processing obs_st",
                        "value": str(e),
                        "line": except_line()
                    }
                except TypeError as e:
                    wf_json = {
                        "error": "Exception TypeError processing obs_st",
                        "value": str(e),
                        "line": except_line()
                    }
                except:
                    wf_json = {
                        "error": "Exception Error processing obs_st",
                        "value": None,
                        "line": except_line()
                    }
    return wf_type, text

def msg_device_status(myjson, privacy = False, raw = False):
    """ Process JSON Packet from WeatherFlow Hub - device_status """
    text = {}
    wf_type = False
    if 'type' in myjson:
        if myjson['type'] == 'device_status':
            try:
                text['Device Serial'] = get_serial(myjson, privacy)
                text['Hub Serial'] = get_hub_sn(myjson, privacy)
                text['Uptime (seconds)'] = myjson['uptime']
                text['Uptime (text)'] = get_uptime(myjson)
                text['Battery Voltage'] = float(myjson['voltage'])
                text['Battery Health (%)'] = get_batthealth(float(myjson['voltage']))
                text['Station Firmware'] = myjson['firmware_revision']
                text['Station RSSI (dBm)'] = myjson['rssi']
                text['Station RSSI Quality'] = get_rssi_text(myjson['rssi'])
                text['Hub RSSI (dBm)'] = myjson['hub_rssi']
                text['Hub RSSI Quality'] = get_rssi_text(myjson['hub_rssi'])
                text['Sensor Status'] = get_device_status_sensortext(myjson['sensor_status'])
                text['Sensor Binary'] = get_device_status_sensorbinary(myjson['sensor_status'])
                text['DateTime'] = epoch_text(myjson['timestamp'])
                text['type'] = myjson['type']
                if raw: text['raw'] = myjson
                wf_type = myjson['type']
            except ValueError as e:
                wf_json = {
                    "error": "Exception ValueError processing device_status",
                    "value": str(e),
                    "line": except_line()
                }
            except TypeError as e:
                wf_json = {
                    "error": "Exception TypeError processing device_status",
                    "value": str(e),
                    "line": except_line()
                }
            except:
                wf_json = {
                    "error": "Exception Error processing device_status",
                    "value": None,
                    "line": except_line()
                }
    return wf_type, text
