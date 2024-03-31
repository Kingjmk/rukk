import logging
import socket
from utils.network import BaseConnection, EMPTY_CHAR, NetworkEvent
logger = logging.Logger(__name__)


class ClientConnection(BaseConnection):
    """
    Communication Client for RPI using Wifi
    We first use an arduino to receive radio signal using Wifi, then we read it from serial
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._conn = socket.socket()
        self._conn.connect((self.host, self.port))

    def send(self, event, data=EMPTY_CHAR):
        """
        Send message to server
        """
        self._send(self._conn, event, data=data)

    def listen(self):
        try:
            data = self._conn.recv(self.buf_size)
            print('received data', data)
        except Exception as e:
            logger.error(e)
            print('error', e)
            return -1

        message = data.decode(self.encoding)

        if not data:
            return -1
        self.handle_message(message)
        return 1

    def run(self):
        print(f'CONNECTED TO {self.host}:{self.port}')
        while True:
            try:
                resp = self.listen()
            except Exception as e:
                logger.error(e)
                resp = -1

            if resp == -1:
                break

        self._conn.close()
