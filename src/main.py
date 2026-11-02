# ---------------------------------------------------------------------------
#  Stark Industries - VEX EXP Clawbot          (version v10 - drive 5 s)
#
#  Latest version of this code (open, Cmd/Ctrl+A, copy, paste into VEXcode):
#  https://raw.githubusercontent.com/dariolotfi/Stark-Industires/claude/eager-pascal-rhmqxo/src/main.py
#
#  Autonomous: drive straight forward for 5 seconds, then stop.
#
#  HOW TO USE (VEXcode EXP, Python):
#    1. Make a new Python project. Press Ctrl/Cmd+A then Delete so the
#       editor is completely empty.
#    2. Paste ALL of this file in, starting at line 1.
#    3. The brain screen shows "[v10]" - if it doesn't, you're running an
#       old version of the code.
#
#  If the robot spins instead of driving straight, flip RIGHT_DRIVE_REVERSED.
#  If it drives backwards, flip both LEFT_DRIVE_REVERSED and RIGHT_DRIVE_REVERSED.
# ---------------------------------------------------------------------------
from vex import *

# ===========================================================================
#  CONFIGURATION
# ===========================================================================
# Ports on our robot
LEFT_DRIVE_PORT = Ports.PORT6     # back-left wheel motor
RIGHT_DRIVE_PORT = Ports.PORT10   # back-right wheel motor

# Motor directions
LEFT_DRIVE_REVERSED = False
RIGHT_DRIVE_REVERSED = True

DRIVE_TIME_S = 5.0                # how long to drive forward
DRIVE_SPEED = 50                  # percent
STRAIGHT_FIX = 0.5                # how hard to correct if one wheel gets ahead (keeps it straight)

VERSION = "v10"


# ===========================================================================
#  DEVICES
#  Motors are created with just a port; the *_REVERSED settings are handled
#  below so they work the same on every VEXcode version.
# ===========================================================================
brain = Brain()
left_drive = Motor(LEFT_DRIVE_PORT)
right_drive = Motor(RIGHT_DRIVE_PORT)


def run_motor(motor, reversed_, speed):
    """Spin a motor at a speed in percent. Negative = backwards."""
    if reversed_:
        speed = -speed
    if speed >= 0:
        motor.spin(FORWARD, speed, PERCENT)
    else:
        motor.spin(REVERSE, -speed, PERCENT)


def motor_position(motor, reversed_):
    p = motor.position(DEGREES)
    return -p if reversed_ else p


def status(line):
    brain.screen.clear_screen()
    brain.screen.set_cursor(1, 1)
    brain.screen.print("[%s] %s" % (VERSION, line))


# ===========================================================================
#  AUTONOMOUS
# ===========================================================================
def autonomous():
    left_drive.set_stopping(BRAKE)
    right_drive.set_stopping(BRAKE)
    left_drive.set_position(0, DEGREES)
    right_drive.set_position(0, DEGREES)

    status("Driving forward")
    brain.timer.clear()
    while brain.timer.time(SECONDS) < DRIVE_TIME_S:
        # If one wheel gets ahead of the other, slow it a little so the
        # robot keeps going straight instead of curving.
        ahead = (motor_position(left_drive, LEFT_DRIVE_REVERSED)
                 - motor_position(right_drive, RIGHT_DRIVE_REVERSED))
        fix = max(-DRIVE_SPEED / 2.0, min(DRIVE_SPEED / 2.0, ahead * STRAIGHT_FIX))
        run_motor(left_drive, LEFT_DRIVE_REVERSED, DRIVE_SPEED - fix)
        run_motor(right_drive, RIGHT_DRIVE_REVERSED, DRIVE_SPEED + fix)
        wait(10, MSEC)

    left_drive.stop()
    right_drive.stop()
    status("Stopped")


autonomous()
