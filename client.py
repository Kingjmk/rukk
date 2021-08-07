#!/usr/bin/python3

"""
This is the client code, to be used to control PI Remotely using
keyboard or gamepad
"""
import sys
import time
from multiprocessing import freeze_support
import threading
import keyboard

import utils
from utils import network
from events import Event
import PySimpleGUI as sg


OUTPUT_EVENT = '-OUTPUT-'


class KeyboardController:
    MAX_THROTTLE = 2400
    MIN_THROTTLE = 650

    def __init__(self):
        self.throttle = 800
        # [ROLL, PITCH, YAW]
        self.rotation = [0, 0, 0]

        self.move_angle = 15  # Change rate by degrees
        self.move_throttle = 50  # Change rate

        self.cycle_speed = 0.05
        # Pressed down state of all keys
        # TODO: Actually support input axis of gamepad in the future
        self._state = {
            'up': False,
            'down': False,
            'left': False,
            'right': False,
            'space': False,
            'shift': False,
        }

    def listen(self):
        keyboard.hook(self.run_event)
        keyboard.wait()

    def run_event(self, event: keyboard.KeyboardEvent):
        # Capture events and register current state
        # Only update when window is in focus
        self._state[event.name] = event.event_type == keyboard.KEY_DOWN

    def run(self):
        """
        Actually transform raw inputs into throttle and target angle
        should run every like 50ms
        """
        while True:
            _state = self._state
            pitch_controls = [_state['up'], _state['down']]
            if any(pitch_controls) and not all(pitch_controls):
                self.rotation[1] = self.move_angle * (- 1 if _state['up'] else 1)
            else:
                self.rotation[1] = 0

            roll_controls = [_state['left'], _state['right']]
            if any(roll_controls) and not all(roll_controls):
                self.rotation[0] = self.move_angle * (- 1 if _state['left'] else 1)
            else:
                self.rotation[0] = 0

            throttle_controls = [_state['space'], _state['shift']]
            if any(throttle_controls) and not all(throttle_controls):
                self.throttle += self.move_throttle * (- 1 if _state['shift'] else 1)
                self.throttle = utils.clamp(self.throttle, self.MIN_THROTTLE, self.MAX_THROTTLE)

            # And Send by network
            CLIENT_THREAD.send(Event.CONTROL, utils.encode_control(self.throttle, *self.rotation))
            time.sleep(self.cycle_speed)


def listen_client_func(_event, data):
    message = '%s -> %s' % (_event, data)
    # DO STUFF TO WINDOW
    WINDOW.write_event_value(OUTPUT_EVENT, message)


def init(host, port):
    global CLIENT_THREAD, INPUT_THREAD, CONTROLLER_THREAD, CONTROLLER
    WINDOW.write_event_value(OUTPUT_EVENT, 'CONNECTING TO %s:%s' % (host, port))
    CLIENT_THREAD = network.Client(1, listen_client_func, host=host, port=int(port))
    CLIENT_THREAD.start()
    CLIENT_THREAD.send(Event.CONNECTED)

    # RUN INPUT THREAD
    CONTROLLER = KeyboardController()
    INPUT_THREAD = threading.Thread(target=CONTROLLER.listen, daemon=True)
    CONTROLLER_THREAD = threading.Thread(target=CONTROLLER.run, daemon=True)
    INPUT_THREAD.start()
    CONTROLLER_THREAD.start()


def main(host='127.0.0.1', port=7777, *args):
    global WINDOW

    layout = [
        [sg.Text('Output', font='Any 15')],
        [sg.Multiline(
            size=(65, 20), key='-ML-', autoscroll=True, reroute_stdout=True,
            write_only=True, reroute_cprint=True
        )],
    ]

    WINDOW = sg.Window('RemoteControl', layout, finalize=True)

    init(host, port)

    # Event Loop
    while True:
        event, values = WINDOW.read()
        if event == sg.WIN_CLOSED or event == 'Exit':
            break

        elif event == OUTPUT_EVENT:
            output_message = values[OUTPUT_EVENT]
            sg.cprint(output_message)

    WINDOW.close()


if __name__ == "__main__":
    freeze_support()
    print('Starting Program...')
    print('if you dont see a window, then something went wrong :(')
    main(*sys.argv[1:])
    exit(-1)
