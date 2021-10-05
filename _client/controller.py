import keyboard
import time
import utils
from utils import network
import pygame

# Throttle in percentage
INT_THROTTLE = 20
MAX_THROTTLE = 100
MIN_THROTTLE = 0


class KeyboardController:
    def __init__(self, send_callback):
        self.send_callback = send_callback
        self.throttle = INT_THROTTLE
        # [ROLL, PITCH, YAW]
        self.rotation = [0, 0, 0]

        # YAW Rotation factor, currently this is just a flag since we dont have a compass meter yet
        self.rotation_angle = 90
        self.move_angle = 15  # Change rate by degrees
        self.move_throttle = 5  # Change rate

        self.cycle_speed = 0.05
        # Pressed down state of all keys
        self._state = {
            'left': False,
            'right': False,
            'up': False,
            'down': False,
            'a': False,  # Rotation on YAW
            'd': False,  # Rotation on YAW
            'w': False,  # Throttle Increase
            's': False,  # Throttle Decrease
        }

    def run_event(self, event: keyboard.KeyboardEvent):
        # Capture events and register current state
        # Only update when window is in focus
        self._state[event.name] = event.event_type == keyboard.KEY_DOWN

    def loop(self):
        _state = self._state
        roll_controls = [_state['left'], _state['right']]
        if any(roll_controls) and not all(roll_controls):
            self.rotation[0] = self.move_angle * (- 1 if _state['left'] else 1)
        else:
            self.rotation[0] = 0

        pitch_controls = [_state['up'], _state['down']]
        if any(pitch_controls) and not all(pitch_controls):
            self.rotation[1] = self.move_angle * (- 1 if _state['up'] else 1)
        else:
            self.rotation[1] = 0

        yaw_controls = [_state['a'], _state['d']]
        if any(yaw_controls) and not all(yaw_controls):
            self.rotation[2] = self.rotation_angle * (- 1 if _state['d'] else 1)
        else:
            self.rotation[2] = 0

        throttle_controls = [_state['w'], _state['s']]
        if any(throttle_controls) and not all(throttle_controls):
            self.throttle += self.move_throttle * (- 1 if _state['s'] else 1)
            self.throttle = utils.clamp(self.throttle, MIN_THROTTLE, MAX_THROTTLE)

        self.send_callback(network.Event.CONTROL, utils.encode_control(self.throttle, *self.rotation))

    def run(self):
        """
        Actually transform raw inputs into throttle and target angle
        should run every like 50ms
        """

        keyboard.hook(self.run_event)
        while True:
            self.loop()
            time.sleep(self.cycle_speed)


class GamepadController:
    """
    Controller Scheme

    ------------------------------------------------------------
    |        Left Thumbstick             Right Thumbstick      |
    |                                                          |
    |          + THROTTLE                   + PITCH            |
    |                                                          |
    |    - YAW           + YAW        - ROLL         + ROLL    |
    |                                                          |
    |          - THROTTLE                   - PITCH            |
    |                                                          |
    ------------------------------------------------------------
    """

    def __init__(self, send_callback):
        self.send_callback = send_callback
        self.throttle = INT_THROTTLE
        # [ROLL, PITCH, YAW]
        self.rotation = [0, 0, 0]

        # YAW Rotation factor, currently this is just a flag since we dont have a compass meter yet
        self.rotation_angle = 90
        self.max_angle = 25  # Max angle -/+
        self.cycle_speed = 0.05

        self.AXIS = {
            'ROLL': 2,
            'PITCH': 4,
            'YAW': 0,
            'THROTTLE': 1
        }

        pygame.init()
        pygame.joystick.init()
        self.joystick = pygame.joystick.Joystick(0)

    def loop(self):
        pygame.event.pump()

        roll_axis = self.joystick.get_axis(self.AXIS['ROLL'])
        if abs(roll_axis):
            self.rotation[0] = int(self.max_angle * roll_axis)
        else:
            self.rotation[0] = 0

        pitch_axis = self.joystick.get_axis(self.AXIS['PITCH']) * -1
        if abs(pitch_axis):
            self.rotation[1] = int(self.max_angle * pitch_axis)
        else:
            self.rotation[1] = 0

        yaw_axis = self.joystick.get_axis(self.AXIS['YAW'])

        if abs(yaw_axis):
            self.rotation[2] = self.rotation_angle * (-1 if yaw_axis < 0 else 1)
        else:
            self.rotation[2] = 0

        # This normalizes -1.0 to 1.0 range to be 0, 1.0 range * 100 is percentage
        throttle_axis = (self.joystick.get_axis(self.AXIS['THROTTLE']) * -1 + 1) / 2.0
        self.throttle = utils.clamp(round(throttle_axis * 100, 2), MIN_THROTTLE, MAX_THROTTLE)

        self.send_callback(network.Event.CONTROL, utils.encode_control(self.throttle, *self.rotation))
        #print(f'{self.throttle}, {self.rotation[0]}, {self.rotation[1]}, {self.rotation[2]}')

    def run(self):
        """
        Actually transform raw inputs into throttle and target angle
        should run every like 50ms
        """

        while True:
            self.loop()
            time.sleep(self.cycle_speed)
