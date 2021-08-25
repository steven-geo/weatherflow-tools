""" Process WeatherFlow Packets and notify on Major events like Low Batt, Offline, Online, Sensor Failure """
import json
import sys
import logging
import weatherflow
import signal
import time
try:
    import slackmsg
    slackenabled = True
except ImportError:
    slackenabled = False
try:
    import treepoem  # Also Requires GhostScript
    barcodeenabled = True
except ImportError:
    barcodeenabled = False

FILE_STATUS = '/opt/weatherflow-tools/status.json'
FILE_CONFIG = '/opt/weatherflow-tools/config.json'
SAVE_STATUS_INTERVALSEC=600

wf_conn =  None
wf_notify = None
wf_config = None

def main():
    """ Main Service Loop """
    global wf_conn
    global wf_notify
    global wf_config
    # Setup Logging to Console
    logging.basicConfig(format='%(filename)s %(levelname)s: %(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', stream=sys.stdout, level=logging.DEBUG)
    logging.info("Running...")
    # Loop to Receive Packets from WeatherFlow Hub
    wf_conn =  weatherflow.Connect(privacy = False)
    wf_notify = weatherflow.Notifications()
    wf_config = wf_notify.readconfig(FILE_CONFIG)
    if 'slackhookurl' in wf_config:
        logging.info("Messaging: Slack is Enabled")
    save_status_time = int(time.time()) + SAVE_STATUS_INTERVALSEC
    while True:
        try:
            print("Loaded " + str(wf_notify.open(FILE_STATUS)) + " devices from saved status information")
            if not __debug__: send_msg("WeatherFlow","WeatherFlow Monitor Starting","ok")
            while True:
                # Wait for and Get Broadcast Packets from the WeatherFlow Hub
                wf_type, wf_serial, wf_json = wf_conn.get_event()
                if wf_type:
                    if __debug__: logging.debug("Received: " + str(wf_type) + " from " + str(wf_serial))
                else:
                    if __debug__: logging.debug("\n##### ERROR #####\n" + json.dumps(wf_json, sort_keys=True, indent=4))
                # Get Notifications for status changes from device status messages
                st_type, st_device, st_event, st_json = wf_notify.get_status(wf_json)
                if st_type:
                    if __debug__: logging.debug("\n####### STATUS EVENT #######\nType: " + str(st_type) + "\nEvent: " + str(st_event) + "\nDevice: " + str(st_device) + "\nPayload: " + json.dumps(st_json, sort_keys=True, indent=4))
                    msgtitle, msgtext, msgstatus = weatherflow.notification(st_type, st_device, st_event, st_json)
                    send_msg(msgtitle, msgtext, msgstatus)
                # Check all devices to see if any have gone offline
                st_type, st_device, st_event, st_json = wf_notify.offline()
                if st_type:
                    if __debug__: logging.debug("\n####### OFFLINE EVENT #######\nType: " + str(st_type) + "\nEvent: " + str(st_event) + "\nDevice: " + str(st_device) + "\nPayload: " + json.dumps(st_json, sort_keys=True, indent=4))
                    msgtitle, msgtext, msgstatus = weatherflow.notification(st_type, st_device, st_event, st_json)
                    send_msg(msgtitle, msgtext, msgstatus)
                if int(time.time()) > save_status_time:
                    wf_notify.save_status()
                    save_status_time = int(time.time()) + SAVE_STATUS_INTERVALSEC
                    logging.info("Saving Status Information File")

        except ValueError as e:
            wait_time = 5 if __debug__ else 60
            logging.error("Failure Occured - Waiting " + str(wait_time) + " seconds then retrying.")
            logging.error(e)
            time.sleep(wait_time)
        except KeyboardInterrupt as e:
            logging.info("Stopping by Interrupt...")
            break

def send_msg(msgtitle, msgtext, msgstatus):
    global wf_config
    msgsent = False
    if slackenabled and 'slackhookurl' in wf_config:
        msg_slack(msgtitle, msgtext, msgstatus)
        msgsent = True
    # Insert other message options, email, etc.. here.
    if not msgsent:
        # Write to syslog if no other outputs are enabled
        msg_log(msgtitle, msgtext, msgstatus)
    return False

def msg_log(msgtitle, msgtext, msgstatus):
        # TODO - Remove line breaks from msgtext
        logging.info(str(msgstatus) + ": " + str(msgtitle) + ":" + str(msgtext))

def msg_slack(msgtitle, msgtext, msgstatus):
    slack_hook_url = wf_config['slackhookurl']
    slack = slackmsg.Connect(slack_hook_url, '#technical', 'WeatherFlow', ':mostly_sunny:')
    response = slack.send(msgtitle, msgtext, msgstatus)
    if response:
        logging.error("Error Sending Message: " + str(response))
        # Log to Syslog if slack fails
        msg_log(msgtitle, msgtext, msgstatus)
    return response


def handler(signum, frame):
    global wf_conn
    global wf_notify
    print("\nTermination Handler")
    wf_conn.close()  # Close Network Socket
    wf_notify.close()  # Save Status Information
    if not __debug__: send_msg("WeatherFlow","WeatherFlow Monitor Stopping","warning")
    exit(0)

signal.signal(signal.SIGINT, handler)

main()
