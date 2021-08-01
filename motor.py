import os
import time

os.system("sudo pigpiod")
time.sleep(3)
import pigpio


pi = pigpio.pi()


# MOTOR GPIO MAPPING - CLOCK WISE
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
    max_value = 2000
    # MIN ESC SPEED
    min_value = 700
    # GPIO PIN
    pin = None

    def __init__(self, pin):
        self.pin = pin

    def arm(self):
        self.stop()
        time.sleep(1)
        self.move(self.min_value)
        time.sleep(1)
        self.move(self.max_value)
        time.sleep(1)
        self.move(self.min_value)

    def stop(self):
        pi.set_servo_pulsewidth(self.pin, 0)

    def move(self, speed: int, calibrated: bool = True):
        if calibrated:
            speed += CALIBRATION_OFFSET[self.pin]
        pi.set_servo_pulsewidth(self.pin, speed)
