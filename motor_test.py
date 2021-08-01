# This program will let you test your ESC and brushless motor.
# Make sure your battery is not connected if you are going to calibrate it at first.
# Since you are testing your motor, I hope you don't have your propeller attached to it otherwise you are in trouble my friend...?
# This program is made by AGT @instructable.com. DO NOT REPUBLISH THIS PROGRAM... actually the program itself is harmful                                             pssst Its not, its safe.


import os  # importing os library so as to communicate with the system
import time  # importing time library to make Rpi wait because its too impatient

os.system("sudo pigpiod")  # Launching GPIO library
time.sleep(3)  # As i said it is too impatient and so if this delay is removed you will get an error
import pigpio  # importing GPIO library

ESC = 4  # Connect the ESC in this GPIO pin
ESC1 = 6
ESC2 = 17
ESC3 = 27

CAL0 = 0
CAL1 = 0
CAL2 = 0
CAL3 = 0

pi = pigpio.pi()
pi.set_servo_pulsewidth(ESC, 0)

max_value = 2000  # change this if your ESC's max value is different or leave it be
min_value = 700  # change this if your ESC's min value is different or leave it be
print("For first time launch, select calibrate")
print("Type the exact word for the function you want")
print("calibrate OR manual OR control OR arm OR stop")


def manual_drive():  # You will use this function to program your ESC if required
    print("You have selected manual option so give a value between 0 and you max value")
    while True:
        inp = input()
        if inp == "stop":
            stop()
            break
        elif inp == "control":
            control()
            break
        elif inp == "arm":
            arm()
            break
        else:
            pi.set_servo_pulsewidth(ESC, inp + CAL0)
            pi.set_servo_pulsewidth(ESC1, inp + CAL1)
            pi.set_servo_pulsewidth(ESC2, inp + CAL2)
            pi.set_servo_pulsewidth(ESC3, inp + CAL3)


def calibrate():  # This is the auto calibration procedure of a normal ESC
    pi.set_servo_pulsewidth(ESC, 0)
    print("Disconnect the battery and press Enter")
    inp = input()
    if inp == '':
        pi.set_servo_pulsewidth(ESC, max_value)
        pi.set_servo_pulsewidth(ESC1, max_value)
        pi.set_servo_pulsewidth(ESC2, max_value)
        pi.set_servo_pulsewidth(ESC3, max_value)

        print(
            "Connect the battery NOW.. you will here two beeps, then wait for a gradual falling tone then press Enter")
        inp = input()
        if inp == '':
            pi.set_servo_pulsewidth(ESC, min_value)
            pi.set_servo_pulsewidth(ESC1, min_value)
            pi.set_servo_pulsewidth(ESC2, min_value)
            pi.set_servo_pulsewidth(ESC3, min_value)

            print("Wierd eh! Special tone")
            time.sleep(7)
            print("Wait for it ....")
            time.sleep(5)
            print("Im working on it, DONT WORRY JUST WAIT.....")
            pi.set_servo_pulsewidth(ESC, 0)
            pi.set_servo_pulsewidth(ESC1, 0)
            pi.set_servo_pulsewidth(ESC2, 0)
            pi.set_servo_pulsewidth(ESC3, 0)

            time.sleep(2)
            print("Arming ESC now...")
            pi.set_servo_pulsewidth(ESC, min_value)
            pi.set_servo_pulsewidth(ESC1, min_value)
            pi.set_servo_pulsewidth(ESC2, min_value)
            pi.set_servo_pulsewidth(ESC3, min_value)

            time.sleep(1)
            print("See.... uhhhhh")
            control()  # You can change this to any other function you want


