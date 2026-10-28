# ---------------------------------------------------------------------------
#  Stark Industries - VEX EXP Clawbot          (version v9 - spin, drive, grab, lift)
#
#  Latest version of this code (open, Cmd/Ctrl+A, copy, paste into VEXcode):
#  https://raw.githubusercontent.com/dariolotfi/Stark-Industires/claude/eager-pascal-rhmqxo/src/main.py
#
#  30-second autonomous, in this order:
#    0. open the claw (so it can close around the object later)
#    1. spin in a circle until the optical sensor detects BLUE
#    2. stop the motors immediately
#    3. drive forward until the blue object is within 2 inches,
#       or until blue can't be detected anymore
#    4. close the claw
#    5. lift the claw arm
#  Everything stops at 30 seconds no matter what.
#
#  HOW TO USE (VEXcode EXP, Python):
#    1. Make a new Python project. Press Ctrl/Cmd+A then Delete so the
#       editor is completely empty.
#    2. Paste ALL of this file in, starting at line 1.
#    3. Ports are already set for our robot: optical 1, claw 2, claw arm 5,
#       left drive 6, right drive 10. Change them in CONFIGURATION if you
#       ever move a cable.
#    4. Start the robot with the arm DOWN and the claw CLOSED.
#    The brain screen starts with "[v9]" - if it doesn't, you're running
#    an old version of the code.
#
#  TUNING (the brain screen shows hue, brightness and "BLUE: YES/no"):
#    - SENSOR_TEST_MODE = True -> robot does not move, screen shows what the
#      sensor sees. Hold the blue object in front of it. Set back to False.
#    - BLUE_HUE_MIN / BLUE_HUE_MAX -> the hue range counted as blue.
#    - NEAR_BRIGHTNESS -> to make the robot stop at exactly 2 inches: in
#      sensor test mode, hold the object 2 inches away, read "Bright", and
#      put that number here. (0 = just use the sensor's "Near" signal.)
#    - ARM_LIFT_DEGREES -> how high the arm lifts.
#    - If the robot drives when it should spin (or spins when it should
#      drive), flip RIGHT_DRIVE_REVERSED.
# ---------------------------------------------------------------------------
from vex import *

# ===========================================================================
#  CONFIGURATION - change these to match YOUR robot
# ===========================================================================
# Ports on our robot. (If OPTICAL_PORT is ever wrong, the code searches
# the other ports for the optical sensor by itself.)
OPTICAL_PORT = Ports.PORT1        # optical sensor (mounted at the front, facing forward,
                                  # centered with the claw)
CLAW_PORT = Ports.PORT2           # claw (open / close) motor
ARM_PORT = Ports.PORT5            # claw arm (up / down) motor
LEFT_DRIVE_PORT = Ports.PORT6     # back-left wheel motor
RIGHT_DRIVE_PORT = Ports.PORT10   # back-right wheel motor

# Motor directions - flip if that motor turns the wrong way
LEFT_DRIVE_REVERSED = False
RIGHT_DRIVE_REVERSED = True
ARM_REVERSED = False              # flip if the arm goes DOWN when it should lift
CLAW_REVERSED = False             # flip if the claw closes when it should open

# Wheel size (only used for the "drive this far" safety limit)
WHEEL_TRAVEL_MM = 200.0           # distance the wheel rolls in one full turn

# Sensor test mode: set to True, download, and the robot will NOT move. The
# screen just shows what the optical sensor reads. Set back to False after.
SENSOR_TEST_MODE = False

# Timing
AUTON_TIME_LIMIT_S = 30.0         # the autonomous can never run longer than this

# Blue detection. Hue is a color wheel from 0-360:
#   red ~0, yellow ~60, green ~120, cyan ~180, BLUE ~200-250, purple ~280
BLUE_HUE_MIN = 165
BLUE_HUE_MAX = 275
MIN_BRIGHTNESS = 1                # below this the sensor is seeing nothing at all
CONFIRM_READINGS = 2              # readings in a row needed to trust "blue"

