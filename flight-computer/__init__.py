#!/usr/bin/python3
"""
FLIGHT COMPUTER ON RPI
currently it will just run and send video feed to client
"""
import threading
import config

if config.CAMERA_ENABLED:
    from utils import camera


def start_server():
    global TELEMETRY_THREAD, SERVER_THREAD, CAMERA_THREAD, CONTROLLER

    if config.CAMERA_ENABLED:
        print('STARTING CAMERA STREAM...')
        camera_handler = camera.Server()
        VIDEO_THREAD = threading.Thread(target=camera_handler.run, daemon=True)
        VIDEO_THREAD.start()


def main():
    """
    MAIN PROGRAM LOOP
    launch server, controller and hardware
    """
    print('INITIALIZING RPI...')
    start_server()
    print('\n...\nREADY TO FLY!')

    # TODO: Maybe move to thread?
    # Infinite loop
    CONTROLLER.run()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        CONTROLLER.halt()
        print('\nStopping flight computer')
