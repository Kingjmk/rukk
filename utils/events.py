from enum import Enum


class Event(Enum):
    CONNECTED = 'CONNECTED'
    CONTROL = 'CONTROL'
    STOP = 'STOP'
