#!/usr/bin/python3
"""
CODE ON RPI

SHOULD RUN ON PI STARTUP and beep or something
"""
import os
import time
import threading
from utils import network, telemetry
from _pi import (
    motor, sensor, controller
)
import config

if config.CAMERA_ENABLED:
    from utils import camera

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


def listen_server_func(event, data):
    """
    Mapping events to controller actions
    """
    if CONTROLLER:
        CONTROLLER.run_event(event, data)
    else:
        print('CONTROLLER NOT INITIALIZED YET')


def start_server():
    global TELEMETRY_THREAD, SERVER_THREAD, CAMERA_THREAD

    print('STARTING SERVER...')
    SERVER_THREAD = network.Server(listen_server_func)
    SERVER_THREAD.start()

    print('STARTING TELEMETRY...')
    telemetry_handler = telemetry.Telemetry(SERVER_THREAD.send)
    TELEMETRY_THREAD = threading.Thread(target=telemetry_handler.run, daemon=True)
    TELEMETRY_THREAD.start()

    if config.CAMERA_ENABLED:
        print('STARTING CAMERA STREAM...')
        camera_handler = camera.Server()
        VIDEO_THREAD = threading.Thread(target=camera_handler.run, daemon=True)
        VIDEO_THREAD.start()


def start_controller():
    global CONTROLLER

    print('STARTING FLIGHT CONTROLLER...')
    CONTROLLER = controller.QuadController(SENSOR, MOTOR_FL, MOTOR_FR, MOTOR_BR, MOTOR_BL)
    print('ARMING MOTORS...')
    CONTROLLER.arm_motors()
    print('FINISHED ARMING!')


def main():
    """
    MAIN PROGRAM LOOP
    launch server, controller and hardware
    """
    print('INITIALIZING DRONE...')

    start_server()
    start_controller()
    print('\n...\nREADY TO FLY!')

    # TODO: Maybe move to thread?
    # Infinite loop
    CONTROLLER.run()


if __name__ == "__main__":
    # These are here since they actually do something on init
    MOTOR_FL = motor.Motor(pi, config.MOTOR_FRONT_LEFT, config.MOTOR_CALIBRATION[config.MOTOR_FRONT_LEFT])
    MOTOR_FR = motor.Motor(pi, config.MOTOR_FRONT_RIGHT, config.MOTOR_CALIBRATION[config.MOTOR_FRONT_RIGHT])
    MOTOR_BR = motor.Motor(pi, config.MOTOR_BACK_RIGHT, config.MOTOR_CALIBRATION[config.MOTOR_BACK_RIGHT])
    MOTOR_BL = motor.Motor(pi, config.MOTOR_BACK_LEFT, config.MOTOR_CALIBRATION[config.MOTOR_BACK_LEFT])

    SENSOR = sensor.Mpu(flip=True)

    # Function exists as to not pollute the global namespace
    try:
        main()
    except KeyboardInterrupt:
        CONTROLLER.halt()
        print('\nStopping flight controller')
