"""
This is the client code, to be used to control PI Remotely using
keyboard or gamepad
"""
import logging
import threading
import PySimpleGUI as sg
from multiprocessing import freeze_support
from utils import telemetry, helpers
from client.controller import GamepadController, KeyboardController
from client.radio import NetworkEvent, ClientConnection
import config

logger = logging.Logger(__name__)

if config.CAMERA_ENABLED:
    from utils import camera

EVENT_OUTPUT = '-OUTPUT-'
EVENT_RECONNECT = '-RECONNECT-'
EVENT_CAMERA_FEED = '-CAMERA_FEED-'
EVENT_IP_ADDRESS_FIELD = '-EVENT_IP_ADDRESS_FIELD-'

CLIENT_THREAD = None
CONTROLLER_THREAD = None
CAMERA_THREAD = None


CURRENT_HOST = config.DEFAULT_HOST
CURRENT_PORT = config.DEFAULT_PORT


def listen_client_func(event, data):
    if event == NetworkEvent.TELEMETRY:
        # Update Telemetry UI with new value
        telemetry_name, telemetry_data = helpers.decode_telemetry_record(data)
        WINDOW[telemetry_name].update(value=telemetry_data)
    else:
        WINDOW.write_event_value(EVENT_OUTPUT, '%s -> %s' % (event, data))


def listen_camera_func(img):
    WINDOW[EVENT_CAMERA_FEED].update(value=img.tobytes())


def connect(host, port):
    global CLIENT_THREAD, CONTROLLER_THREAD, CAMERA_THREAD

    # RESET THREADS
    if CLIENT_THREAD:
        try:
            CLIENT_THREAD._stop()
        except Exception as e:
            logger.error(e)
            pass

    if CONTROLLER_THREAD:
        CONTROLLER_THREAD._stop()

    if CAMERA_THREAD:
        CAMERA_THREAD._stop()

    CLIENT_THREAD = None
    CONTROLLER_THREAD = None
    CAMERA_THREAD = None

    WINDOW.write_event_value(EVENT_OUTPUT, 'CONNECTING TO %s:%s' % (host, port))
    try:
        network_client = ClientConnection(listen_client_func, host=host, port=int(port))
        CLIENT_THREAD = threading.Thread(target=network_client.run, daemon=True)
        CLIENT_THREAD.start()
        network_client.send(NetworkEvent.CONNECTED)
    except Exception as e:
        logger.error(e)
        WINDOW.write_event_value(EVENT_OUTPUT, 'CONNECTION FAILED')
        return False

    controller = KeyboardController(network_client.send)
    CONTROLLER_THREAD = threading.Thread(target=controller.run, daemon=True)
    CONTROLLER_THREAD.start()

    if config.CAMERA_ENABLED:
        camera_handler = camera.Client(listen_camera_func, host=host)
        CAMERA_THREAD = threading.Thread(target=camera_handler.run, daemon=True)
        CAMERA_THREAD.start()

    return True


def main():
    global WINDOW, CURRENT_HOST, CURRENT_PORT

    output_col = [
        [sg.Text('Output', font='Any 15')],
        [sg.Output(size=(65, 20), key=EVENT_OUTPUT, echo_stdout_stderr=True)]
    ]

    telemetry_col = [
        [sg.Text('Telemetry', font='Any 15')],
    ] + [[sg.Text('%s:' % record, size=(10, None)), sg.Text('NONE', key=record.strip(), size=(20, None))] for record in telemetry.TelemetryRecord.all()]

    layout = [
        [
            sg.Text('Camera Feed', font='Any 15'),
            sg.Image(filename='', key=EVENT_CAMERA_FEED)
        ],
        [
            sg.Column(output_col, vertical_alignment='top', pad=(0, 0)),
            sg.Column(telemetry_col, vertical_alignment='top', pad=(0, 0)),
        ],
        [
            sg.InputText(default_text=CURRENT_HOST, tooltip='IP Address', key=EVENT_IP_ADDRESS_FIELD),
            sg.Button('Reconnect', key=EVENT_RECONNECT)
        ],
    ]

    WINDOW = sg.Window('RemoteControl', layout, finalize=True)

    # Event Loop
    while True:
        event, values = WINDOW.read()
        if event == sg.WIN_CLOSED or event == 'Exit':
            break

        elif event == EVENT_OUTPUT:
            print(values[EVENT_OUTPUT])
        elif event == EVENT_RECONNECT:
            CURRENT_HOST = values[EVENT_IP_ADDRESS_FIELD]
            connect(CURRENT_HOST, CURRENT_PORT)

    WINDOW.close()


if __name__ == "__main__":
    freeze_support()
    print('Starting Program...')
    print('if you dont see a window, then something went wrong :(')
    main()
    exit(-1)
