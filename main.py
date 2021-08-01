#!/usr/bin/python3
"""
CODE ON RASPBERRY PI

SHOULD RUN ON PI STARTUP and beep or something
"""
import os
import time
import motor

MOTOR_FL = motor.Motor(motor.FRONT_LEFT)
MOTOR_FR = motor.Motor(motor.FRONT_RIGHT)
MOTOR_BR = motor.Motor(motor.BACK_RIGHT)
MOTOR_BL = motor.Motor(motor.BACK_LEFT)


def arm_all():
    MOTOR_FL.arm()
    time.sleep(1)
    MOTOR_FR.arm()
    time.sleep(1)
    MOTOR_BR.arm()
    time.sleep(1)
    MOTOR_BL.arm()
    time.sleep(1)


def init():
    print('INITIALIZING DRONE')

    # ARM MOTORS
    print('ARMING MOTORS FL, FR, BR, BL')
    arm_all()
    print('FINISHED ARMING')


def main():
    """
    MAIN PROGRAM LOOP
    launch threads and
    """
    init()


if __name__ == "__main__":
    # Function exists as to not pollute the global namespace
    main()
