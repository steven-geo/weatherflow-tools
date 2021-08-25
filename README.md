# WeatherFlow Tools

Weather Flow tools is under development

The aim of these tools is to provide foundation libraries and tools to monitor your WeatherFlow Tempest Weather Station

These tools are written in Python 3.7

REFERENCES

https://weatherflow.com/tempest-weather-system/

https://community.weatherflow.com/


## Contents

**[Installation](#installation)**
**[Using wftools-test.py](#Using wftools-test.py)**
**[Using WFTempest Module](#Using WFTempest Module)**



## Library Installation

Install using pip

```bash
pip install -e git+https://github.com/steven-geo/weatherflow-tools#egg=weatherflow
```

## Using WeatherFlow Module

See Samples

*weatherflowmon.py* - Designed to notify you on status changes, and includes a service that can be installed. Currently only Slack is setup as an integration.

*weatherflowlive.py* - Simply outputs all weatherflow information to the console.

*wf-livedevice.py* - Same as above, but filters just to device messages.


### About

The WeatherFlow Tools Library provides method to integrate with the tempest packets in a more user friendly method. It provides decoding of fields based on the WeatherFlow UDP specification v170 (https://weatherflow.github.io/Tempest/api/udp/v170/)

It also provides additional fields
* Human Readable Date/Time from timestamp
* Wind Direction in Cardinal Directions based on degrees
* Estimated Battery Charge percentage from voltage
* Uptime in Days, Hours, Minutes from uptime
* RSSI Quality Text (Excellent, Good) from RSSI dBm reading

It also offers a privacy option to mask Serial Numbers of the Hub and Stations when outputting information if required



### TODO

More Documentation

Confirm Undocumented Sensor Status Messages for Battery Modes - remove voltage level table requirements
