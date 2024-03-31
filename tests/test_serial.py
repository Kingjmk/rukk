#!/usr/bin/python3
import serial
import time

# Replace 'COM3' with the correct port for your system
ser = serial.Serial('COM5', 9600, timeout=1)

count = 1

try:
    while True:
        # Send data to Arduino
        # Wait for a short time to avoid reading incomplete data
        count += 1
        time.sleep(0.25)
        print('attempt to recv...')
        # Read data from Arduino
        if ser.in_waiting > 0:
            received_data = ser.readline().decode('ascii').rstrip()
            print(f"Received: {received_data}")


except KeyboardInterrupt:
    pass

finally:
    ser.close()
