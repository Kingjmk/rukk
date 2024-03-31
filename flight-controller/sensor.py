import math
import ustruct
import utime
from machine import I2C
from micropython import const
import config


_WIA = const(0x00)
_HXL = const(0x03)
_HXH = const(0x04)
_HYL = const(0x05)
_HYH = const(0x06)
_HZL = const(0x07)
_HZH = const(0x08)
_ST2 = const(0x09)
_CNTL1 = const(0x0a)
_ASAX = const(0x10)
_ASAY = const(0x11)
_ASAZ = const(0x12)

_INT_PIN_CFG = const(0x37)
_I2C_BYPASS_MASK = const(0b00000010)
_I2C_BYPASS_EN = const(0b00000010)
_I2C_BYPASS_DIS = const(0b00000000)

_MODE_POWER_DOWN = 0b00000000
MODE_SINGLE_MEASURE = 0b00000001
MODE_CONTINOUS_MEASURE_1 = 0b00000010  # 8Hz
MODE_CONTINOUS_MEASURE_2 = 0b00000110  # 100Hz
MODE_EXTERNAL_TRIGGER_MEASURE = 0b00000100
_MODE_SELF_TEST = 0b00001000
_MODE_FUSE_ROM_ACCESS = 0b00001111

OUTPUT_14_BIT = 0b00000000
OUTPUT_16_BIT = 0b00010000

_SO_14BIT = 0.6
_SO_16BIT = 0.15


class KalmanAngle:
    def __init__(self):
        # Q (ANGLE) unknown uncertainty from the environment
        self.QAngle = 0.001
        # Q (BIAS) unknown uncertainty from the environment. Here - covariance is degree of correlation
        # between variances of the angle and its error/bias.
        self.QBias = 0.003
        self.RMeasure = 0.1
        self.angle = 0.0
        self.bias = 0.0
        self.rate = 0.0
        self.P = [[0.0, 0.0], [0.0, 0.0]]

    def get_angle(self, new_angle, new_rate, dt):
        # step 1: Predict new state (for our case - state is angle) from old state + known external influence
        self.rate = new_rate - self.bias  # new_rate is the latest Gyro measurement
        self.angle += dt * self.rate

        # step 2: Predict new uncertainty (or covariance) from old uncertainity and unknown uncertainty from the environment.
        self.P[0][0] += dt * (dt * self.P[1][1] - self.P[0][1] - self.P[1][0] + self.QAngle)
        self.P[0][1] -= dt * self.P[1][1]
        self.P[1][0] -= dt * self.P[1][1]
        self.P[1][1] += self.QBias * dt

        # step 3: Innovation i.e. predict th next measurement
        y = new_angle - self.angle

        # step 4: Innovation covariance i.e. error in prediction
        s = self.P[0][0] + self.RMeasure

        # step 5:  Calculate Kalman Gain
        k = [0.0, 0.0]
        k[0] = self.P[0][0] / s
        k[1] = self.P[1][0] / s

        # step 6: Update the Angle
        self.angle += k[0] * y
        self.bias += k[1] * y

        # step 7: Calculate estimation error covariance - Update the error covariance
        p00_temp = self.P[0][0]
        p01_temp = self.P[0][1]

        self.P[0][0] -= k[0] * p00_temp
        self.P[0][1] -= k[0] * p01_temp
        self.P[1][0] -= k[1] * p00_temp
        self.P[1][1] -= k[1] * p01_temp
        return self.angle


