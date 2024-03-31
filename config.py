CAMERA_ENABLED = False

DEFAULT_HOST = 'pico1'
DEFAULT_PORT = 7777
DEFAULT_WIFI_SSID = ''
DEFAULT_WIFI_PASSWORD = ''


class Mpu:
    enable = True
    id = 1
    SDA = 2
    SCL = 3


class ConfigMotor:
    enable = False
    pin = 0
    calibration = 0

    def __init__(self, pin: int = 0, calibration: float = 0.0):
        self.pin = pin
        self.calibration = calibration


class Motors:
    FRONT_LEFT = ConfigMotor(10, 0)
    FRONT_RIGHT = ConfigMotor(11, 0)
    BACK_RIGHT = ConfigMotor(12, 0)
    BACK_LEFT = ConfigMotor(13, 0)
