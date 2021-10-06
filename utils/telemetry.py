import re
import os
import time
import psutil
from enum import Enum
from utils import network, helpers


def get_cpu_temperature():
    """
    Get cpu temperature using vcgencmd
    """
    temp = os.popen("vcgencmd measure_temp").readline()
    return temp.replace('temp=', '')


def get_signal_strength():
    """
    Get connection signal strength using iwconfig
    """
    temp = os.popen("iwconfig").read()

    return re.findall('(wlan[0-9]+).*?Signal level=(-[0-9]+) dBm', temp, re.DOTALL)


def get_battery_percent():
    # TODO: DO THIS SOMEHOW
    return str(0.0)


class TelemetryRecord(Enum):
    RPI_TEMP = 'RPI_TEMP'
    RPI_CPU = 'RPI_CPU'
    RPI_MEM = 'RPI_MEM'
    # Yes its Signal Strength im calling STR as a bad Dark souls reference
    SIG_STR = 'SIG_STR'
    BATTERY = 'BATTERY'

    @property
    def mapping(self):
        """
        Return mapping of telemetry records to callable functions
        """
        return {
            self.RPI_TEMP: get_cpu_temperature,
            self.RPI_CPU: lambda: str(psutil.cpu_percent()),
            self.RPI_MEM: lambda: str(psutil.virtual_memory().percent),
            self.SIG_STR: lambda: get_signal_strength,
            self.BATTERY: lambda: get_battery_percent,
        }

    def read_value(self):
        return self.mapping[self]()


class Telemetry:
    """
    This class will aggregate all readings on pi side and
    then send them to client on a different or same socket every x seconds
    """

    def __init__(self, send_callback):
        self.send_callback = send_callback
        self.cycle_speed = 0.5

    def loop(self):
        # Get all readings then send them to client
        for record in TelemetryRecord:
            value = record.read_value()
            self.send_callback(network.Event.TELEMETRY, helpers.encode_telemetry_record(record.value, value))

    def run(self):
        while True:
            self.loop()
            time.sleep(self.cycle_speed)
