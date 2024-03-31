import utime
# Copy flight-controller/sensor to
from sensor import Mpu


# Set up the MPU class
sensor = Mpu()

# continuously print the data
while True:
    print("ROTATION: ", str(sensor.angles), ' MAGNETIC ', str(sensor.__magnetic))
    sensor.loop()
    utime.sleep_ms(100)
    