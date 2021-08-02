#!/usr/bin/python3
"""
CODE ON RASPBERRY PI

SHOULD RUN ON PI STARTUP and beep or something
"""
import os
import time
import motor
import network

try:
    import pigpio
except ImportError:
    os.system("sudo pigpiod")
    time.sleep(1)
    import pigpio

pi = pigpio.pi()

MOTOR_FL = motor.Motor(pi, motor.FRONT_LEFT)
MOTOR_FR = motor.Motor(pi, motor.FRONT_RIGHT)
MOTOR_BR = motor.Motor(pi, motor.BACK_RIGHT)
MOTOR_BL = motor.Motor(pi, motor.BACK_LEFT)

# THREAD GLOBAL REFERENCE
SERVER_THREAD = None


def arm_all():
    print('ARMING MOTORS FL, FR, BR, BL')
    MOTOR_FL.arm()
    MOTOR_FR.arm()
    MOTOR_BL.arm()
    MOTOR_FR.arm()
    print('FINISHED ARMING')


def listen_server(event, data):
    pass


def start_server():
    global SERVER_THREAD

    print('STARTING SERVER')
    SERVER_THREAD = network.Server(1, listen_server)


def init():
    print('INITIALIZING DRONE')

    # ARM MOTORS
    arm_all()
    start_server()

    time.sleep(1)
    SERVER_THREAD.send('FINISHED')


def main():
    """
    MAIN PROGRAM LOOP
    launch threads and
    """
    init()


if __name__ == "__main__":
    # Function exists as to not pollute the global namespace
    main()
