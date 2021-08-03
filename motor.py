import time
import utils

"""
MOTOR GPIO MAPPING - CLOCK WISE

      4    front    17
        \         /
          \  -  /
  left     |   |    right
          /  -  \
        /         \
      22    back   27

17-22 is X or ROLL
4-27 is Y or PITCH

Z is vertical

"""

FRONT_LEFT = 4
FRONT_RIGHT = 17
BACK_RIGHT = 27
BACK_LEFT = 22

CALIBRATION_OFFSET = {
    FRONT_LEFT: 0,
    FRONT_RIGHT: 0,
    BACK_RIGHT: 0,
    BACK_LEFT: 0,
}


class Motor:
    # MAX ESC SPEED
    MAX_THROTTLE = 2400
    # MIN ESC SPEED
    MIN_THROTTLE = 650

    def __init__(self, conn, pin):
        self.conn = conn
        self.pin = pin
        self.throttle = 0

    def halt(self, snooze=1) -> None:
        """
        Switch of the GPIO, and un-arm the ESC.
        Ensure this runs, even on unclean shutdown.
        """
        self.pwm(throttle=self.MIN_THROTTLE, snooze=snooze)  # This 1 sec seems to *hasten* shutdown.
        self.pwm(0)

    def pwm(self, throttle: int, calibrated: bool = True, snooze=0):
        if calibrated:
            throttle += CALIBRATION_OFFSET[self.pin]

        self.throttle = utils.clamp(throttle, self.MIN_THROTTLE, self.MAX_THROTTLE)
        self.conn.set_servo_pulsethrottle(self.pin, self.throttle)

        if snooze:
            time.sleep(snooze)
        return

    def calibrate(self) -> None:
        """
        This trains the ESC on the full scale (max - min range) of the controller / pulse generator.
        This only needs to be done when changing controllers, transmitters, etc. not upon every power-on.
        NB: if already calibrated, full throttle will be applied (briefly)!  Disconnect propellers, etc.
        """
        self.pwm(throttle=self.MAX_THROTTLE)
        self.pwm(throttle=self.MAX_THROTTLE, snooze=2)  # Official docs: "about 2 seconds".
        self.pwm(throttle=self.MIN_THROTTLE, snooze=4)  # Time enough for the cell count, etc. beeps to play.

    def arm(self) -> None:
        """
        Arms the ESC. Required upon every power cycle.
        """
        self.pwm(throttle=self.MIN_THROTTLE, snooze=4)  # Time enough for the cell count, etc. beeps to play.
