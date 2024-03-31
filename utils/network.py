import random


HOST = "0.0.0.0"
PORT = 7777
# Allow any (manage os side)
SEP_CHAR = '##'
EMPTY_CHAR = '__'
END_CHAR = '$$'


class NetworkEvent:
    CONNECTED = 'CONNECTED'
    CONTROL = 'CONTROL'
    STOP = 'STOP'
    TELEMETRY = 'TELEMETRY'

    @property
    def all(self):
        return [
            self.CONNECTED,
            self.CONTROL,
            self.STOP,
            self.TELEMETRY,
        ]


class BaseConnection:
    buf_size = 1024
    encoding = 'ascii'

    def __init__(self, target_func, host: str = HOST, port: int = PORT, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.target_func = target_func
        self.host = host
        self.port = port

    def handle_message(self, messages):
        """
        Handle Incoming event and run whatever in response
        """

        # This For loop will handle if the socket sent multiple messages at once
        print('MESSAGES', messages)
        for message in messages.split(END_CHAR):
            message = message.strip('')

            if not message or message == '':
                continue
            try:
                event, data = message.split(SEP_CHAR)
            except ValueError as e:
                print(f'ERROR ON MESSAGE: {message}')
                raise e

            self.target_func(event, data)

    @classmethod
    def _send(cls, _conn, event, data=EMPTY_CHAR):
        """
        Send message to socket
        """
        message = '%s%s%s%s' % (event, SEP_CHAR, data, END_CHAR)
        _conn.send(message.encode(cls.encoding))
