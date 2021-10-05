#!/usr/bin/python3
"""
CODE ON RPI

SHOULD RUN ON PI STARTUP and beep or something
"""
import os
import time
from utils import network
from _pi import (
    motor, sensor, controller
)

os.system("sudo pigpiod")
time.sleep(3)
import pigpio

pi = pigpio.pi()

"""
MOTOR GPIO MAPPING - CLOCK WISE

      4    front    17
        \         /
          \  -  /
  left     |   |    right
          /  -  \
        /         \
      22    back   27

17-22 is X or ROLL or sideways after -45deg
4-27 is Y or PITCH or tilt forward or backwards after -45deg

Z is vertical or YAW

"""

MOTOR_FRONT_LEFT = 4
MOTOR_FRONT_RIGHT = 17
MOTOR_BACK_RIGHT = 27
MOTOR_BACK_LEFT = 22

MOTOR_CALIBRATION = {
    MOTOR_FRONT_LEFT: 0,
    MOTOR_FRONT_RIGHT: 0,
    MOTOR_BACK_RIGHT: 0,
    MOTOR_BACK_LEFT: 0,
}


def listen_server_func(event, data):
    """
    Mapping events to controller actions
    """
    if CONTROLLER:
        CONTROLLER.run_event(event, data)
    else:
        print('CONTROLLER NOT INITIALIZED YET')


def start_server():
    global SERVER_THREAD

    print('STARTING SERVER')
    SERVER_THREAD = network.Server(listen_server_func)
    SERVER_THREAD.start()


def start_controller():
    global CONTROLLER

    print('STARTING FLIGHT CONTROLLER')
    CONTROLLER = controller.QuadController(SENSOR, MOTOR_FL, MOTOR_FR, MOTOR_BR, MOTOR_BL)
    print('ARMING MOTORS')
    CONTROLLER.arm_motors()
    print('FINISHED ARMING')


def main():
    """
    MAIN PROGRAM LOOP
    launch server, controller and hardware
    """
    print('INITIALIZING DRONE')

    start_server()
    start_controller()
    print('\n...\nREADY TO FLY')

    # TODO: Maybe move to thread?
    # Infinite loop
    CONTROLLER.run()


if __name__ == "__main__":
    # These are here since they actually do something on init
    MOTOR_FL = motor.Motor(pi, MOTOR_FRONT_LEFT, MOTOR_CALIBRATION[MOTOR_FRONT_LEFT])
    MOTOR_FR = motor.Motor(pi, MOTOR_FRONT_RIGHT, MOTOR_CALIBRATION[MOTOR_FRONT_RIGHT])
    MOTOR_BR = motor.Motor(pi, MOTOR_BACK_RIGHT, MOTOR_CALIBRATION[MOTOR_BACK_RIGHT])
    MOTOR_BL = motor.Motor(pi, MOTOR_BACK_LEFT, MOTOR_CALIBRATION[MOTOR_BACK_LEFT])

    SENSOR = sensor.Mpu(flip=True)

    # Function exists as to not pollute the global namespace
    try:
        main()
    except KeyboardInterrupt:
        CONTROLLER.halt()
        print('\nStopping flight controller')