class Ak8963:
    """Class which provides interface to AK8963 magnetometer."""
    def __init__(
        self, i2c, address: int = 0x0C,
        mode=MODE_CONTINOUS_MEASURE_1, output=OUTPUT_16_BIT,
        offset=(0, 0, 0), scale=(1, 1, 1)
    ):
        self.i2c = i2c
        self.address = address
        self._offset = offset
        self._scale = scale

        char = i2c.readfrom_mem(0x68, _INT_PIN_CFG, 1)[0]
        char &= ~_I2C_BYPASS_MASK  # clear I2C bits
        char |= _I2C_BYPASS_EN
        i2c.writeto_mem(0x68, _INT_PIN_CFG, bytes([char]))

        if 0x48 != self.whoami:
            raise RuntimeError("AK8963 not found in I2C bus.")

        # Sensitivity adjustement values
        self._read_or_write_char(_CNTL1, _MODE_FUSE_ROM_ACCESS)
        asax = self._read_or_write_char(_ASAX)
        asay = self._read_or_write_char(_ASAY)
        asaz = self._read_or_write_char(_ASAZ)
        self._read_or_write_char(_CNTL1, _MODE_POWER_DOWN)

        # Should wait atleast 100us before next mode
        self._adjustement = (
            (0.5 * (asax - 128)) / 128 + 1,
            (0.5 * (asay - 128)) / 128 + 1,
            (0.5 * (asaz - 128)) / 128 + 1
        )

        # Power on
        self._read_or_write_char(_CNTL1, (mode | output))

        if output is OUTPUT_16_BIT:
            self._so = _SO_16BIT
        else:
            self._so = _SO_14BIT

    def magnetic(self):
        """
        X, Y, Z axis micro-Tesla (uT) as floats.
        """
        xyz = list(self._read_three_shorts(_HXL))
        self._read_or_write_char(_ST2)  # Enable updating readings again

        # Apply factory axial sensitivy adjustements
        xyz[0] *= self._adjustement[0]
        xyz[1] *= self._adjustement[1]
        xyz[2] *= self._adjustement[2]

        # Apply output scale determined in constructor
        so = self._so
        xyz[0] *= so
        xyz[1] *= so
        xyz[2] *= so

        # Apply hard iron ie. offset bias from calibration
        xyz[0] -= self._offset[0]
        xyz[1] -= self._offset[1]
        xyz[2] -= self._offset[2]

        # Apply soft iron ie. scale bias from calibration
        xyz[0] *= self._scale[0]
        xyz[1] *= self._scale[1]
        xyz[2] *= self._scale[2]

        return tuple(xyz)

    def adjustement(self):
        return self._adjustement

    @property
    def whoami(self):
        """ Value of the whoami register. """
        return self._read_or_write_char(_WIA)

    def calibrate(self, count=256, delay=200):
        self._offset = (0, 0, 0)
        self._scale = (1, 1, 1)

        reading = self.magnetic
        minx = maxx = reading[0]
        miny = maxy = reading[1]
        minz = maxz = reading[2]

        while count:
            utime.sleep_ms(delay)
            reading = self.magnetic
            minx = min(minx, reading[0])
            maxx = max(maxx, reading[0])
            miny = min(miny, reading[1])
            maxy = max(maxy, reading[1])
            minz = min(minz, reading[2])
            maxz = max(maxz, reading[2])
            count -= 1
            print(count)

        # Hard iron correction
        offset_x = (maxx + minx) / 2
        offset_y = (maxy + miny) / 2
        offset_z = (maxz + minz) / 2

        self._offset = (offset_x, offset_y, offset_z)

        # Soft iron correction
        avg_delta_x = (maxx - minx) / 2
        avg_delta_y = (maxy - miny) / 2
        avg_delta_z = (maxz - minz) / 2

        avg_delta = (avg_delta_x + avg_delta_y + avg_delta_z) / 3

        scale_x = avg_delta / avg_delta_x
        scale_y = avg_delta / avg_delta_y
        scale_z = avg_delta / avg_delta_z

        self._scale = (scale_x, scale_y, scale_z)

        return self._offset, self._scale

    def _read_three_shorts(self, register):
        buf = self.i2c.readfrom_mem(self.address, register, 6)
        return ustruct.unpack("<hhh", buf)

    def _read_or_write_char(self, register, value=None, address=None):
        if value is None:
            buf = self.i2c.readfrom_mem(address if address else self.address, register, 1)
            return buf[0]

        return self.i2c.writeto_mem(address if address else self.address, register, bytes([value]))

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        pass


