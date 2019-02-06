import pytest
import check_idrac_sensor as cis
import re

@pytest.fixture()
def load_status():
    ret = []
    with open('tests/drac_fake_status','r') as dfs:
        ret = dfs.readlines()
    dfs.closed
    return ret
@pytest.fixture()
def run_lines_to_dict(load_status):
    val = cis.lines_to_dict(load_status)
    return val

def test_lines_to_dict(load_status):
    val = cis.lines_to_dict(load_status)
    assert len(val) == 12

def test_nagios_output(run_lines_to_dict):
    sensors = ['redundancy', 'temperature', 'power', 'battery', 'system_performance', 'current', 'fan', 'voltage', 'memory', 'performance', 'intrusion', 'processor']
    val = cis.nagios_output(run_lines_to_dict, 'all')
    assert len(val) == 2081
    assert re.findall('Warning', val)
    for sensor in sensors:
        val = cis.nagios_output(run_lines_to_dict, sensor)
        if sensor == 'memory':
            assert re.findall('Warning', val)
        else:
            assert val