# Step 1 - spinning
SPIN_RIGHT = True                 # True = spin clockwise, False = counter-clockwise
SPIN_SPEED = 15                   # percent - slower = stops closer to the blue object
SWING_BACK_MS = 500               # if it slides past the blue while stopping, swing back
                                  # slowly for up to this long to find it again

# Step 3 - driving forward
DRIVE_SPEED = 15                  # percent
NEAR_BRIGHTNESS = 0               # 0 = stop when the sensor says "Near" (about 1-2 inches).
                                  # Set to the brightness at exactly 2 inches to stop there.
LOST_READINGS = 10                # readings in a row without blue = "can't detect" (10 = 0.1 s)
MAX_DRIVE_MM = 1000               # safety: never drive further than this
STRAIGHT_FIX = 0.5                # keeps the robot driving straight

# Steps 4 and 5 - claw and arm
CLAW_OPEN_DEGREES = 90            # how far the claw motor turns to open
CLAW_SPEED = 50                   # percent
CLAW_GRIP_TORQUE = 50             # percent torque used to squeeze the object
ARM_LIFT_DEGREES = 300            # how far the arm motor turns to lift
ARM_SPEED = 50                    # percent

VERSION = "v9"


# ===========================================================================
#  DEVICES
#  Motors are created with just a port; the *_REVERSED settings are handled
#  in the code below so they work the same on every VEXcode version.
# ===========================================================================
brain = Brain()
left_drive = Motor(LEFT_DRIVE_PORT)
right_drive = Motor(RIGHT_DRIVE_PORT)
arm = Motor(ARM_PORT)
claw = Motor(CLAW_PORT)


def port_number(port):
    """Turn Ports.PORT5 into 5 (for showing on the screen)."""
    for n in range(1, 13):
        if getattr(Ports, "PORT%d" % n, None) == port:
            return n
    return 0


def is_plugged_in(sensor):
    """True/False if VEXcode can tell, None if this version can't check."""
    try:
        return sensor.installed()
    except AttributeError:
        return None


def find_optical():
    """Use the optical sensor on OPTICAL_PORT. If nothing is plugged in
    there, look on every other port for it, so a wrong OPTICAL_PORT
    setting can't stop the sensor from working.
    Returns (sensor, port number, found?)."""
    wait(200, MSEC)   # give the brain a moment to see every device
    sensor = Optical(OPTICAL_PORT)
    if is_plugged_in(sensor) is not False:
        return sensor, port_number(OPTICAL_PORT), True
    motor_ports = (LEFT_DRIVE_PORT, RIGHT_DRIVE_PORT, ARM_PORT, CLAW_PORT)
    for n in range(1, 13):
        port = getattr(Ports, "PORT%d" % n, None)
        if port is None or port == OPTICAL_PORT or port in motor_ports:
            continue
        candidate = Optical(port)
        if is_plugged_in(candidate):
            return candidate, n, True
    # Not found anywhere - still use OPTICAL_PORT and try anyway
    return sensor, port_number(OPTICAL_PORT), False


optical, optical_port, optical_found = find_optical()


# ===========================================================================
#  HELPERS
# ===========================================================================
def time_left():
    return AUTON_TIME_LIMIT_S - brain.timer.time(SECONDS)


def out_of_time():
    return time_left() <= 0


def now_ms():
    return brain.timer.time(MSEC)


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


def move_motor_to(motor, reversed_, degrees):
    """Turn the claw or arm motor to a position, giving up after 2 s."""
    motor.spin_to_position(-degrees if reversed_ else degrees, DEGREES, wait=False)
    start = now_ms()
    while not out_of_time() and not motor.is_done() and now_ms() - start < 2000:
        wait(10, MSEC)
    motor.stop()


def sees_blue():
    """One reading: is the sensor looking at something blue?"""
    if optical.brightness() < MIN_BRIGHTNESS:
        return False
    hue = optical.hue()
    if BLUE_HUE_MIN <= hue <= BLUE_HUE_MAX:
        return True
    # also trust the sensor's own color guess
    return optical.color() == Color.BLUE


def sees_blue_confirmed():
    """Several readings in a row must agree before we believe it's blue."""
    for _ in range(CONFIRM_READINGS):
        if not sees_blue():
            return False
        wait(10, MSEC)
    return True


