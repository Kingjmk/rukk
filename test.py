import tests


tests_functions = [
    tests.pid.test_idle,
    tests.pid.test_rotation,
    tests.pid.test_roll,
    tests.pid.test_pitch,
    tests.pid.test_roll_and_pitch,
    tests.pid.test_roll_and_pitch_offset_angle,
    tests.pid.test_roll_and_pitch_normalized_offset,
]

for func in tests_functions:
    print(f'\nfunction "{func.__name__}" TEST\n')
    func()
    print('======')