def control(cal0=CAL0, cal1=CAL1, cal2=CAL2, cal3=CAL3):
    print("I'm Starting the motor, I hope its calibrated and armed, if not restart by giving 'x'")
    print("CAL0 - %d:" % cal0, " CAL1 - %d:" % cal1, " CAL2 - %d:" % cal2, " CAL3 - %d:" % cal3)
    time.sleep(1)
    speed = 800  # change your speed if you want to.... it should be between 700 - 2000
    print(
        "Controls - a to decrease speed & d to increase speed OR q to decrease a lot of speed & e to increase a lot of speed")
    while True:
        pi.set_servo_pulsewidth(ESC, speed + cal0)
        pi.set_servo_pulsewidth(ESC1, speed + cal1)
        pi.set_servo_pulsewidth(ESC2, speed + cal2)
        pi.set_servo_pulsewidth(ESC3, speed + cal3)
        inp = input()

        if inp == "q":
            speed -= 100  # decrementing the speed like hell
            print("speed = %d" % speed)
        elif inp == "e":
            speed += 100  # incrementing the speed like hell
            print("speed = %d" % speed)
        elif inp == "d":
            speed += 10  # incrementing the speed
            print("speed = %d" % speed)
        elif inp == "a":
            speed -= 10  # decrementing the speed
            print("speed = %d" % speed)
        elif inp == "stop":
            stop()  # going for the stop function
            break
        elif inp == "manual":
            manual_drive()
            break
        elif inp == "arm":
            arm()
            break
        else:
            print("WHAT DID I SAY!! Press a,q,d or e")


def man_cal():
    print("Manual Caliberation: StRTING Speed ? 1000")
    speed = 800
    CAL0 = 0
    CAL1 = 0
    CAL2 = 0
    CAL3 = 0
    while True:
        pi.set_servo_pulsewidth(ESC, speed + CAL0)
        pi.set_servo_pulsewidth(ESC2, speed + CAL2)
        pi.set_servo_pulsewidth(ESC3, speed + CAL3)
        pi.set_servo_pulsewidth(ESC1, speed + CAL1)
        inp = input()
        if inp == "a0":
            CAL0 = CAL0 + 10
        elif inp == "a1":
            CAL1 = CAL1 + 10
        elif inp == "a2":
            CAL2 = CAL2 + 10
        elif inp == "a3":
            CAL3 = CAL3 + 10
        else:
            control(cal0=CAL0, cal1=CAL1, cal2=CAL2, cal3=CAL3)
            break


def arm():  # This is the arming procedure of an ESC
    print("Connect the battery and press Enter")
    inp = input()
    if inp == '':
        pi.set_servo_pulsewidth(ESC, 0)
        pi.set_servo_pulsewidth(ESC1, 0)
        pi.set_servo_pulsewidth(ESC2, 0)
        pi.set_servo_pulsewidth(ESC3, 0)

        time.sleep(1)
        pi.set_servo_pulsewidth(ESC, max_value)
        pi.set_servo_pulsewidth(ESC1, max_value)
        pi.set_servo_pulsewidth(ESC2, max_value)
        pi.set_servo_pulsewidth(ESC3, max_value)

        time.sleep(1)
        pi.set_servo_pulsewidth(ESC, min_value)
        pi.set_servo_pulsewidth(ESC1, min_value)
        pi.set_servo_pulsewidth(ESC2, min_value)
        pi.set_servo_pulsewidth(ESC3, min_value)

        time.sleep(1)
        control()


def stop():  # This will stop every action your Pi is performing for ESC ofcourse.
    pi.set_servo_pulsewidth(ESC, 0)
    pi.set_servo_pulsewidth(ESC1, 0)
    pi.set_servo_pulsewidth(ESC2, 0)
    pi.set_servo_pulsewidth(ESC3, 0)

    pi.stop()


# This is the start of the program actually, to start the function it needs to be initialized before calling... stupid python.
inp = input()
if inp == "manual":
    manual_drive()
elif inp == "calibrate":
    calibrate()
elif inp == "man_cal":
    man_cal()
elif inp == "arm":
    arm()
elif inp == "control":
    control()
elif inp == "stop":
    stop()
else:
    print("Thank You for not following the things I'm saying... now you gotta restart the program STUPID!!")
