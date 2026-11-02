# ---------------------------------------------------------------------------
#  Stark Industries - VEX EXP Clawbot - Autonomous   (version v13)
#
#  Latest version of this code (open, Cmd/Ctrl+A, copy, paste into VEXcode):
#  https://raw.githubusercontent.com/dariolotfi/Stark-Industires/claude/eager-pascal-rhmqxo/src/main.py
#
#  What it does:
#    1. opens the claw
#    2. drives forward for 5 seconds, then stops
#    The brain screen counts down from 30 the whole time. At 0 every motor
#    stops and the screen says "Auton over".
#
#  Start the robot with the claw CLOSED.
# ---------------------------------------------------------------------------
from vex import *

# ----- Settings ------------------------------------------------------------
AUTON_TIME = 30          # seconds in the autonomous period (the countdown)
DRIVE_TIME = 5           # seconds to drive forward
DRIVE_SPEED = 50         # percent
CLAW_OPEN_DEGREES = 90   # how far the claw motor turns to open
CLAW_SPEED = 50          # percent

# ----- Devices (our robot's ports) -----------------------------------------
brain = Brain()
claw = Motor(Ports.PORT2)
left_motor = Motor(Ports.PORT6)
right_motor = Motor(Ports.PORT10)
# The right motor is mounted facing the other way, so it spins REVERSE to
# drive forward. If the robot spins in a circle instead of driving straight,
# change RIGHT_FORWARD to FORWARD.
LEFT_FORWARD = FORWARD
RIGHT_FORWARD = REVERSE


def time_left():
    return AUTON_TIME - brain.timer.time(SECONDS)


def show(row, text):
    brain.screen.clear_row(row)
    brain.screen.set_cursor(row, 1)
    brain.screen.print(text)


def stop_all_motors():
    left_motor.stop()
    right_motor.stop()
    claw.stop()


def countdown():
    """Runs in the background: shows the seconds left on row 2, and stops
    every motor when it reaches 0."""
    last_shown = -1
    while time_left() > 0:
        seconds = int(time_left()) + 1     # 30, 29, ... 1
        if seconds > AUTON_TIME:
            seconds = AUTON_TIME
        if seconds != last_shown:
            show(2, "Time left: %d" % seconds)
            last_shown = seconds
        wait(50, MSEC)
    show(2, "Time left: 0")
    stop_all_motors()
    show(1, "Auton over")


def open_claw():
    show(1, "Opening claw")
    claw.set_velocity(CLAW_SPEED, PERCENT)
    claw.spin_for(FORWARD, CLAW_OPEN_DEGREES, DEGREES, wait=False)
    # wait until it's open (or 2 seconds, in case the claw hits its stop)
    start = brain.timer.time(SECONDS)
    while not claw.is_done() and brain.timer.time(SECONDS) - start < 2:
        wait(10, MSEC)
    claw.stop()   # HOLD keeps the claw open


def drive_forward():
    show(1, "Driving forward")
    left_motor.spin(LEFT_FORWARD, DRIVE_SPEED, PERCENT)
    right_motor.spin(RIGHT_FORWARD, DRIVE_SPEED, PERCENT)
    start = brain.timer.time(SECONDS)
    while brain.timer.time(SECONDS) - start < DRIVE_TIME and time_left() > 0:
        wait(10, MSEC)
    left_motor.stop()
    right_motor.stop()


# ----- Autonomous ----------------------------------------------------------
left_motor.set_stopping(BRAKE)
right_motor.set_stopping(BRAKE)
claw.set_stopping(HOLD)

brain.screen.clear_screen()
brain.timer.clear()          # the 30-second countdown starts now
Thread(countdown)

open_claw()                  # 1. open the claw
drive_forward()              # 2. drive forward for 5 seconds
if time_left() > 0:
    show(1, "Done")

# keep the program running until the countdown hits 0
while time_left() > 0:
    wait(20, MSEC)
wait(200, MSEC)
