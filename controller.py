import time
import datetime
import math
from simple_pid import PID
from events import Event
from utils import decode_control


def complementary_filter(angle, acc, gyro, dt, alpha):
    return (alpha * (angle + gyro * dt) + (1 - alpha) * acc) * (1 / (1 - alpha * dt))


def ease_in(value: int, target: int):
    dist = target - value
    return value + (dist * 0.7)


class FlightController:
    """
    Singleton for Flight controller
    """
    cycle_speed = 0.05  # in Seconds
    initial_speed = 1000

    def __init__(self, sensor, *motors):
        """
        sensor: an Mpu6050 instance,
        motors: Motor instances (FL,FR,BR,BL)
        """
        self.sensor = sensor
        self.motors = motors
        self.motor_fl = motors[0]
        self.motor_fr = motors[1]
        self.motor_br = motors[2]
        self.motor_bl = motors[3]

        # [ROLL, PITCH, YAW]
        self.angles = [0, 0, 0]

        # THROTTLE
        self.throttle = self.initial_speed

        """
        The quadcopter balancing is done via a PID controller
        The values of the PID, might be different for the ROLL and PITCH angles
        """
        self.KR = [0.04, 0, 0]
        self.KP = [0.04, 0, 0]
        self.TARGET_PITCH_ANGLE = 0
        self.TARGET_ROLL_ANGLE = 0
        self.pid_p = None
        self.pid_r = None
        self.update_timestamp = None
        self.set_target()

    @property
    def time_before_reset(self):
        """
        Time duration before resetting controls to idle
        """
        return datetime.timedelta(seconds=2)

    def set_target(self, roll: float = 0, pitch: float = 0, yaw: float = 0):
        self.update_timestamp = datetime.datetime.now()

        # ROLL
        self.TARGET_ROLL_ANGLE = roll
        self.pid_r = PID(Kp=self.KR[0], Ki=self.KR[1], Kd=self.KR[2], setpoint=self.TARGET_ROLL_ANGLE)

        # PITCH
        self.TARGET_ROLL_ANGLE = pitch
        self.pid_p = PID(Kp=self.KP[0], Ki=self.KP[1], Kd=self.KP[2], setpoint=self.TARGET_PITCH_ANGLE)

    def set_throttle(self, throttle: int):
        self.throttle = throttle

    def get_roll_yaw_pitch(self):
        coeff = 1 / (30 * pow(10, 3))
        gd = self.sensor.get_gyro_data()
        ad = self.sensor.get_accel_data()
        gx, gy, gz = gd['x'], gd['y'], gd['z']
        ax, ay, az = ad['x'], ad['y'], ad['z']

        g = math.sqrt(math.pow(ax, 2) + math.pow(ay, 2) + math.pow(az, 2))

        roll = math.acos(ay / g) * 180 / math.pi - 90

        pitch = math.acos(ax / g) * 180 / math.pi - 90

        yaw = -math.acos(az / g) * 180 / math.pi

        # APPLYING FILTERS
        self.angles[0] = (complementary_filter(self.angles[0], roll, gx, coeff, 0.98))
        self.angles[1] = (complementary_filter(self.angles[1], pitch, gy, coeff, 0.98))
        return self.angles

    def accelerate(self):
        """
        Accelerate towards target throttle
        """
        for motor in self.motors:
            motor.pwm(ease_in(motor.throttle, self.throttle))

    def balance(self):
        """
        Balance towards target angle
        """
        vector = self.get_roll_yaw_pitch()
        tmp = [0, 0, 0]

        # copy the values to a new vector
        for i in range(0, len(vector)):
            tmp[i] = vector[i]

        tmp1 = tmp[0]
        tmp[0] += tmp[1]
        tmp[1] -= tmp1

        """
        In these two lines the error is calculated by the difference of the 
        actual angle - the desired angle.
        """
        response_r = (self.pid_r(tmp[0] - self.TARGET_ROLL_ANGLE))
        response_p = -(self.pid_p(tmp[1] - self.TARGET_PITCH_ANGLE))

        """
        after the response is calculated we change the speeds of the motors
        according to that response.
        """

        # ROLL
        self.motor_fl.pwm(self.motor_fl.throttle + response_r)
        self.motor_br.pwm(self.motor_br.throttle - response_r)

        # PITCH
        self.motor_fr.pwm(self.motor_fr.throttle + response_p)
        self.motor_bl.pwm(self.motor_bl.throttle - response_p)

    def run_event(self, event, data):
        if Event.STOP == event:
            self.set_target()
            self.set_throttle(0)

            for motor in self.motors:
                motor.halt(snooze=0)

        if Event.CONTROL == event:
            throttle, roll, pitch, yaw = decode_control(data)
            self.set_target(roll, pitch, yaw)
            self.set_throttle(throttle)

    def run(self):
        """
        Should run inside loop
        """
        if self.update_timestamp and self.update_timestamp + self.time_before_reset < datetime.datetime.now():
            self.set_target()
        self.accelerate()
        self.balance()
        time.sleep(self.cycle_speed)
