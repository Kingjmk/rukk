import time
import datetime
from simple_pid import PID
from utils import network, helpers


def ease_in(value: int, target: int):
    dist = target - value
    return value + (dist * 0.7)


class QuadController:
    """
    Singleton for Flight controller
    """

    # Update cycles in Seconds
    cycle_speed = 0.01
    proportional_gain = 5.0  # TODO: auto calibrate or something
    int_throttle = 800
    max_throttle = 2000
    min_throttle = 600

    # offset of Roll, Pitch from Yaw axis perspective
    # aims to correct axis of an "X" shaped to align with an "+" shaped rotation axis for easier calculations
    # offset angle is provided in Degrees
    offset_angle = -45

    # Time duration before resetting controls to idle
    time_before_reset = datetime.timedelta(milliseconds=250)

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
        self.set_rotation()

    def arm_motors(self):
        """
        Arm all motors at once, this will shorten arming time
        """
        for motor in self.motors:
            motor.arm(0)
        time.sleep(4)

    def set_rotation(self, roll: float = 0, pitch: float = 0, yaw: float = 0):
        """
        Set Target Rotation
        """
        roll, pitch, yaw = helpers.rotate_on_z([roll, pitch, yaw], self.offset_angle)

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
        Set target Throttle
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

    def control(self):
        """
        Balance and Accelerate towards target rotation and throttle
        """

        """
        to get target rotation based on actual X shape we need to rotate the angle vector by {self.offset_angle} degrees
        then convert result from rad to degrees
        """

        rotation_vector = helpers.rotate_on_z(self.angles, self.offset_angle)

        """
        To get the amount of thrust to add to each axis we use the previously defined pids and the rotation vector 
        after accounting for offset of the sensor  
        """
        response_r = 1 * self.pid_r(rotation_vector[0])
        response_p = 1 * self.pid_p(rotation_vector[1])
        response_y = -1 * self.pid_y(rotation_vector[2])

        """
        after the response is calculated we change the speeds of the motors on both axis
        according to the pid response.
        """

        # ROLL AXIS
        self.motor_fr.pwm(self.throttle + response_r)
        self.motor_bl.pwm(self.throttle - response_r)

        # PITCH AXIS
        self.motor_fl.pwm(self.throttle + response_p)
        self.motor_br.pwm(self.throttle - response_p)

        print(
            f"{self.motor_fl.throttle} {self.motor_fr.throttle}\n"
            f"{self.motor_bl.throttle} {self.motor_br.throttle}\n"
            f"real  :{rotation_vector[0]}, {rotation_vector[1]}, {rotation_vector[2]}\n"
            f"target:{self.TARGET_ROLL_ANGLE}, {self.TARGET_PITCH_ANGLE}, {self.TARGET_YAW_ANGLE}\n"
        )

    def idle(self):
        self.set_throttle(self.min_throttle)
        self.set_rotation()

    def halt(self):
        for motor in self.motors:
            motor.halt()

    def run_event(self, event, data):
        if event == network.Event.STOP.value:
            self.set_throttle(self.min_throttle)
            self.set_rotation()

            for motor in self.motors:
                motor.halt(snooze=0)
            return

        elif event == network.Event.CONTROL.value:
            throttle_pct, roll, pitch, yaw = helpers.decode_control(data)
            throttle = self.throttle_pct_pwm(throttle_pct)
            self.set_throttle(throttle)
            self.set_rotation(roll, pitch, yaw)
            return
        elif event in [network.Event.CONNECTED.value]:
            print('\nCONNECTED TO CLIENT\n')
            # NOOP
            return

        raise Exception(f'EVENT {event} UNKNOWN')

    def loop(self):
        # TODO: fix this so the thing wont fly into the void
        # if self.update_timestamp and self.update_timestamp + self.time_before_reset > datetime.datetime.now():
        #     self.idle()

        self.control()

    def run(self):
        while True:
            self.loop()
            time.sleep(self.cycle_speed)