class Mpu6500:
    """Class for reading gyro rates and acceleration data from an MPU-6050 module via I2C."""

    def __init__(self, i2c: I2C, address: int = 0x68):
        """
        Creates a new MPU6050 class for reading gyro rates and acceleration data.
        :param i2c: A setup I2C module of the machine module.
        :param address: The I2C address of the MPU-6050 you are using (0x68 is the default).
        """
        self.address = address
        self.i2c = i2c
        # Wake
        self.i2c.writeto_mem(0x68, 0x6B, bytes([0x01]))

    def sleep(self) -> None:
        """Places MPU-6050 in sleep mode (low power consumption). Stops the internal reading of new data. Any calls to get gyro or accel data while in sleep mode will remain unchanged - the data is not being updated internally within the MPU-6050!"""
        self.i2c.writeto_mem(self.address, 0x6B, bytes([0x40]))

    def who_am_i(self) -> int:
        """Returns the address of the MPU-6050 (ensure it is working)."""
        return self.i2c.readfrom_mem(self.address, 0x75, 1)[0]

    def read_temperature(self) -> float:
        """Reads the temperature, in celsius, of the onboard temperature sensor of the MPU-6050."""
        data = self.i2c.readfrom_mem(self.address, 0x41, 2)
        raw_temp: float = self._translate_pair(data[0], data[1])
        temp: float = (raw_temp / 340.0) + 36.53
        return temp

    def read_gyro_range(self) -> int:
        """Reads the gyroscope range setting."""
        return self._hex_to_index(self.i2c.readfrom_mem(self.address, 0x1B, 1)[0])

    def write_gyro_range(self, range: int) -> None:
        """Sets the gyroscope range setting."""
        self.i2c.writeto_mem(self.address, 0x1B, bytes([self._index_to_hex(range)]))

    def read_gyro_data(self) -> tuple[float, float, float]:
        """Read the gyroscope data, in a (x, y, z) tuple."""

        # set the modified based on the gyro range (need to divide to calculate)
        gr: int = self.read_gyro_range()
        modifier: float = None
        if gr == 0:
            modifier = 131.0
        elif gr == 1:
            modifier = 65.5
        elif gr == 2:
            modifier = 32.8
        elif gr == 3:
            modifier = 16.4

        # read data
        data = self.i2c.readfrom_mem(self.address, 0x43, 6)  # read 6 bytes (gyro data)
        x: float = (self._translate_pair(data[0], data[1])) / modifier
        y: float = (self._translate_pair(data[2], data[3])) / modifier
        z: float = (self._translate_pair(data[4], data[5])) / modifier

        return (x, y, z)

    def read_accel_range(self) -> int:
        """Reads the accelerometer range setting."""
        return self._hex_to_index(self.i2c.readfrom_mem(self.address, 0x1C, 1)[0])

    def write_accel_range(self, range: int) -> None:
        """Sets the gyro accelerometer setting."""
        self.i2c.writeto_mem(self.address, 0x1C, bytes([self._index_to_hex(range)]))

    def read_accel_data(self) -> tuple[float, float, float]:
        """Read the accelerometer data, in a (x, y, z) tuple."""

        # set the modified based on the gyro range (need to divide to calculate)
        ar: int = self.read_accel_range()
        modifier: float = None
        if ar == 0:
            modifier = 16384.0
        elif ar == 1:
            modifier = 8192.0
        elif ar == 2:
            modifier = 4096.0
        elif ar == 3:
            modifier = 2048.0

        # read data
        data = self.i2c.readfrom_mem(self.address, 0x3B, 6)  # read 6 bytes (accel data)
        x: float = (self._translate_pair(data[0], data[1])) / modifier
        y: float = (self._translate_pair(data[2], data[3])) / modifier
        z: float = (self._translate_pair(data[4], data[5])) / modifier

        return (x, y, z)

    def read_lpf_range(self) -> int:
        return self.i2c.readfrom_mem(self.address, 0x1A, 1)[0]

    def write_lpf_range(self, range: int) -> None:
        """
        Sets low pass filter range.
        :param range: Low pass range setting, 0-6. 0 = minimum filter, 6 = maximum filter.
        """

        # check range
        if range < 0 or range > 6:
            raise Exception("Range '" + str(range) + "' is not a valid low pass filter setting.")

        self.i2c.writeto_mem(self.address, 0x1A, bytes([range]))

    def _translate_pair(self, high: int, low: int) -> int:
        """Converts a byte pair to a usable value. Borrowed from https://github.com/m-rtijn/mpu6050/blob/0626053a5e1182f4951b78b8326691a9223a5f7d/mpu6050/mpu6050.py#L76C39-L76C39."""
        value = (high << 8) + low
        if value >= 0x8000:
            value = -((65535 - value) + 1)
        return value

    def _hex_to_index(self, range: int) -> int:
        """Converts a hexadecimal range setting to an integer (index), 0-3. This is used for both the gyroscope and accelerometer ranges."""
        if range == 0x00:
            return 0
        elif range == 0x08:
            return 1
        elif range == 0x10:
            return 2
        elif range == 0x18:
            return 3
        else:
            raise Exception("Found unknown gyro range setting '" + str(range) + "'")

    def _index_to_hex(self, index: int) -> int:
        """Converts an index integer (0-3) to a hexadecimal range setting. This is used for both the gyroscope and accelerometer ranges."""
        if index == 0:
            return 0x00
        elif index == 1:
            return 0x08
        elif index == 2:
            return 0x10
        elif index == 3:
            return 0x18
        else:
            raise Exception("Range index '" + index + "' invalid. Must be 0-3.")


