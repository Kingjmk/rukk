import math
import time
import datetime
from simple_pid import PID
from events import Event
import utils

DEBUG = True


def ease_in(value: int, target: int):
    dist = target - value
    return value + (dist * 0.7)


class FlightController:
    """
    Singleton for Flight controller
    """
    cycle_speed = 0.05  # in Seconds
    initial_throttle = 800
    proportional_gain = 20.0

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

        # THROTTLE
        self.throttle = self.initial_throttle

        """
        The quadcopter balancing is done via a PID controller
        The values of the PID, might be different for the ROLL and PITCH angles
        """
        self.KR = [self.proportional_gain, 0, 0]
        self.KP = [self.proportional_gain, 0, 0]
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
        self.update_timestamp = datetime.datetime.now()
        self.throttle = throttle

    @property
    def angles(self):
        return self.sensor.angles

    def accelerate(self):
        """
        Accelerate towards target throttle
        """
        for motor in self.motors:
            motor.pwm(ease_in(motor.throttle, self.throttle))

    def balance(self):
        """
        Balance towards target rotation
        """

        """
        to get target rotation based on actual X shape we need to rotate the angle vector by 45 degrees
        """
        x_angle, y_angle, z_angle = self.angles
        rotation_angle = math.radians(45)
        rotation_vector = [
            math.cos(rotation_angle) * math.radians(x_angle) - math.sin(rotation_angle) * math.radians(y_angle),
            math.sin(rotation_angle) * math.radians(x_angle) + math.cos(rotation_angle) * math.radians(y_angle),
        ]

        """
        In these two lines the error is calculated by the difference of the 
        actual angle - the desired angle.
        """
        response_r = self.pid_r(rotation_vector[0] - self.TARGET_ROLL_ANGLE)
        response_p = -1 * (self.pid_p(rotation_vector[1] - self.TARGET_PITCH_ANGLE))

        """
        after the response is calculated we change the speeds of the motors
        according to that response.
        """
        if DEBUG:
            print('-----')
            m = f'{self.motor_fl.throttle - response_p} {self.motor_fr.throttle - response_r}\n'
            m += f'\n{self.motor_bl.throttle + response_r} {self.motor_br.throttle + response_p}\n'
            print(m)

        # ROLL
        self.motor_fr.pwm(self.motor_fr.throttle - response_r)
        self.motor_bl.pwm(self.motor_bl.throttle + response_r)

        # PITCH
        self.motor_fl.pwm(self.motor_fl.throttle - response_p)
        self.motor_br.pwm(self.motor_br.throttle + response_p)

    def idle(self):
        self.set_target()
        self.set_throttle(self.initial_throttle)

    def halt(self):
        for motor in self.motors:
            motor.halt()

    def run_event(self, event, data):
        if Event.STOP == event:
            self.set_target()
            self.set_throttle(0)

            for motor in self.motors:
                motor.halt(snooze=0)

        if Event.CONTROL == event:
            throttle, roll, pitch, yaw = utils.decode_control(data)
            self.set_target(roll, pitch, yaw)
            self.set_throttle(throttle)

    def run(self):
        """
        Should run inside loop
        """
        if self.update_timestamp and self.update_timestamp + self.time_before_reset < datetime.datetime.now():
            self.idle()

        self.accelerate()
        self.balance()

        time.sleep(self.cycle_speed)
