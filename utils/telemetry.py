import time
from utils import network, helpers


def get_cpu_temperature(**kwargs):
    """
    Get cpu temperature using vcgencmd
    """
    # temp = os.popen("vcgencmd measure_temp").readline()
    # return temp.replace('temp=', '')
    return '0C'


def get_cpu_percent(**kwargs):
    # return str(psutil.cpu_percent())
    return '0%'


def get_mem_percent(**kwargs):
    # return str(psutil.virtual_memory().percent)
    return '0%'


def get_signal_strength(**kwargs):
    """
    Get connection signal strength using iwconfig
    """
    # TODO: do this better
    # temp = os.popen("iwconfig").read()
    # return re.findall('(wlan[0-9]+).*?Signal level=(-[0-9]+) dBm', temp, re.DOTALL)
    return '0 dbm'


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


class TelemetryRecord:
    RPI_TEMP = 'RPI_TEMP'
    RPI_CPU = 'RPI_CPU'
    RPI_MEM = 'RPI_MEM'
    SIG_STR = 'SIG_STR'
    BATTERY = 'BATTERY'
    ROTATION = 'ROTATION'
    THROTTLE = 'THROTTLE'

    @classmethod
    def all(cls):
        return [
            cls.RPI_TEMP,
            cls.RPI_CPU,
            cls.RPI_MEM,
            cls.SIG_STR,
            cls.BATTERY,
            cls.ROTATION,
            cls.THROTTLE,
        ]

    @classmethod
    def read_value(cls, value: str, **kwargs):
        return {
            cls.RPI_TEMP: get_cpu_temperature,
            cls.RPI_CPU: get_cpu_percent,
            cls.RPI_MEM: get_mem_percent,
            cls.SIG_STR: get_signal_strength,
            cls.BATTERY: get_battery_percent,
            cls.ROTATION: get_rotation,
            cls.THROTTLE: get_throttle,
        }[value](**kwargs)


class Telemetry:
    """
    This class will aggregate all readings on pi side and
    then send them to client on a different or same socket every x seconds
    """

    def __init__(self, send_callback, **kwargs):
        self.send_callback = send_callback
        self.cycle_speed = 100
        self.options = kwargs

    def loop(self):
        # Get all readings then send them to client
        for record in TelemetryRecord.all():
            value = TelemetryRecord.read_value(record, **self.options)
            self.send_callback(network.NetworkEvent.TELEMETRY, helpers.encode_telemetry_record(record, value))

    def run(self):
        while True:
            self.loop()
            time.sleep(self.cycle_speed)
