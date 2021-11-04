import copy
import math


def rotate_on_z(vector, angle) -> list:
    """
    Rotate vector on z or yaw axis by angle
    @param vector: tuple Vector to rotate
    @param angle: float angle in deg

    """

    theta = math.radians(angle)
    cs = math.cos(theta)
    sn = math.sin(theta)

    result = copy.copy(vector)

    result[0] = round(vector[0] * cs - vector[1] * sn, 2)
    result[1] = round(vector[0] * sn + vector[1] * cs, 2)

    return result


def clamp(value, minn, maxn):
    """
    Limit value inside a specific range defined by `minn` for lower bound and `maxn` for upper bound.

    @param value: value
    @param minn: lower bound value
    @param maxn: upper bound value
    @return: clamped value
    """
    return max(min(maxn, value), minn)


def decode_control(data):
    # Data should always have 4 keys
    throttle, roll, pitch, yaw = data.split('/')
    return float(throttle), int(roll), int(pitch), int(yaw)


def encode_control(throttle, roll, pitch, yaw):
    return '%d/%d/%d/%d' % (throttle, roll, pitch, yaw)


def decode_telemetry_record(data):
    # Data should always have 2 keys
    name, data = data.split('/')
    return name, data


def encode_telemetry_record(name, value):
    return '%s/%s' % (name, value)
