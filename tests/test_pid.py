from utils.pid import PID
from utils.helpers import rotate_on_z

VECTOR_ZERO = [0, 0, 0]


def get_pid_response(target: list, current: list, proportional_gain: float = 20.0):
    target = rotate_on_z(target, -45)
    TARGET_ROLL_ANGLE, TARGET_PITCH_ANGLE, TARGET_YAW_ANGLE = target

    KR = [proportional_gain, 0, 0]
    KP = [proportional_gain, 0, 0]

    pid_r = PID(Kp=KR[0], Ki=KR[1], Kd=KR[2], setpoint=TARGET_ROLL_ANGLE)
    pid_p = PID(Kp=KP[0], Ki=KP[1], Kd=KP[2], setpoint=TARGET_PITCH_ANGLE)

    rotation_vector = rotate_on_z(current, -45)

    response_r = 1 * pid_r(rotation_vector[0])
    response_p = 1 * pid_p(rotation_vector[1])
    return round(response_r, 2), round(response_p, 2)


def test_rotation():
    """
    Test PID when idling
    """
    print(VECTOR_ZERO, rotate_on_z(VECTOR_ZERO, -45))
    print([10, 10, 0], rotate_on_z([10, 10, 0], -45))
    print([0, 10, 0], rotate_on_z([0, 10, 0], -45))
    print([10, 0, 0], rotate_on_z([10, 0, 0], -45))


def test_idle():
    """
    Test PID when idling
    """

    print(VECTOR_ZERO, VECTOR_ZERO, get_pid_response(VECTOR_ZERO, VECTOR_ZERO))


def test_roll():
    """
    Test PID when roll changes
    """
    print(VECTOR_ZERO, [5, 0, 0], get_pid_response(VECTOR_ZERO, [5, 0, 0]))
    print(VECTOR_ZERO, [-5, 0, 0], get_pid_response(VECTOR_ZERO, [-5, 0, 0]))


def test_pitch():
    """
    Test PID when pitch changes
    """

    print(VECTOR_ZERO, [0, 5, 0], get_pid_response(VECTOR_ZERO, [0, 5, 0]))
    print(VECTOR_ZERO, [0, -5, 0], get_pid_response(VECTOR_ZERO, [0, -5, 0]))


def test_roll_and_pitch():
    """
    Test PID when pitch and roll changes
    """
    print(VECTOR_ZERO, [15, 15, 0], get_pid_response(VECTOR_ZERO, [15, 15, 0]))
    print(VECTOR_ZERO, [10, 10, 0], get_pid_response(VECTOR_ZERO, [10, 10, 0]))
    print(VECTOR_ZERO, [5, 5, 0], get_pid_response(VECTOR_ZERO, [5, 5, 0]))

    print(VECTOR_ZERO, [-15, -15, 0], get_pid_response(VECTOR_ZERO, [-15, -15, 0]))
    print(VECTOR_ZERO, [-10, -10, 0], get_pid_response(VECTOR_ZERO, [-10, -10, 0]))
    print(VECTOR_ZERO, [-5, -5, 0], get_pid_response(VECTOR_ZERO, [-5, -5, 0]))


def test_roll_and_pitch_offset_angle():
    """
    Test PID when pitch and roll changes
    """
    target = [15, 15, 0]

    print(target, VECTOR_ZERO, get_pid_response(target, VECTOR_ZERO))
    print(target, [5, 10, 0], get_pid_response(target, [5, 10, 0]))
    print(target, [10, 5, 0], get_pid_response(target, [10, 5, 0]))

    print(target, [-5, -10, 0], get_pid_response(target, [-5, -10, 0]))
    print(target, [-10, -5, 0], get_pid_response(target, [-10, -5, 0]))


def test_roll_and_pitch_normalized_offset():
    """
    Test if difference between angles and angles themselves changes result
    """
    print(VECTOR_ZERO, [5, 5, 0], get_pid_response(VECTOR_ZERO, [5, 5, 0]))
    print([5, 5, 0], [10, 10, 0], get_pid_response([5, 5, 0], [10, 10, 0]))
    print([10, 10, 0], [15, 15, 0], get_pid_response([10, 10, 0], [15, 15, 0]))
