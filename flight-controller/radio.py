import socket
from utils.network import BaseConnection, NetworkEvent, EMPTY_CHAR


class ServerConnection(BaseConnection):
    """
    Communication Server for RPI using Wifi
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind(('0.0.0.0', self.port))
        self.server.listen(1)
        self._conn = None

    def send(self, event, data=EMPTY_CHAR):
        """
        Send message to client
        """
        if self._conn:
            print(f'attempt to send {data}')
            self._send(self._conn, event, data=data)

    def listen(self):
        try:
            data = self._conn.recv(self.buf_size)
        except Exception:
            return -1

        message = data.decode(self.encoding)

        if not data:
            return -1
        self.handle_message(message)
        return 1

    def connect(self):
        print('WAITING FOR CONNECTION')
        self._conn, client_addr = self.server.accept()

        print(f'CONNECTED TO {client_addr}')
        # Send finish initializing event to whoever is on the other side
        self.send(NetworkEvent.CONNECTED)

    def loop(self):
        resp = self.listen()
        if resp == -1:
            return -1

        return 1

    def run(self):
        self.connect()

        while True:
            resp = self.listen()
            if resp == -1:
                break

        self._conn.close()
        self._conn = None
        # WAIT FOR CONN AGAIN
        # YES THIS IS RECURSION THAT's THE POINT IT SHOULD RUN UNTIL THE END OF THE UNIVERSE (or battery)
        print('CONNECTION RESET, WAITING FOR NEW CONNECTION')
        # TODO: should be idling on new connection NOT first connection
        self.run()
