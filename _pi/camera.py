import datetime
import math
import struct
import socket
import time
import cv2


MAX_DGRAM = 2 ** 16
MAX_IMAGE_DGRAM = MAX_DGRAM - 64


class CameraTransmit:
    """
    Camera TX Interface to get and transmit live video feed
    this is a custom class for easier extensibility and conversion to other languages if needed
    """

    def __init__(self, src=0, fps=24, width=320, height=240, port=7801, host='0.0.0.0'):
        self.width = width
        self.height = height
        self.video = cv2.VideoCapture(src)
        self.fps = fps
        self.port = port
        self.host = host
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def process_frame(self, frame):
        frame = cv2.resize(frame, [self.width, self.height])

        # Convert to grayscale
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        img = cv2.imencode(".jpg", frame)[1]

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

        data = img.tostring()
        size = len(data)
        _start = 0
        for count in reversed(range(0, math.ceil(size / MAX_IMAGE_DGRAM))):
            _end = min(size, _start + MAX_IMAGE_DGRAM)
            self.sock.send(struct.pack('B', count), data[_start:_end])
            _start = _end

    def run(self):
        while True:
            self.loop()
            time.sleep(1 / self.fps)

        self.video.release()
        cv2.destroyAllWindows()
        self.sock.close()
