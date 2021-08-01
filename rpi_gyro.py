import struct
import socket
from utils import mpu6050


class Output:
    def __init__(self):
        self.socket = socket.socket()
        host = '0.0.0.0'  # ip of raspberry pi
        port = 12345
        self.socket.bind((host, port))

    def send_data(self, data):
        ax, ay, az, gx, gy, gz = data
        data_packed = struct.pack('!dddddd', ax, ay, az, gx, gy, gz)
        self.conn.sendall(data_packed)

    def close_conn(self):
        self.conn.close()
        self.socket.close()

    def accept_conn(self):
        self.socket.listen(5)
        self.conn, addr = self.socket.accept()
        print('Got connection from', addr)


gx = gy = gz = 0

if __name__ == '__main__':
    output = Output()
    print("WAITING FOR CLIENT")

    client = mpu6050.Mpu6050(0x68)  # MPU6050 device address

    try:
        output.accept_conn()
        while True:
            gyro_data = client.get_gyro_data()
            accel_data = client.get_accel_data()
            gx += gyro_data['x']
            gy += gyro_data['y']
            gz += gyro_data['z']

            ax = gyro_data['x']
            ay = gyro_data['y']
            az = gyro_data['z']

            sensor_data = [ax, ay, az, gx, gy, gz]
            print("Gx=%.2f" % gx, "Gy=%.2f" % gy, "Gz=%.2f" % gz, "Ax=%.2f g" % ax, "Ay=%.2f g" % ay, "Az=%.2f g" % az)

            output.send_data(sensor_data)
    finally:
        output.close_conn()
