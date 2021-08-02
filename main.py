#!/usr/bin/python3
"""
CODE ON RPI

SHOULD RUN ON PI STARTUP and beep or something
"""
import os
import time
import motor
import network
from utils import mpu6050

try:
    import pigpio
except ImportError:
    os.system("sudo pigpiod")
    time.sleep(1)
    import pigpio

pi = pigpio.pi()

# THREAD GLOBAL REFERENCE
# yes its bad practice, i dont care
SERVER_THREAD = None


def arm_all():
    print('ARMING MOTORS FL, FR, BR, BL')
    MOTOR_FL.arm()
    MOTOR_FR.arm()
    MOTOR_BL.arm()
    MOTOR_FR.arm()
    print('FINISHED ARMING')


def listen_server_func(event, data):
    pass


def start_server():
    global SERVER_THREAD

    print('STARTING SERVER')
    SERVER_THREAD = network.Server(1, listen_server_func)


def main():
    """
    MAIN PROGRAM LOOP
    launch threads and
    """
    print('INITIALIZING DRONE')

    # ARM MOTORS
    arm_all()
    start_server()

    print('\n...\nREADY TO RUN')
    return


if __name__ == "__main__":
    # These are here since they actually do something
    MOTOR_FL = motor.Motor(pi, motor.FRONT_LEFT)
    MOTOR_FR = motor.Motor(pi, motor.FRONT_RIGHT)
    MOTOR_BR = motor.Motor(pi, motor.BACK_RIGHT)
    MOTOR_BL = motor.Motor(pi, motor.BACK_LEFT)

    SENSOR = mpu6050.Mpu6050(0x68)

    # Function exists as to not pollute the global namespace
    main()
