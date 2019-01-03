# check-idrac-sensor

Nagios check script utilizing racadm by ssh to check getsensorinfo endpoint

## Purpose

This check script uses racadm by to check sensorinfo output from a Dell iDRAC

## Requirements

paramiko ssh library

## Installation

Clone the repo and move the check-idrac-sensor.py script to your Nagios plugin directory

## Usage

Below is the minimal usage. The default command (-C) is "getsensorinfo" and default sensors (-s) are "all".
Perfdata does not yet return anything and authfile feature is not yet implemented. 

```
./check-idrac-sensor.py -H 192.168.1.120 -u root -p calvin

usage: check-idrac-sensor.py [-h] -H HOST -u USERNAME -p PASSWORD
                             [-a AUTHFILE] [-f PERFDATA] [-s SENSOR]
                             [-d DEBUG]
```

## Bugs

- If you encounter a problem, please open an issue and I will do my best to help

## Known Issues / Compatibility

- Tested only on latest idrac version by ssh (8/9)
- Perfdata are options but not yet implemented

## TODO

- Perfdata for certain sensortypes
- Handle some of the failure cases better
- Implement single/multi sensor return (as opposed to just 'all')
