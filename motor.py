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
    MAX_WIDTH = 2400
    # MIN ESC SPEED
    MIN_WIDTH = 650

    def __init__(self, conn, pin):
        self.conn = conn
        self.pin = pin
        self.width = 0

    def halt(self, snooze=1) -> None:
        """
        Switch of the GPIO, and un-arm the ESC.
        Ensure this runs, even on unclean shutdown.
        """
        self.pwm(width=self.MIN_WIDTH, snooze=snooze)  # This 1 sec seems to *hasten* shutdown.
        self.pwm(0)

    def pwm(self, width: int, calibrated: bool = True, snooze=0):
        if calibrated:
            width += CALIBRATION_OFFSET[self.pin]

        self.width = utils.clamp(width, self.MIN_WIDTH, self.MAX_WIDTH)
        self.conn.set_servo_pulsewidth(self.pin, self.width)

        if snooze:
            time.sleep(snooze)
        return

    def calibrate(self) -> None:
        """
        This trains the ESC on the full scale (max - min range) of the controller / pulse generator.
        This only needs to be done when changing controllers, transmitters, etc. not upon every power-on.
        NB: if already calibrated, full throttle will be applied (briefly)!  Disconnect propellers, etc.
        """
        self.pwm(width=self.MAX_WIDTH)
        self.pwm(width=self.MAX_WIDTH, snooze=2)  # Official docs: "about 2 seconds".
        self.pwm(width=self.MIN_WIDTH, snooze=4)  # Time enough for the cell count, etc. beeps to play.

    def arm(self) -> None:
        """
        Arms the ESC. Required upon every power cycle.
        """
        self.pwm(width=self.MIN_WIDTH, snooze=4)  # Time enough for the cell count, etc. beeps to play.