class Mpu:
    """
    Mpu class to manage connection to sensor and have an up to date mpu6050 sensor running in a separate thread isolated
    from cycle speed for flight controller
    """
    # [ROLL, PITCH, YAW]
    ZERO = [0.0, 0.0, 0.0]
    DELTA_TIME = 0.1

    def __init__(self, flip=False, invert_x=False, invert_y=False):
        """
        :param flip: Flip X, Y axis
        :param invert_x: Invert X
        :param invert_y: Invert Y
        """
        i2c: I2C = I2C(
            config.Mpu.id,
            sda=config.Mpu.SDA,
            scl=config.Mpu.SCL,
        )
        # TODO: Enable Magnetometer
        self.ak8963 = None # Ak8963(i2c)
        self.mpu6500 = Mpu6500(i2c)

        self.flip = flip
        self.invert_x = invert_x
        self.invert_y = invert_y
        self._angles = self.__zero()

        self.__gyro = self.__zero()
        self.__accel = self.__zero()
        self.__magnetic = self.__zero()

        self.__gyro_calibration = self.__zero()
        # Last read in nanoseconds
        self.last_read = 0
        self.__kalman_x = KalmanAngle()
        self.__kalman_y = KalmanAngle()
        self.calibrate()

    @property
    def angles(self):
        angles = self._angles

        if self.flip:
            angles = [angles[1], angles[0], angles[2]]

        if self.invert_x:
            angles[0] *= -1

        if self.invert_y:
            angles[1] *= -1

        return angles

    def raw_gyro(self):
        """
        Gyro measured by the sensor. By default will return a 3-tuple of
        X, Y, Z axis values in rad/s as floats. To get values in deg/s pass
        `gyro_sf=SF_DEG_S` parameter to the MPU6500 constructor.
        """
        return [x for x in self.mpu6500.read_gyro_data()]

    def raw_accel(self):
        """
        Acceleration measured by the sensor. By default will return a
        3-tuple of X, Y, Z axis values in m/s^2 as floats. To get values in g
        pass `accel_fs=SF_G` parameter to the MPU6500 constructor.
        """
        return [x for x in self.mpu6500.read_accel_data()]

    def temperature(self):
        """
        The temperature in celsius as a float.
        """
        return self.mpu6500.read_temperature()

    def raw_magnetic(self):
        """
        X, Y, Z axis micro-Tesla (uT) as floats.
        """
        if self.ak8963 and (data := self.ak8963.magnetic()):
            return [x for x in data]
        return [0, 0, 0]

    @property
    def whoami(self):
        return self.mpu6500.who_am_i()

    def calibrate(self):
        if self.ak8963:
            self.ak8963.calibrate()

        # Run this code 2000 times
        for i in range(0, 2000):
            gyro_data = self.raw_gyro()

            # add gyro offset vector to calibration vector
            self.__add(self.__gyro_calibration, gyro_data)
            utime.sleep_ms(3)  # Delay 3us to simulate the 250Hz program loop

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

    def k_filtered_angle(self, ax_angle, ay_angle, gx, gy, dt):
        """
        Kalman filter to determine the change in angle by combining accelerometer and gyro values.
        """
        k_angle_x = self.__kalman_x.get_angle(ax_angle, gx, dt)
        k_angle_y = self.__kalman_y.get_angle(ay_angle, gy, dt)
        return k_angle_x, k_angle_y

    def m_filtered_angle(self, mx_angle, my_angle):
        """
        Calculate angle for magnetometer
        """
        filtered_magx, filtered_magy = 0, 0
        declination = -1 * 3.19

        def low_pass_filter(prev_value, new_value):
            return 0.85 * prev_value + 0.15 * new_value

        filtered_magx = low_pass_filter(filtered_magx, mx_angle)
        filtered_magy = low_pass_filter(filtered_magy, my_angle)

        heading_angle_in_degrees = math.atan2(filtered_magx, filtered_magy) * (180 / math.pi)
        heading_angle_in_degrees_plus_declination = heading_angle_in_degrees + declination

        if heading_angle_in_degrees_plus_declination < 0:
            heading_angle_in_degrees += 360
            heading_angle_in_degrees_plus_declination += 360

        return heading_angle_in_degrees_plus_declination

    def loop(self, *args, **kwargs):
        now = utime.time_ns()
        # Get time difference in seconds
        dt = (now - self.last_read) / (10**9 * 1.0)
        self.__gyro = self.raw_gyro()
        self.__accel = self.raw_accel()
        self.__magnetic = self.raw_magnetic()

        ax = self.__accel[0]
        ay = self.__accel[1]
        az = self.__accel[2]

        # This is angular velocity in each of the 3 directions
        gx = (self.__gyro[0] - self.__gyro_calibration[0])
        gy = (self.__gyro[1] - self.__gyro_calibration[1])
        gz = (self.__gyro[2] - self.__gyro_calibration[2])

        mx = self.__magnetic[0]
        my = self.__magnetic[1]

        # Calculate angle of inclination or tilt for the x and y axes with acquired acceleration vectors
        acc_angles = self.acc_angle(ax, ay, az)
        # Calculate angle of inclination or tilt for x,y and z axes with angular rates and dt
        gyr_angles = self.gyr_angle(gx, gy, gz, dt)
        # filtered tilt angle i.e. what we're after
        c_angle_x, c_angle_y = self.c_filtered_angle(acc_angles[0], acc_angles[1], gyr_angles[0], gyr_angles[1])
        k_angle_x, k_angle_y = self.k_filtered_angle(acc_angles[0], acc_angles[1], gx, gy, dt)

        # Use magnetometer to calculate yaw / z axis
        c_angle_z = self.m_filtered_angle(mx, my)

        self._angles = [c_angle_x, c_angle_y, c_angle_z]
        self.last_read = now

    @classmethod
    def __zero(cls):
        return [x for x in cls.ZERO]

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
