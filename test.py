import pytest
import check_idrac_sensor as cis
import re

@pytest.fixture()
def open_fixture():
    ret = []
    with open('drac_fake_status','r') as dfs:
        ret = dfs.readlines()
    dfs.closed
    return ret
@pytest.fixture()
def test_line_to_dict(open_fixture):
    val = cis.lines_to_dict(open_fixture)
    return val

def test_lines_to_dict(open_fixture):
    val = cis.lines_to_dict(open_fixture)
    assert len(val) == 12
    return val

def test_nagios_output(test_line_to_dict):
    sensors = ['redundancy', 'temperature', 'power', 'battery', 'system_performance', 'current', 'fan', 'voltage', 'memory', 'performance', 'intrusion', 'processor']
    val = cis.nagios_output(test_line_to_dict, 'all')
    assert len(val) == 2081
    assert re.findall('Warning', val)
    for sensor in sensors:
        val = cis.nagios_output(test_line_to_dict, sensor)
        if sensor == 'memory':
            assert re.findall('Warning', val)
        else:
            assert val
