import threading
import time
import copy
from utils import mpu6050


class Mpu:
    """
    Mpu class to manage connection to sensor and have an up to date mpu6050 sensor running in a separate thread isolated
    from cycle speed for flight controller
    """
    ADDRESS = 0x68
    # [ROLL, PITCH, YAW]
    ZERO = [0.0, 0.0, 0.0]
    DELTA_TIME = 0.01
    CALIBRATION = 200

    def __init__(self):
        print('STARTING SENSOR')
        self.__gyro_offset = self.__zero()
        self.__accel_offset = self.__zero()
        self.__gyro = self.__zero()
        self.__accel = self.__zero()
        self.__step = 0
        self.__sensor = mpu6050.Mpu6050(self.ADDRESS)
        self.thread = threading.Thread(target=self.update, daemon=True, args=(6050,))
        self.thread.start()

    def update(self, *args, **kwargs):
        while True:
            time.sleep(self.DELTA_TIME)
            gd = self.__sensor.get_gyro_data()
            ad = self.__sensor.get_accel_data()

            gyro_data = [gd['x'], gd['y'], gd['z']]
            accel_data = [ad['x'], ad['y'], ad['z']]

            if self.__step < self.CALIBRATION:
                self.__add(self.__gyro_offset, gyro_data)
                self.__add(self.__accel_offset, accel_data)
                self.__step += 1
                if self.__step == self.CALIBRATION:
                    self.__div(self.__gyro_offset, self.CALIBRATION)
                    self.__div(self.__accel_offset, self.CALIBRATION)
                continue
            self.__sub(gyro_data, self.__gyro_offset)
            self.__sub(accel_data, self.__accel_offset)
            self.__mul(gyro_data, self.DELTA_TIME * 2)
            self.__mul(accel_data, self.DELTA_TIME * 2)
            self.__add(self.__gyro, gyro_data)
            self.__add(self.__accel, accel_data)

    def gyro(self):
        return self.__gyro

    def accel(self):
        return self.__accel

    @classmethod
    def __zero(cls):
        return copy.deepcopy(cls.ZERO)

    @staticmethod
    def __add(a, b):
        a[0] += b[0]
        a[1] += b[1]
        a[2] += b[2]

    @staticmethod
    def __sub(a, b):
        a[0] -= b[0]
        a[1] -= b[1]
        a[2] -= b[2]

    @staticmethod
    def __div(a, b):
        a[0] /= b
        a[1] /= b
        a[2] /= b

    @staticmethod
    def __mul(a, b):
        a[0] *= b
        a[1] *= b
        a[2] *= b
