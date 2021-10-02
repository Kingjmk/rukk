import random
import socket
import threading
from utils.events import Event

# Allow any (manage os side)
HOST = '0.0.0.0'
PORT = 7777
SEP_CHAR = '#'
EMPTY_CHAR = '_'
END_CHAR = '$'


class BaseThread(threading.Thread):
    buf_size = 1024
    encoding = 'ascii'
    daemon = True

    def __init__(self, target_func, host=HOST, port: int = PORT):
        super().__init__()
        self.target_func = target_func
        self.threadId = random.randint(1, 1000)
        self.port = port
        self.host = host

    def handle_message(self, messages):
        """
        Handle Incoming event and run whatever in response
        """

        # This For loop will handle if the socket sent multiple messages at once
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
    def _send(cls, sock, event, data=EMPTY_CHAR):
        """
        Send message to socket
        """
        if isinstance(event, Event):
            event = event.value

        message = '%s%s%s%s' % (event, SEP_CHAR, data, END_CHAR)
        sock.send(message.encode('ascii'))


class Client(BaseThread):
    """
    Communication Client for RPI
    """

    def __init__(self, target_func, host=HOST, port: int = PORT):
        super().__init__(target_func, host)
        self.sock = socket.socket()
        self.sock.connect((host, port))

    def send(self, event, data=EMPTY_CHAR):
        """
        Send message to server
        """
        self._send(self.sock, event, data=data)

    def listen(self):
        try:
            data = self.sock.recv(self.buf_size)
        except ConnectionResetError:
            return -1

        message = data.decode(self.encoding)

        if not data:
            return -1
        self.handle_message(message)
        return 1

    def run(self):
        print(f'CONNECTED TO {self.host}:{self.port}')
        while True:
            resp = self.listen()
            if resp == -1:
                break

        self.sock.close()


class Server(BaseThread):
    """
    Communication Server for RPI
    """

    @property
    def connected(self):
        return self.sock is not None

    def __init__(self, target_func, host=HOST, port: int = PORT):
        super().__init__(target_func, host)
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((host, port))
        self.server.listen(1)
        self.sock = None

    def send(self, event, data=EMPTY_CHAR):
        """
        Send message to client
        """
        self._send(self.sock, event, data=data)

    def listen(self):
        try:
            data = self.sock.recv(self.buf_size)
        except ConnectionResetError:
            return -1

        message = data.decode(self.encoding)

        if not data:
            return -1
        self.handle_message(message)
        return 1

    def run(self):
        print('WAITING FOR CONNECTION')
        self.sock, client_addr = self.server.accept()

        print(f'CONNECTED TO {client_addr}')
        # Send finish initializing event to whoever is on the other side
        self.send(Event.CONNECTED)
        while True:
            resp = self.listen()
            if resp == -1:
                break

        self.sock.close()
        self.sock = None
        # WAIT FOR CONN AGAIN
        # YES THIS IS RECURSION THAT's THE POINT IT SHOULD RUN UNTIL THE END OF THE UNIVERSE (or battery)
        print('CONNECTION RESET, WAITING FOR NEW CONNECTION')
        # TODO: should be idling on new connection NOT first connection
        self.run()