def within_2_inches():
    if NEAR_BRIGHTNESS > 0 and optical.brightness() >= NEAR_BRIGHTNESS:
        return True
    return optical.is_near_object()


def status(line):
    brain.screen.clear_screen()
    brain.screen.set_cursor(1, 1)
    brain.screen.print("[%s] %s" % (VERSION, line))
    brain.screen.next_row()
    brain.screen.print("%.1fs left  port %d" % (max(0, time_left()), optical_port))
    brain.screen.next_row()
    brain.screen.print("Hue %d Bright %d" % (int(optical.hue()), int(optical.brightness())))
    brain.screen.next_row()
    brain.screen.print("BLUE: %s" % ("YES" if sees_blue() else "no"))


last_screen_update = [0]


def show_live(line):
    """Refresh the screen a few times a second (more often would slow the robot)."""
    if now_ms() - last_screen_update[0] >= 250:
        last_screen_update[0] = now_ms()
        status(line)


def mm_to_wheel_degrees(mm):
    return mm / WHEEL_TRAVEL_MM * 360.0


def stop_drive():
    left_drive.stop()
    right_drive.stop()


def spin(speed):
    """Spin in place. Positive = clockwise."""
    run_motor(left_drive, LEFT_DRIVE_REVERSED, speed)
    run_motor(right_drive, RIGHT_DRIVE_REVERSED, -speed)


class StraightDrive:
    """Drives both wheels forward at the same speed. If one wheel gets
    ahead of the other, it slows that wheel a little so the robot keeps
    going straight instead of curving."""

    def __init__(self):
        self.left_start = motor_position(left_drive, LEFT_DRIVE_REVERSED)
        self.right_start = motor_position(right_drive, RIGHT_DRIVE_REVERSED)

    def progress(self):
        left = motor_position(left_drive, LEFT_DRIVE_REVERSED) - self.left_start
        right = motor_position(right_drive, RIGHT_DRIVE_REVERSED) - self.right_start
        return left, right

    def distance(self):
        """How far we've driven since starting, in wheel degrees."""
        left, right = self.progress()
        return (left + right) / 2.0

    def go(self, speed):
        left, right = self.progress()
        fix = max(-speed / 2.0, min(speed / 2.0, (left - right) * STRAIGHT_FIX))
        run_motor(left_drive, LEFT_DRIVE_REVERSED, speed - fix)
        run_motor(right_drive, RIGHT_DRIVE_REVERSED, speed + fix)


def stop_everything():
    stop_drive()
    arm.stop()
    claw.stop()


def watchdog():
    """Runs in the background: stops EVERYTHING the moment 30 s are up,
    even if the robot is in the middle of a move."""
    while not out_of_time():
        wait(20, MSEC)
    stop_everything()
    status("Time's up!")


# ===========================================================================
#  AUTONOMOUS STEPS
# ===========================================================================
def setup():
    brain.timer.clear()

    # HOLD = the wheels lock in place the instant they're told to stop
    left_drive.set_stopping(HOLD)
    right_drive.set_stopping(HOLD)
    arm.set_stopping(HOLD)
    claw.set_stopping(HOLD)
    arm.set_velocity(ARM_SPEED, PERCENT)
    claw.set_velocity(CLAW_SPEED, PERCENT)

    # The robot should START with the arm down and the claw closed.
    arm.set_position(0, DEGREES)
    claw.set_position(0, DEGREES)
    arm.stop()   # hold the arm down where it is

    # Turn on the sensor's light so colors read the same in any room lighting
    optical.set_light(LedStateType.ON)
    optical.set_light_power(100, PERCENT)
    wait(200, MSEC)


def open_claw():
    status("Opening claw")
    claw.set_max_torque(100, PERCENT)
    move_motor_to(claw, CLAW_REVERSED, CLAW_OPEN_DEGREES)


