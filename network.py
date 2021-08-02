import socket
import threading


# Allow any (manage os side)
HOST = '0.0.0.0'
PORT = 7777
SEP_CHAR = '#'


class BaseThread(threading.Thread):
    buf_size = 1024
    encoding = 'ascii'
    daemon = True

    def __init__(self, thread_id, target_func, host=HOST, port: int = PORT):
        super().__init__()
        self.target_func = target_func
        self.threadId = thread_id
        self.port = port
        self.host = host


class Client(BaseThread):
    """
    Communication Client for RPI
    """
    def __init__(self, thread_id, target_func, host=HOST, port: int = PORT):
        super().__init__(thread_id, target_func, host)
        self.sock = socket.socket()
        self.sock.connect((host, port))

    def handle_message(self, message):
        """
        Handle Incoming event and run whatever in response
        """
        event, data = message.split(SEP_CHAR)
        self.target_func(message, data)

    def send(self, event, data=''):
        """
        Send message to client
        """
        message = '%s%s%s' % (event, SEP_CHAR, data)
        self.sock.send(message.encode('ascii'))

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
        return self._sock is not None

    def __init__(self, thread_id, target_func, host=HOST, port: int = PORT):
        super().__init__(thread_id, target_func, host)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((host, port))
        self.sock.listen(1)
        self._sock = None

    def handle_message(self, message):
        """
        Handle Incoming event and run whatever in response
        """
        event, data = message.split(SEP_CHAR)
        self.target_func(message, data)

    def send(self, event, data=''):
        """
        Send message to client
        """
        message = '%s%s%s' % (event, SEP_CHAR, data)
        self._sock.send(message.encode('ascii'))

    def listen(self):
        try:
            data = self._sock.recv(self.buf_size)
        except ConnectionResetError:
            return -1

        message = data.decode(self.encoding)

        if not data:
            return -1
        self.handle_message(message)
        return 1

    def run(self):
        print('WAITING FOR CONNECTION')
        self._sock, client_addr = self.sock.accept()

        print(f'CONNECTED TO {client_addr}')
        while True:
            resp = self.listen()
            if resp == -1:
                break

        self._sock.close()
        self._sock = None
        # WAIT FOR CONN AGAIN
        # YES THIS IS RECURSION THAT's THE POINT
        print('CONNECTION RESET, WAITING FOR CONNECTION')
        self.run()
