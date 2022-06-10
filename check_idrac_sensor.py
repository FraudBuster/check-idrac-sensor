#!/usr/bin/env python

import sys
import argparse
import re
import json
import paramiko


def build_parser():

    parser = argparse.ArgumentParser(description='Check iDRAC Sensors')
    parser.add_argument('-H', '--host', required=True, type=str, dest='host')
    parser.add_argument('-P', '--port', required=False, type=int, dest='port', default=22)
    parser.add_argument(
            '-u', '--username', required=True, type=str, dest='username')
    parser.add_argument(
            '-p', '--password', required=True, type=str, dest='password')
    parser.add_argument(
            '-s', '--sensortype', required=False, type=str, dest='sensor', default='all')
    parser.add_argument(
            '-d', '--debug', required=False, type=bool, dest='debug', default=False)

    return parser


def main():

    parser = build_parser()
    args = parser.parse_args()

    debug = args.debug
    valid_sensors = [
            'battery',
            'current',
            'intrusion',
            'memory',
            'power',
            'temperature',
            'fan',
            'performance',
            'processor',
            'redundancy',
            'system_performance',
            'voltage',
            'all'
            ]

    if args.sensor in valid_sensors:

        host = args.host
        port = args.port
        user = args.username
        password = args.password.strip("'").replace('\\', '')
        sensor = args.sensor

        sensor_data = ssh_connect(host, port, user, password, "racadm getsensorinfo")

        if sensor_data:
            formatted_out = lines_to_dict(sensor_data)
            sensors_text = nagios_output(formatted_out, sensor)

            if debug:
                print(json.dumps(formatted_out, sort_keys=True, indent=4))

            if sensors_text:
                return sensors_text

        else:
            print("No response from iDRAC!")
            sys.exit(3)
    else:
        print("ERROR: Invalid command or sensortype. Please check that command or sensortype is valid. Exiting...")
        sys.exit(3)


def ssh_connect(host, port, user, password, command):
    try:
        drac_con = paramiko.SSHClient()
        drac_con.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        drac_con.connect(host, port=port, username=user, password=password)
        stdin, stdout, stderr = drac_con.exec_command(command)
        stdin.close()

        return stdout.readlines()
    except Exception as e:
        print("UNKNOWN: Unable to run ssh racadm by SSH:  {}".format(e))
        sys.exit(3)


# Extract output lines and format a huge dict with all sensors informations
def lines_to_dict(lines):
    sensors = {}
    match = False
    g = ""
    for line in lines:
        m = re.match("Sensor\\sType\\s:\\s([A-Z\\s]+)", line)
        if m:
            match = True
            g = m.groups()[0].strip().replace(' ', '_')
            sensors[g] = {}
        elif re.findall('^\\<|^\\[', line):
            # Jump if line starts with junk as < or [
            continue
        else:
            sections = [x.strip() for x in line.split('  ') if x.strip()]
            if sections:
                s = sections.pop(0)
                sensors[g][s] = sections
    return sensors


# Ugly sensor output
def dump_sensors(sensors):
    for item_name, sensor_arr in sensors.items():
        print("ITEM = {}".format(item_name))
        for sensor_name,  sensor_values in sensor_arr.items():
            print("\t * {}".format(sensor_name))
            for value in sensor_values:
                print("\t\t - {}".format(value))


# Each sensors should have a matching function to format the results
def redundancy(status):
    redundancy_out = ''
    for n, a in sorted(status.items()):
        if "Full Redundant" in a:
            redundancy_out += '- %s : is Ok ' % n
    return redundancy_out


def power(status):
    power_out = ''
    for n, a in sorted(status.items()):
        if "Present" == a[0]:
            power_out += "- %s : is Ok " % n
    return power_out


def memory(status):
    memory_out = ''
    for n, a in sorted(status.items()):
        if "Presence_Detected" == a[1]:
            memory_out += "- %s is %s " % (n, a[0])
    return memory_out


def intrusion(status):
    intrusion_out = ''
    for n, a in sorted(status.items()):
        if "Closed" == a[0]:
            intrusion_out += "- %s is Ok " % (n)
    return intrusion_out


# Generic status retriever no further formating is required
def sensor_generic(status):
    sensor_generic = ''
    for n, a in sorted(status.items()):
        sensor_generic += "- %s=%s is %s " % (n, a[1], a[0])
    return sensor_generic


# Generate text output icinga/nagios formatted
def nagios_output(sensor_data, sensor):
    '''Provide Nagios output for check results'''

    # Function pointer look-alike map
    funct_map = {
            'redundancy': redundancy,
            'temperature': sensor_generic,
            'power': power,
            'battery': sensor_generic,
            'system_performance': sensor_generic,
            'current': sensor_generic,
            'fan': sensor_generic,
            'voltage': sensor_generic,
            'memory': memory,
            'performance': sensor_generic,
            'intrusion': intrusion,
            'processor': sensor_generic

            }

    output = ''

    if sensor == 'all':
        for item_name, sensors in sensor_data.items():
            output += "[%s] " % item_name
            output += funct_map[item_name.lower()](sensors)
    else:
        output += "[%s] " % sensor.upper()
        output = funct_map[sensor](sensor_data[sensor.upper()])

    return output


if __name__ == "__main__":
    sensors_text = main()

    # Let's take care of Nagios / Icinga statutes
    # Just match Warning/Critical in output messages
    if re.findall('Critical', sensors_text):
        print("CRITICAL: {}".format(sensors_text))
        sys.exit(2)
    elif re.findall('Warning', sensors_text):
        print("WARNING: {}".format(sensors_text))
        sys.exit(1)
    else:
        print("OK: {}".format(sensors_text))
    sys.exit(0)