def spin_until_blue():
    """Step 1 + 2: spin in a circle until blue is detected, then stop the
    motors immediately. Returns True once the robot is stopped facing blue."""
    direction = 1 if SPIN_RIGHT else -1
    while not out_of_time():
        spin(SPIN_SPEED * direction)
        if sees_blue():
            stop_drive()                     # stop the motors immediately
            wait(50, MSEC)
            if sees_blue_confirmed():
                return True
            # Slid a little past it while stopping - swing back slowly
            start = now_ms()
            spin(-SPIN_SPEED / 2.0 * direction)
            while not out_of_time() and now_ms() - start < SWING_BACK_MS:
                if sees_blue():
                    stop_drive()
                    if sees_blue_confirmed():
                        return True
                    spin(-SPIN_SPEED / 2.0 * direction)
                wait(10, MSEC)
            stop_drive()
            # just a flicker - keep spinning
        show_live("Spinning - looking")
        wait(10, MSEC)
    stop_drive()
    return False


def drive_to_blue():
    """Step 3: drive forward until the blue object is within 2 inches, or
    until blue can't be detected anymore. Then stop."""
    status("Driving to blue")
    robot = StraightDrive()
    limit = mm_to_wheel_degrees(MAX_DRIVE_MM)
    lost = 0
    while not out_of_time():
        if within_2_inches():
            break
        if sees_blue():
            lost = 0
        else:
            lost += 1
            if lost >= LOST_READINGS:
                break                        # blue can't be detected anymore
        if robot.distance() > limit:
            break
        robot.go(DRIVE_SPEED)
        show_live("Driving to blue")
        wait(10, MSEC)
    stop_drive()


def close_claw():
    """Step 4: close the claw until it squeezes the object."""
    status("Closing claw")
    claw.set_max_torque(CLAW_GRIP_TORQUE, PERCENT)
    run_motor(claw, CLAW_REVERSED, -CLAW_SPEED)
    start = now_ms()
    wait(300, MSEC)
    while not out_of_time() and abs(claw.velocity(PERCENT)) > 2:
        if now_ms() - start > 2000:
            break
        wait(20, MSEC)
    claw.stop()   # HOLD keeps squeezing the object


def lift_arm():
    """Step 5: lift the claw arm."""
    status("Lifting arm")
    arm.set_max_torque(100, PERCENT)
    move_motor_to(arm, ARM_REVERSED, ARM_LIFT_DEGREES)


# ===========================================================================
#  AUTONOMOUS (30 seconds max)
# ===========================================================================
def autonomous():
    setup()
    if not optical_found:
        # Don't give up - just warn on the screen and keep going
        status("No optical found!")
        wait(500, MSEC)
    Thread(watchdog)

    open_claw()                     # 0. open the claw

    if spin_until_blue():           # 1. spin until blue  2. stop immediately
        drive_to_blue()             # 3. drive until within 2 in / blue lost
        if not out_of_time():
            close_claw()            # 4. close the claw
        if not out_of_time():
            lift_arm()              # 5. lift the arm
        status("Done!")
    else:
        status("No blue found")

    stop_drive()
    # Keep holding the object up until the 30 seconds are over
    while not out_of_time():
        wait(20, MSEC)
    stop_everything()


def sensor_test():
    """Robot does not move - just shows what the optical sensor sees."""
    optical.set_light(LedStateType.ON)
    optical.set_light_power(100, PERCENT)
    while True:
        brain.screen.clear_screen()
        brain.screen.set_cursor(1, 1)
        brain.screen.print("[%s] SENSOR TEST - no driving" % VERSION)
        brain.screen.next_row()
        brain.screen.print("Optical port %d %s" % (optical_port, "" if optical_found else "NOT FOUND"))
        brain.screen.next_row()
        brain.screen.print("Hue %d Bright %d" % (int(optical.hue()), int(optical.brightness())))
        brain.screen.next_row()
        brain.screen.print("Near: %s" % ("YES" if optical.is_near_object() else "no"))
        brain.screen.next_row()
        brain.screen.print("BLUE: %s" % ("YES" if sees_blue() else "no"))
        wait(200, MSEC)


# ===========================================================================
#  START - runs as soon as the program starts
# ===========================================================================
if SENSOR_TEST_MODE:
    sensor_test()
else:
    autonomous()
