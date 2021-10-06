import time
from utils import helpers


class Motor:
    # MAX ESC SPEED
    MAX_THROTTLE = 2400
    # MIN ESC SPEED
    MIN_THROTTLE = 650

    def __init__(self, conn, pin, calibration):
        self.conn = conn
        self.pin = pin
        self.throttle = 0
        self.calibration = calibration

    def halt(self, snooze=1) -> None:
        """
        Switch off the GPIO, and un-arm the ESC.
        Ensure this runs, even on unclean shutdown.
        """
        self.pwm(throttle=self.MIN_THROTTLE, snooze=snooze)  # This 1 sec seems to *hasten* shutdown.
        self.pwm(0)

    def pwm(self, throttle: int, calibrated: bool = True, snooze=0):
        if calibrated:
            throttle += self.calibration

        self.throttle = helpers.clamp(throttle, self.MIN_THROTTLE, self.MAX_THROTTLE)
        self.conn.set_servo_pulsewidth(self.pin, self.throttle)

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

    def arm(self, snooze: int = 4) -> None:
        """
        Arms the ESC. Required upon every power cycle.
        """

        # Time enough for the cell count, etc. beeps to play.
        self.pwm(throttle=self.MIN_THROTTLE, snooze=snooze)
