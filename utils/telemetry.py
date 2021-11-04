import re
import os
import time
import psutil
from enum import Enum
from utils import network, helpers


def get_cpu_temperature(**kwargs):
    """
    Get cpu temperature using vcgencmd
    """
    temp = os.popen("vcgencmd measure_temp").readline()
    return temp.replace('temp=', '')


def get_cpu_percent(**kwargs):
    return str(psutil.cpu_percent())


def get_mem_percent(**kwargs):
    return str(psutil.virtual_memory().percent)


def get_signal_strength(**kwargs):
    """
    Get connection signal strength using iwconfig
    """
    temp = os.popen("iwconfig").read()

    return re.findall('(wlan[0-9]+).*?Signal level=(-[0-9]+) dBm', temp, re.DOTALL)


def get_battery_percent(**kwargs):
    # TODO: DO THIS SOMEHOW
    return str(0.0)


def get_rotation(controller=None, **kwargs):
    if not controller:
        return '0,0,0'
    return ','.join(['%.2f' % x for x in controller.sensor.angles])


def get_throttle(controller=None, **kwargs):
    if not controller:
        return 'None'
    return ','.join([str(f'{x.code}={x.throttle}') for x in controller.motors])


class TelemetryRecord(Enum):
    RPI_TEMP = 'RPI_TEMP'
    RPI_CPU = 'RPI_CPU'
    RPI_MEM = 'RPI_MEM'
    # Yes its Signal Strength im calling STR as a bad Dark souls reference
    SIG_STR = 'SIG_STR'
    BATTERY = 'BATTERY'
    ROTATION = 'ROTATION'
    THROTTLE = 'THROTTLE'

    @property
    def mapping(self):
        """
        Return mapping of telemetry records to callable functions
        """
        return {
            self.RPI_TEMP: get_cpu_temperature,
            self.RPI_CPU: get_cpu_percent,
            self.RPI_MEM: get_mem_percent,
            self.SIG_STR: get_signal_strength,
            self.BATTERY: get_battery_percent,
            self.ROTATION: get_rotation,
            self.THROTTLE: get_throttle,
        }

    def read_value(self, **kwargs):
        return self.mapping[self](**kwargs)


class Telemetry:
    """
    This class will aggregate all readings on pi side and
    then send them to client on a different or same socket every x seconds
    """

    def __init__(self, send_callback, **kwargs):
        self.send_callback = send_callback
        self.cycle_speed = 0.5
        self.options = kwargs

    def loop(self):
        # Get all readings then send them to client
        for record in TelemetryRecord:
            value = record.read_value(**self.options)
            self.send_callback(network.Event.TELEMETRY, helpers.encode_telemetry_record(record.value, value))

    def run(self):
        while True:
            self.loop()
            time.sleep(self.cycle_speed)
