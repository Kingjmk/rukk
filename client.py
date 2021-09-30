#!/usr/bin/python3

"""
This is the client code, to be used to control PI Remotely using
keyboard or gamepad
"""
import sys
import socket
import threading
from multiprocessing import freeze_support
from utils import network
from utils.events import Event
import PySimpleGUI as sg
from _client.controller import GamepadController


EVENT_OUTPUT = '-OUTPUT-'
EVENT_RECONNECT = '-RECONNECT-'

CLIENT_THREAD = None
CONTROLLER_THREAD = None


def listen_client_func(_event, data):
    message = '%s -> %s' % (_event, data)
    WINDOW.write_event_value(EVENT_OUTPUT, message)


def connect(host, port):
    global CLIENT_THREAD, CONTROLLER_THREAD

    # RESET THREADS
    if CLIENT_THREAD:
        CLIENT_THREAD._stop()

    if CONTROLLER_THREAD:
        CONTROLLER_THREAD._stop()

    CLIENT_THREAD = None
    CONTROLLER_THREAD = None

    WINDOW.write_event_value(EVENT_OUTPUT, 'CONNECTING TO %s:%s' % (host, port))
    try:
        CLIENT_THREAD = network.Client(listen_client_func, host=host, port=int(port))
        CLIENT_THREAD.start()
        CLIENT_THREAD.send(Event.CONNECTED)
    except (socket.error, socket.gaierror, socket.herror):
        WINDOW.write_event_value(EVENT_OUTPUT, 'CONNECTION FAILED TO %s:%s' % (host, port))
        return False

    # RUN INPUT THREAD
    controller = GamepadController(CLIENT_THREAD.send)
    CONTROLLER_THREAD = threading.Thread(target=controller.run, daemon=True)
    CONTROLLER_THREAD.start()

    return True


def main(host='raspberrypi', port=7777, *args):
    global WINDOW

    layout = [
        [sg.Text('Output', font='Any 15')],
        [sg.Multiline(
            size=(65, 20), key='-ML-', autoscroll=True, reroute_stdout=True,
            write_only=True, reroute_cprint=True, disabled=True,
        ), sg.Button('Reconnect', key=EVENT_RECONNECT)],
    ]

    WINDOW = sg.Window('RemoteControl', layout, finalize=True)

    connect(host, port)

    # Event Loop
    while True:
        event, values = WINDOW.read()
        if event == sg.WIN_CLOSED or event == 'Exit':
            break

        elif event == EVENT_OUTPUT:
            output_message = values[EVENT_OUTPUT]
            sg.cprint(output_message)
        elif event == EVENT_RECONNECT:
            connect(host, port)

    WINDOW.close()


if __name__ == "__main__":
    freeze_support()
    print('Starting Program...')
    print('if you dont see a window, then something went wrong :(')
    main(*sys.argv[1:])
    exit(-1)
