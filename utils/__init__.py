from . import network, mpu6050


def clamp(v, minn, maxn):
    return max(min(maxn, v), minn)


RAD_TO_DEG = 180 / 3.14159265359
