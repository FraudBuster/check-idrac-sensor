#!/usr/bin/env python

import subprocess
import sys
import argparse
import re
import json
import time
import paramiko

def build_parser():
    parser = argparse.ArgumentParser(description='Check iDRAC Sensors')
    parser.add_argument('-H', '--host', required=True, type=str, dest='host')
    # racadm authentication - username/password or authfile. If authfile is
    # specified, it takes precedence
    parser.add_argument(
        '-u', '--username', required=True, type=str, dest='username')
    parser.add_argument(
        '-p', '--password', required=True, type=str, dest='password')
    parser.add_argument(
        '-a', '--authfile', required=False, type=str, dest='authfile')

    parser.add_argument(
        '-f', '--perfdata', required=False, type=bool, dest='perfdata', default=False)
    # Use 'all' to return data for all sensor types at once
    # Valid sensor types: battery, current, intrusion, memory, performance,
    # processor, redundancy, sd_card, voltage
    parser.add_argument(
        '-s', '--sensortype', required=False, type=str, dest='sensor', default='all')
    parser.add_argument(
        '-d', '--debug', required=False, type=bool, dest='debug', default=False)

    return parser


def main():
    global debug

    parser = build_parser()
    args = parser.parse_args()

    debug = args.debug
    valid_sensors = ['battery', 'current', 'intrusion', 'memory', 'power', 'temperature', 'fan',
                         'performance', 'processor', 'redundancy', 'system_performance', 'voltage', 'all']

    if args.sensor in valid_sensors:

        host = args.host
        user = args.username
        password = args.password.strip("'").replace('\\', '')

        perfdata = args.perfdata

        sensor = args.sensor
        start = time.time()
        
        sensor_data = ssh_connect(host, user, password, "racadm getsensorinfo")

        if sensor_data:
            formatted_out = lines_to_dict(sensor_data)
            sensors_text = nagios_output(formatted_out, sensor, perfdata)

            if debug:
                print json.dumps(formatted_out, sort_keys=True, indent=4)

            if sensors_text:
                return sensors_text

        else:
            print "No response from iDRAC!"
            sys.exit(3)
    else:
        print "ERROR: Invalid command or sensortype. Please check that command or sensortype is valid. Exiting...\n"
        sys.exit(3)

def format_sensor(sensor):
    return sensor.strip().lower().replace(' ', '_')

def set_sensor_info(lines):
    try:
        sensor = format_sensor(lines[0].split(':')[1])
        headings = clean_headings(lines[1].split('>'))
    except:
        sensor = format_sensor(lines[1].split(':')[1])
        headings = clean_headings(lines[2].split('>'))

    return sensor, headings

# Extract output lines and format a huge dict with all sensors informations
def lines_to_dict(lines):
    sensors = {}
    match = False
    g = ""
    for line in lines:
        m = re.match("Sensor\sType\s:\s([A-Z\s]+)", line)
        if m:
            match = True
            g = m.groups()[0].strip()
            sensors[g] = {}
        elif re.findall('^\<|^\[',line):
            # Jump if line starts with junk < or [
            continue
        else:
            sections = []
            sections = [x.strip() for x in line.split('  ') if x.strip()]
            if sections:
                s = sections.pop(0)
                sensors[g][s] = sections
    return sensors

#Ugly sensor output
def dump_sensors(sensors):
        for s,a in sensors.items():
            print "ITEM = %s" % s
            for b,c in a.items():
                print "\t * %s" % b
                for d in c:
                    print "\t\t - %s" %d

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

#Generate text output icinga/nagios formatted
def nagios_output(sensor_data, sensor, perfdata):
    '''Provide Nagios output for check results'''

    #Pointer function like map
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
        #dump_sensors(sensor_data)
        for item_name, sensor in sensor_data.items():
            output += "[%s] " % item_name
            try:
                output += funct_map[item_name.lower().replace(' ','_')](sensor)
            except Exception as e:
                print "%s" % e
                pass
    else:
        status = sensor_data[sensor]['status'].upper()

        # Nagios STDOUT format
        output = "%s - %s;" % (sensor, status)

        if perfdata:
            output += "| %s" % (status)

    return output

def validate_arguments(args):
    '''make sure command is valid'''

    validate = [args.cmd, args.sensor]


    validated = {}
    for option in validate:
        if option in valid_commands:
            validated[option] = True
        elif option in valid_sensortypes:
            validated[option] = True

    if any(a == False for a in validated.values()):
        return False
    else:
        return True

def clean_bracket_content(data):
    return re.sub("\[.*?\]", '', data)

def exec_command(command):
    """Execute command.
       Return a tuple: returncode, output and error message(None if no error).
    """
    sub_p = subprocess.Popen(command,
                             shell=True,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
    output, err_msg = sub_p.communicate()
    return (sub_p.returncode, output, err_msg)

def ssh_connect(host, user, password, command):
    ret_val = []
    try:
        drac_con = paramiko.SSHClient()
        drac_con.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        drac_con.connect(host, username=user, password=password)
        stdin, stdout, stderr = drac_con.exec_command(command)
        stdin.close()
        for line in stdout.readlines():
            ret_val.append(line)

        return ret_val
    except Exception as e:
        print "UNKNOWN: Unable to run ssh racadm by SSH:  %s" % e
        sys.exit(3)


if __name__ == "__main__":
    sensors_text = main()

    # Let's take care of Nagios / Icinga statutes
    # Just match Warning/Critical in output messages
    if re.findall('Critical', sensors_text):
        print "CRITICAL: %s" % sensors_text
        sys.exit(2)
    elif re.findall('Warning',sensors_text):
        print "WARNING: %s" % sensors_text
        print sys.exit(1)
    else:
        print "OK: %s" % sensors_text
    sys.exit(0)
