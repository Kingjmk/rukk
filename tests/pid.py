import math
from simple_pid import PID


def get_pid_response(target: list, current: list, proportional_gain: float = 20.0):
    TARGET_ROLL_ANGLE, TARGET_PITCH_ANGLE, TARGET_YAW_ANGLE = target
    x_angle, y_angle, z_angle = current

    KR = [proportional_gain, 0, 0]
    KP = [proportional_gain, 0, 0]

    pid_r = PID(Kp=KR[0], Ki=KR[1], Kd=KR[2], setpoint=TARGET_ROLL_ANGLE)
    pid_p = PID(Kp=KP[0], Ki=KP[1], Kd=KP[2], setpoint=TARGET_PITCH_ANGLE)

    rotation_angle = math.radians(-45)
    rotation_vector = [
        math.cos(rotation_angle) * math.radians(x_angle) - math.sin(rotation_angle) * math.radians(y_angle),
        math.sin(rotation_angle) * math.radians(x_angle) + math.cos(rotation_angle) * math.radians(y_angle),
        z_angle,
    ]

    # Convert rad to deg
    rotation_vector[0] = math.degrees(rotation_vector[0])
    rotation_vector[1] = math.degrees(rotation_vector[1])

    response_r = 1 * pid_r(TARGET_ROLL_ANGLE - rotation_vector[0])
    response_p = 1 * pid_p(TARGET_PITCH_ANGLE - rotation_vector[1])

    return response_r, response_p


def test_idle():
    """
    Test PID when idling
    """
    print('IDLE TEST')
    target = [0, 0, 0]
    current = [0, 0, 0]

    print(get_pid_response(target, current))
    print('FINISHED\n')


def test_roll():
    """
    Test PID when roll changes
    """
    print('ROLL TEST')
    target = [0, 0, 0]
    current = [-5, 0, 0]

    print(get_pid_response(target, current))
    print('FINISHED\n')


def test_pitch():
    """
    Test PID when pitch changes
    """
    print('PITCH TEST')
    target = [0, 0, 0]
    current = [0, 5, 0]

    print(get_pid_response(target, current))
    print('FINISHED\n')


def test_roll_and_pitch():
    """
    Test PID when pitch and roll changes
    """
    print('ROLL AND PITCH TEST')
    target = [0, 0, 0]

    print(get_pid_response(target, [15, 15, 0]))
    print(get_pid_response(target, [10, 10, 0]))
    print(get_pid_response(target, [5, 5, 0]))
    print('FINISHED\n')


test_idle()
test_roll()
test_pitch()
test_roll_and_pitch()
