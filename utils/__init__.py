def clamp(v, minn, maxn):
    return max(min(maxn, v), minn)


def decode_control(data):
    # Data should always have 4 keys
    throttle, roll, pitch, yaw = data.split(',')
    return float(throttle), int(roll), int(pitch), int(yaw)


def encode_control(throttle, roll, pitch, yaw):
    return '%d,%d,%d,%d' % (throttle, roll, pitch, yaw)
