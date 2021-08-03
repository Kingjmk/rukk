import threading
import time
import math
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
    DELTA_TIME = 0.004

    def __init__(self):
        self.__gyro = self.__zero()
        self.__accel = self.__zero()
        self.__sensor = mpu6050.Mpu6050(self.ADDRESS)
        self.__gyro_calibration = self.__zero()
        self.__accel_calibration = self.__zero()
        self.angles = self.__zero()
        self.thread = threading.Thread(target=self.update, daemon=True, args=(6050,))
        self.thread.start()

    def raw_gyro(self):
        _g = self.__sensor.get_gyro_data()
        return [_g['x'], _g['y'], _g['z']]

    def raw_accel(self):
        _a = self.__sensor.get_accel_data()
        return [_a['x'], _a['y'], _a['z']]

    def calibrate(self):
        # Run this code 2000 times
        for i in range(0, 2000):
            gyro_data = self.raw_gyro()

            # add gyro offset vector to calibration vector
            self.__add(self.__gyro_calibration, gyro_data)
            time.sleep(0.003)  # Delay 3us to simulate the 250Hz program loop

        self.__div(self.__gyro_calibration, 2000)

    def update(self, *args, **kwargs):
        self.calibrate()

        init_angle = True

        while True:
            gyro_data = self.raw_gyro()
            accel_data = self.raw_accel()

            # Subtract the offset calibration value from the raw gyro value
            self.__sub(gyro_data, self.__gyro_calibration)

            # Gyro angle calculations
            # 0.0000611 = 1 / (250Hz / 65.5)

            self.__add(self.__gyro, [
                gyro_data[0] * 0.0000611,
                gyro_data[1] * 0.0000611,
                0,
            ])

            # 0.000001066 = 0.0000611 * (3.142(PI) / 180deg) The sin function is in radians
            # If the IMU has yawed transfer the roll angle to the pitch angel
            # and if the IMU has yawed transfer the pitch angle to the roll angel
            self.__add(self.__gyro, [
                self.__gyro[1] * math.sin(gyro_data[2] * 0.000001066 * -1),
                self.__gyro[0] * math.sin(gyro_data[2] * 0.000001066),
                0,
            ])

            # Accelerometer angle calculations
            # Calculate the total accelerometer vector
            acc_total_vector = math.sqrt((accel_data[0] ** 2) + (accel_data[1] ** 2) + (accel_data[2] ** 2))
            # 57.296 = 1 / (3.142 / 180) The asin function is in radians
            angle_roll_acc = math.asin((accel_data[0] * 1.0) / acc_total_vector) * -57.296
            angle_pitch_acc = math.asin((accel_data[1] * 1.0) / acc_total_vector) * 57.296
            self.__accel = [angle_roll_acc, angle_pitch_acc, 0]

            # Accelerometer calibration
            self.__sub(self.__accel, self.__accel_calibration)

            # Initialize Gyro Angle
            if init_angle:
                self.__gyro[0] = angle_roll_acc
                self.__gyro[1] = angle_pitch_acc
                init_angle = False
            else:
                self.__gyro[0] *= 0.9996 + angle_roll_acc * 0.0004
                self.__gyro[1] *= 0.9996 + angle_pitch_acc * 0.0004

            # To dampen the pitch and roll angles a complementary filter is used
            # Take 90% of the output roll value and add 10% of the raw roll value

            self.angles[0] = self.angles[0] * 0.9 + self.__gyro[0] * 0.1
            self.angles[1] = self.angles[1] * 0.9 + self.__gyro[1] * 0.1

            time.sleep(self.DELTA_TIME)

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
