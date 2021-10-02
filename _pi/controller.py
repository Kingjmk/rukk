import math
import time
import datetime
from simple_pid import PID
import utils
from utils import network

DEBUG = True


def ease_in(value: int, target: int):
    dist = target - value
    return value + (dist * 0.7)


class QuadController:
    """
    Singleton for Flight controller
    """
    cycle_speed = 0.01  # in Seconds
    int_throttle = 800
    max_throttle = 2000
    min_throttle = 650
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
        self.throttle = self.int_throttle

        """
        The quadcopter balancing is done via a PID controller
        The values of the PID, might be different for the ROLL and PITCH angles
        """
        self.KR = [self.proportional_gain, 0, 0]
        self.TARGET_ROLL_ANGLE = 0
        self.pid_r = None

        self.KP = [self.proportional_gain, 0, 0]
        self.TARGET_PITCH_ANGLE = 0
        self.pid_p = None

        self.KY = [self.proportional_gain * 0.1, 0, 0]
        self.TARGET_YAW_ANGLE = 0
        self.pid_y = None

        self.update_timestamp = None
        self.set_target()

    def arm_motors(self):
        """
        Arm all motors at once, this will shorten arming time
        """
        for motor in self.motors:
            motor.arm(0)
        time.sleep(4)

    @property
    def time_before_reset(self):
        """
        Time duration before resetting controls to idle
        """
        return datetime.timedelta(milliseconds=250)

    def set_target(self, roll: float = 0, pitch: float = 0, yaw: float = 0):
        """
        Set Target
        """

        self.update_timestamp = datetime.datetime.now()

        # ROLL
        self.TARGET_ROLL_ANGLE = roll
        self.pid_r = PID(Kp=self.KR[0], Ki=self.KR[1], Kd=self.KR[2], setpoint=self.TARGET_ROLL_ANGLE)

        # PITCH
        self.TARGET_PITCH_ANGLE = pitch
        self.pid_p = PID(Kp=self.KP[0], Ki=self.KP[1], Kd=self.KP[2], setpoint=self.TARGET_PITCH_ANGLE)

        # YAW
        self.TARGET_YAW_ANGLE = yaw
        self.pid_y = PID(Kp=self.KY[0], Ki=self.KY[1], Kd=self.KY[2], setpoint=self.TARGET_YAW_ANGLE)

    @classmethod
    def throttle_pct_pwm(cls, percentage: float) -> int:
        """
        Get PWM Throttle from percentage (0.0, 100.0)
        """
        percentage /= 100.0
        diff = cls.max_throttle - cls.min_throttle
        return int(cls.min_throttle + diff * percentage)

    def set_throttle(self, throttle: int):
        """
        Set Throttle
        """
        self.update_timestamp = datetime.datetime.now()
        self.throttle = throttle

    @property
    def angles(self):
        """
        Return current rotation from sensor
        """
        # TODO: Implement MPU with functional z axis
        x, y, z = self.sensor.angles
        return [x, y, 0]

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
        rotation_angle = math.radians(-45)
        rotation_vector = [
            math.cos(rotation_angle) * math.radians(x_angle) - math.sin(rotation_angle) * math.radians(y_angle),
            math.sin(rotation_angle) * math.radians(x_angle) + math.cos(rotation_angle) * math.radians(y_angle),
            z_angle,
        ]

        """
        In these two lines the error is calculated by the difference of the 
        actual angle - the desired angle.
        """
        response_r = 1 * self.pid_r(rotation_vector[0] - self.TARGET_ROLL_ANGLE)
        response_p = 1 * self.pid_p(rotation_vector[1] - self.TARGET_PITCH_ANGLE)
        response_y = -1 * self.pid_y(rotation_vector[2] - self.TARGET_YAW_ANGLE)

        """
        after the response is calculated we change the speeds of the motors
        according to that response.
        """
        if DEBUG:
            print(
                f"{self.motor_fl.throttle + response_p} {self.motor_fr.throttle + response_r}\n"
                f"{self.motor_bl.throttle - response_r} {self.motor_br.throttle - response_p}\n"
                f"real  :{rotation_vector[0]}, {rotation_vector[1]}, {rotation_vector[2]}\n"
                f"target:{self.TARGET_ROLL_ANGLE}, {self.TARGET_PITCH_ANGLE}, {self.TARGET_YAW_ANGLE}\n"
            )

        # ROLL AXIS
        self.motor_fr.pwm(self.motor_fr.throttle + response_r)
        self.motor_bl.pwm(self.motor_bl.throttle - response_r)

        # PITCH AXIS
        self.motor_fl.pwm(self.motor_fl.throttle + response_p)
        self.motor_br.pwm(self.motor_br.throttle - response_p)

    def idle(self):
        self.set_throttle(self.min_throttle)
        self.set_target()

    def halt(self):
        for motor in self.motors:
            motor.halt()

    def run_event(self, event, data):
        if event == network.Event.STOP.value:
            self.set_throttle(self.min_throttle)
            self.set_target()

            for motor in self.motors:
                motor.halt(snooze=0)
            return

        elif event == network.Event.CONTROL.value:
            throttle_pct, roll, pitch, yaw = utils.decode_control(data)
            throttle = self.throttle_pct_pwm(throttle_pct)
            self.set_throttle(throttle)
            self.set_target(roll, pitch, yaw)
            return
        elif event in [network.Event.CONNECTED.value]:
            print('\nCONNECTED TO CLIENT\n')
            # NOOP
            return

        raise Exception(f'EVENT {event} UNKNOWN')

    def run(self):
        """
        Should run inside loop
        """
        # TODO: fix this so the thing wont fly into the void
        # if self.update_timestamp and self.update_timestamp + self.time_before_reset > datetime.datetime.now():
        #     self.idle()

        self.accelerate()
        self.balance()

        time.sleep(self.cycle_speed)
