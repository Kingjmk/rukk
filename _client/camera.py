import struct
import socket
import cv2
import numpy as np


MAX_DGRAM = 2 ** 16
MAX_IMAGE_DGRAM = MAX_DGRAM - 64


class CameraReceive:
    """
    Camera RX to receive video feed
    """

    def __init__(self, receive_callback, port=7801, host='0.0.0.0'):
        self.receive_callback = receive_callback
        self.port = port
        self.host = host
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.host, self.port))
        self._data = b''

    def loop(self):
        seg, _ = self.sock.recvfrom(MAX_DGRAM)
        self._data += seg[1:]
        if not struct.unpack('B', seg[0:1])[0] > 1:
            img = cv2.imdecode(np.fromstring(self._data, dtype=np.uint8), 1)
            self.receive_callback(img)
            self._data = b''

    def run(self):
        while True:
            self.loop()

        self.sock.close()
