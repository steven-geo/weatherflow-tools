""" Log Weatherflow Packets to Console """
import json
import sys
import weatherflow
import signal

wf_conn = None
wait_time = 5

def main():
    """ Main Service Loop """
    global wf_conn
    # Loop to Receive Packets from WeatherFlow Hub
    while True:
        try:
            wf_conn =  weatherflow.Connect(privacy = False)
            while True:
                # Wait for and Get Broadcast Packets from the WeatherFlow Hub
                wf_type, wf_serial, wf_json = wf_conn.get_event()
                if wf_type:
                    if 'device' in wf_type: print(str(wf_type) + " from " + str(wf_serial) + "\n" + json.dumps(wf_json, sort_keys=True, indent=4))
                else:
                    print("### ERROR ###\n" + json.dumps(wf_json, sort_keys=True, indent=4))
        except ValueError as e:
            print("Failure Occured - Waiting " + str(wait_time) + " seconds then retrying.")
            print(e)
            time.sleep(wait_time)
        except KeyboardInterrupt as e:
            print("Stopping by Interrupt...")
            break

def handler(signum, frame):
    """ Handle Closing Gracefully """
    global wf_conn
    print("\nExiting...")
    wf_conn.close()  # Close Network Socket
    exit(0)

signal.signal(signal.SIGINT, handler)

main()
