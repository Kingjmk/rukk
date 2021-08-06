import threading
import time
import math
import copy
from utils import mpu6050, filters


class Mpu:
    """
    Mpu class to manage connection to sensor and have an up to date mpu6050 sensor running in a separate thread isolated
    from cycle speed for flight controller
    """
    ADDRESS = 0x68
    # [ROLL, PITCH, YAW]
    ZERO = [0.0, 0.0, 0.0]
    DELTA_TIME = 0.004

    def __init__(self, flip=False, invert=False):
        """
        :param flip: Flip X, Y axis
        :param invert: Invert Both X and Y
        """
        self.flip = flip
        self.invert = invert
        self._angles = self.__zero()

        self.__gyro = self.__zero()
        self.__accel = self.__zero()
        self.__sensor = mpu6050.Mpu6050(self.ADDRESS)
        self.__gyro_calibration = self.__zero()
        self.__accel_calibration = self.__zero()
        # Last read in nano seconds
        self.last_read = 0
        self.__kalman_x = filters.KalmanAngle()
        self.__kalman_y = filters.KalmanAngle()
        self.thread = threading.Thread(target=self.update, daemon=True, args=(6050,))
        self.thread.start()

    @property
    def angles(self):
        angles = self._angles

        if self.flip:
            angles = [angles[1], angles[0], angles[2]]

        if self.invert:
            self.__mul(angles, -1)

        return angles

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

    def acc_angle(self, ax, ay, az):
        rad_to_deg = 180 / 3.14159
        ax_angle = math.atan(ay / math.sqrt(math.pow(ax, 2) + math.pow(az, 2))) * rad_to_deg
        ay_angle = math.atan((-1 * ax) / math.sqrt(math.pow(ay, 2) + math.pow(az, 2))) * rad_to_deg
        return ax_angle, ay_angle

    def gyr_angle(self, gx, gy, gz, dt):
        gx_angle = gx * dt + self._angles[0]
        gy_angle = gy * dt + self._angles[1]
        gz_angle = gz * dt + self._angles[2]
        return gx_angle, gy_angle, gz_angle

    def c_filtered_angle(self, ax_angle, ay_angle, gx_angle, gy_angle):
        alpha = 0.90
        c_angle_x = alpha * gx_angle + (1.0 - alpha) * ax_angle
        c_angle_y = alpha * gy_angle + (1.0 - alpha) * ay_angle
        return c_angle_x, c_angle_y

    # Kalman filter to determine the change in angle by combining accelerometer and gyro values.
    def k_filtered_angle(self, ax_angle, ay_angle, gx, gy, dt):
        k_angle_x = self.__kalman_x.get_angle(ax_angle, gx, dt)
        k_angle_y = self.__kalman_y.get_angle(ay_angle, gy, dt)
        return k_angle_x, k_angle_y

    def update(self, *args, **kwargs):
        self.calibrate()

        while True:
            now = time.time_ns()
            # Get time difference in seconds
            dt = (now - self.last_read) / (10**9 * 1.0)
            gyro_data = self.raw_gyro()
            accel_data = self.raw_accel()

            ax = accel_data[0]
            ay = accel_data[1]
            az = accel_data[2]

            # This is angular velocity in each of the 3 directions
            gx = (gyro_data[0] - self.__gyro_calibration[0])
            gy = (gyro_data[1] - self.__gyro_calibration[0])
            gz = (gyro_data[2] - self.__gyro_calibration[0])

            # Calculate angle of inclination or tilt for the x and y axes with acquired acceleration vectors
            acc_angles = self.acc_angle(ax, ay, az)
            # Calculate angle of inclination or tilt for x,y and z axes with angular rates and dt
            gyr_angles = self.gyr_angle(gx, gy, gz, dt)
            # filtered tilt angle i.e. what we're after
            c_angle_x, c_angle_y = self.c_filtered_angle(acc_angles[0], acc_angles[1], gyr_angles[0], gyr_angles[1])
            k_angle_x, k_angle_y = self.k_filtered_angle(acc_angles[0], acc_angles[1], gx, gy, dt)

            self._angles = [c_angle_x, c_angle_y, 0]
            self.last_read = now
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
