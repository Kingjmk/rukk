import time
import datetime
import struct
import socket
import cv2
import pickle

BUFFER_SIZE = 2 ** 12
HOST = '0.0.0.0'
PORT = 7801


class Server:
    """
    Camera TX Interface to get and transmit live video feed
    this is a custom class for easier extensibility and conversion to other languages if needed
    """

    def __init__(self, src=0, fps=24, width=320, height=240, host=HOST, port: int = PORT):
        self.width = width
        self.height = height
        self.video = cv2.VideoCapture(src)
        self.fps = fps

        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((host, port))
        self.server.listen(1)
        self.sock = None

    def process_frame(self, frame):
        frame = cv2.resize(frame, [self.width, self.height])

        # Convert to grayscale
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        img = cv2.imencode(".png", frame)[1]

        # Add timestamp
        img = cv2.putText(
            img,
            datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            (10, frame.shape[0] - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.35, (0, 0, 255), 1
        )

        return img

    def loop(self):
        _, frame = self.video.read()
        img = self.process_frame(frame)
        data = pickle.dumps(img)
        message = struct.pack("Q", len(data)) + data
        self.sock.sendall(message)

    def run(self):
        self.sock, client_addr = self.server.accept()
        # Send finish initializing event to whoever is on the other side
        while True:
            try:
                self.loop()
            except Exception as e:
                print(f'ERROR CONNECTION {e}')
                break

            time.sleep(1 / self.fps)

        self.sock.close()
        self.sock = None
        # WAIT FOR CONN AGAIN
        # YES THIS IS RECURSION THAT's THE POINT IT SHOULD RUN UNTIL THE END OF THE UNIVERSE (or battery)
        # TODO: should be idling on new connection NOT first connection
        self.run()


class Client:
    """
    Camera RX to receive video feed
    """
    def __init__(self, receive_callback, address: str = '127.0.0.1:8000'):
        host, port = address.split(':')
        self.receive_callback = receive_callback
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((host, port))
        self.payload_size = struct.calcsize("Q")
        self._data = b''

    def loop(self):
        while len(self._data) < self.payload_size:
            packet = self.sock.recv(BUFFER_SIZE)
            if not packet:
                break
            self._data += packet

        packed_msg_size = self._data[:self.payload_size]
        self._data = self._data[self.payload_size:]
        msg_size = struct.unpack("Q", packed_msg_size)[0]

        while len(self._data) < msg_size:
            self._data += self.sock.recv(BUFFER_SIZE)
        frame_data = self._data[:msg_size]
        self._data = self._data[msg_size:]
        frame = pickle.loads(frame_data)
        self.receive_callback(frame)

    def run(self):
        while True:
            self.loop()

        self.sock.close()
