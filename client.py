#!/usr/bin/python3

"""
This is the client code, to be used to control PI Remotely using
keyboard or gamepad
"""
import sys
import threading
from multiprocessing import freeze_support
from utils import network
from utils.events import Event
import PySimpleGUI as sg
from _client.controller import GamepadController


OUTPUT_EVENT = '-OUTPUT-'


def listen_client_func(_event, data):
    message = '%s -> %s' % (_event, data)
    WINDOW.write_event_value(OUTPUT_EVENT, message)


def init(host, port):
    global CLIENT_THREAD, CONTROLLER_THREAD, CONTROLLER
    WINDOW.write_event_value(OUTPUT_EVENT, 'CONNECTING TO %s:%s' % (host, port))
    CLIENT_THREAD = network.Client(1, listen_client_func, host=host, port=int(port))
    CLIENT_THREAD.start()
    CLIENT_THREAD.send(Event.CONNECTED)

    # RUN INPUT THREAD
    CONTROLLER = GamepadController(CLIENT_THREAD.send)
    CONTROLLER_THREAD = threading.Thread(target=CONTROLLER.run, daemon=True)
    CONTROLLER_THREAD.start()


def main(host='raspberrypi', port=7777, *args):
    global WINDOW

    layout = [
        [sg.Text('Output', font='Any 15')],
        [sg.Multiline(
            size=(65, 20), key='-ML-', autoscroll=True, reroute_stdout=True,
            write_only=True, reroute_cprint=True, disabled=True,
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
