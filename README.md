# check-idrac-sensor

Forked from https://github.com/lagooj/check-idrac-sensor

which itself was forked from https://github.com/hobbsh/check-idrac-sensor

Icinga / nagios check script utilizing racadm by ssh to check getsensorinfo endpoint

## Purpose

This check script uses racadm through ssh, to check sensorinfo output from a Dell iDRAC without any 
further dependencies except paramiko.

## Requirements

paramiko ssh library

## Installation

Clone the repo and move the check-idrac-sensor.py script to your Icinga / Nagios plugin directory

## Usage

Below is the minimal usage. The default sensors (-s) are "all".

```
check_idrac_sensor.py -H 192.168.1.120 -u root -p calvin

usage: check_idrac_sensor.py -H host [-P port] -u username -p password
                             [-s sensor] [-d debug]
```

## Bugs

- If you encounter a problem, please open an issue and I will do my best to help

## Known Issues / Compatibility

- This shoud work on iDRAC 7/8/9
- Python2/3 compatible
