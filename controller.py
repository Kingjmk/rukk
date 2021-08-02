import time
import math
from simple_pid import PID


def complementary_filter(angle, acc, gyro, dt, alpha):
    return (alpha * (angle + gyro * dt) + (1 - alpha) * acc) * (1 / (1 - alpha * dt))


class FlightController:
    """
    Singleton for Flight controller
    """
    cycle_speed = 0.05  # in Seconds

    def __init__(self, sensor, *motors):
        """
        sensor: an Mpu6050 instance,
        motors: Motor instances (FL,FR,BR,BL)
        """
        self.sensor = sensor
        self.motors = motors
        self.fl_motor = motors[0]
        self.fr_motor = motors[1]
        self.br_motor = motors[2]
        self.bl_motor = motors[3]

        # [ROLL, PITCH, YAW]
        self.angles = [0, 0, 0]

        self.TARGET_PITCH_ANGLE = 0
        self.TARGET_ROLL_ANGLE = 0

        """
        The quadcopter balancing is done via a PID controller
        The values of the PID, might be different for the ROLL and PITCH angles
        """
        # ROLL
        self.KR = [0.04, 0, 0]
        self.pid_r = PID(Kp=self.KR[0], Ki=self.KR[1], Kd=self.KR[2], setpoint=self.TARGET_ROLL_ANGLE)
        # PITCH
        self.KP = [0.04, 0, 0]
        self.pid_p = PID(Kp=self.KP[0], Ki=self.KP[1], Kd=self.KP[2], setpoint=self.TARGET_PITCH_ANGLE)

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

    def balance(self):
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
        self.fl_motor.pwd(self.fl_motor.width + response_r)
        self.br_motor.pwd(self.br_motor.width - response_r)

        # PITCH
        self.fr_motor.pwd(self.fr_motor.width + response_p)
        self.bl_motor.pwd(self.bl_motor.width - response_p)

    def run(self):
        """
        Should run inside loop
        """
        self.balance()
        time.sleep(self.cycle_speed)

    def stop(self):
        for motor in self.motors:
            motor.halt(snooze=0)
