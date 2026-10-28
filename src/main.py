# ---------------------------------------------------------------------------
#  Stark Industries - VEX EXP Clawbot          (version v8 - no spinning)
#
#  Latest version of this code (open, Cmd/Ctrl+A, copy, paste into VEXcode):
#  https://raw.githubusercontent.com/dariolotfi/Stark-Industires/claude/eager-pascal-rhmqxo/src/main.py
#
#  30-second autonomous - the robot NEVER turns or spins:
#    1. open the claw
#    2. drive slowly STRAIGHT forward, watching the optical sensor
#    3. the moment it sees BLUE, stop
#    4. creep straight forward until the object is right at the claw, stop
#    5. close the claw and stop
#  Everything stops at 30 seconds no matter what.
#
#  HOW TO USE (VEXcode EXP, Python):
#    1. Make a new Python project. Press Ctrl/Cmd+A then Delete so the
#       editor is completely empty.
#    2. Paste ALL of this file in, starting at line 1.
#    3. Change the ports in CONFIGURATION below to match your robot.
#       (If the optical sensor isn't on OPTICAL_PORT, the code finds it on
#       any other port by itself - the screen shows which port it's using.)
#    4. Start the robot with the arm DOWN and the claw CLOSED,
#       pointed straight at the blue object.
#    The brain screen starts with "[v8]" - if it doesn't, you're running
#    an old version of the code.
#
#  TUNING (the brain screen shows hue, brightness and "BLUE: YES/no"):
#    - SENSOR_TEST_MODE = True -> robot does not move, screen shows what the
#      sensor sees. Hold the blue object in front of it. Set back to False.
#    - BLUE_HUE_MIN / BLUE_HUE_MAX -> the hue range counted as blue.
#    - If the robot stops at an object and the screen says "NOT BLUE",
#      it shows that object's hue - widen BLUE_HUE_MIN/MAX to include it.
#    - EXTRA_DRIVE_MM -> raise it if the robot stops before the object is
#      between the claw fingers.
#    - If the robot spins in place instead of driving straight, flip
#      RIGHT_DRIVE_REVERSED (or LEFT_DRIVE_REVERSED).
# ---------------------------------------------------------------------------
from vex import *

# ===========================================================================
#  CONFIGURATION - change these to match YOUR robot
# ===========================================================================
# Ports - CHECK THESE. (If OPTICAL_PORT is wrong, the code searches the
# other ports for the optical sensor by itself.)
LEFT_DRIVE_PORT = Ports.PORT6     # back-left wheel motor
RIGHT_DRIVE_PORT = Ports.PORT10   # back-right wheel motor
ARM_PORT = Ports.PORT3            # arm (up / down) motor
CLAW_PORT = Ports.PORT4           # claw (open / close) motor
OPTICAL_PORT = Ports.PORT2        # optical sensor (mounted at the front, facing forward,
                                  # centered with the claw)

# Motor directions - if the robot spins when it should drive straight,
# flip RIGHT_DRIVE_REVERSED. If it drives backwards, flip both.
LEFT_DRIVE_REVERSED = False
RIGHT_DRIVE_REVERSED = True
CLAW_REVERSED = False

# Wheel size (only used for the "drive this far" distances)
WHEEL_TRAVEL_MM = 200.0           # distance the wheel rolls in one full turn

# Sensor test mode: set to True, download, and the robot will NOT move. The
# screen just shows what the optical sensor reads. Hold your blue object in
# front of it to check the hue, then set back to False.
SENSOR_TEST_MODE = False

# Timing
AUTON_TIME_LIMIT_S = 30.0         # the autonomous can never run longer than this

# Blue detection. Hue is a color wheel from 0-360:
#   red ~0, yellow ~60, green ~120, cyan ~180, BLUE ~200-250, purple ~280
# This range is wide so that light blue, dark blue and blue-purple all count.
BLUE_HUE_MIN = 165
BLUE_HUE_MAX = 275
MIN_BRIGHTNESS = 1                # below this the sensor is seeing nothing at all
CONFIRM_READINGS = 3              # readings in a row needed to trust "blue"

# Driving (straight only - the robot never turns)
SEARCH_SPEED = 20                 # percent - slow drive forward while looking for blue
APPROACH_SPEED = 10               # percent - creep speed once blue is seen
STRAIGHT_FIX = 0.5                # how hard to correct if one wheel gets ahead (keeps it straight)
MAX_SEARCH_MM = 1500              # stop if no blue has been seen after driving this far
MAX_APPROACH_MM = 400             # stop if the object isn't reached after this far
EXTRA_DRIVE_MM = 0                # drive this much further AFTER the sensor says the object is
                                  # close. Raise it if the robot stops before the object is
                                  # between the claw fingers; keep 0 if it is already inside.

# Claw
CLAW_OPEN_DEGREES = 90            # how far the claw motor turns to open
CLAW_SPEED = 50                   # percent
CLAW_GRIP_TORQUE = 50             # percent torque used to squeeze the object

VERSION = "v8"


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


def left_pos():
    return motor_position(left_drive, LEFT_DRIVE_REVERSED)


def right_pos():
    return motor_position(right_drive, RIGHT_DRIVE_REVERSED)


def stop_drive():
    left_drive.stop()
    right_drive.stop()


class StraightDrive:
    """Drives both wheels forward at the same speed. If one wheel gets
    ahead of the other, it slows that wheel a little so the robot keeps
    going straight instead of curving."""

    def __init__(self):
        self.left_start = left_pos()
        self.right_start = right_pos()

    def distance(self):
        """How far we've driven since starting, in wheel degrees."""
        return ((left_pos() - self.left_start) + (right_pos() - self.right_start)) / 2.0

    def go(self, speed):
        ahead = (left_pos() - self.left_start) - (right_pos() - self.right_start)
        fix = max(-speed / 2.0, min(speed / 2.0, ahead * STRAIGHT_FIX))
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

    left_drive.set_stopping(BRAKE)
    right_drive.set_stopping(BRAKE)
    arm.set_stopping(HOLD)
    claw.set_stopping(HOLD)
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
    target = -CLAW_OPEN_DEGREES if CLAW_REVERSED else CLAW_OPEN_DEGREES
    claw.spin_to_position(target, DEGREES, wait=False)
    start = now_ms()
    while not out_of_time() and not claw.is_done() and now_ms() - start < 2000:
        wait(10, MSEC)
    claw.stop()


def drive_until_blue():
    """Drive slowly straight forward until the sensor sees blue, then stop
    right away. Returns:
      "blue"     - saw blue
      "not blue" - bumped right up to something that isn't blue
      "nothing"  - drove MAX_SEARCH_MM (or ran out of time) without seeing blue"""
    status("Driving - looking")
    robot = StraightDrive()
    limit = mm_to_wheel_degrees(MAX_SEARCH_MM)
    near_not_blue = 0
    while not out_of_time():
        if sees_blue():
            stop_drive()
            if sees_blue_confirmed():
                return "blue"
        # something is right in front but it isn't blue - don't push it
        if optical.is_near_object() and not sees_blue():
            near_not_blue += 1
            if near_not_blue >= CONFIRM_READINGS:
                stop_drive()
                return "not blue"
        else:
            near_not_blue = 0
        if robot.distance() > limit:
            break
        robot.go(SEARCH_SPEED)
        show_live("Driving - looking")
        wait(10, MSEC)
    stop_drive()
    return "nothing"


def creep_to_object():
    """Blue was seen - creep straight forward until the object is right in
    front of the claw, then stop."""
    status("Blue! Moving in")
    wait(200, MSEC)
    robot = StraightDrive()
    limit = mm_to_wheel_degrees(MAX_APPROACH_MM)
    while not out_of_time():
        if optical.is_near_object():
            break
        if robot.distance() > limit:
            break
        robot.go(APPROACH_SPEED)
        show_live("Blue! Moving in")
        wait(10, MSEC)
    stop_drive()

    if EXTRA_DRIVE_MM > 0 and not out_of_time():
        robot = StraightDrive()
        target = mm_to_wheel_degrees(EXTRA_DRIVE_MM)
        while not out_of_time() and robot.distance() < target:
            robot.go(APPROACH_SPEED)
            wait(10, MSEC)
        stop_drive()


def close_claw():
    status("Closing claw")
    claw.set_max_torque(CLAW_GRIP_TORQUE, PERCENT)
    # Close until the claw squeezes the object (the motor stalls)
    run_motor(claw, CLAW_REVERSED, -CLAW_SPEED)
    start = now_ms()
    wait(300, MSEC)
    while not out_of_time() and abs(claw.velocity(PERCENT)) > 2:
        if now_ms() - start > 2000:
            break
        wait(20, MSEC)
    claw.stop()   # HOLD keeps squeezing the object


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

    # 1) start with the claw open
    open_claw()

    # 2) + 3) drive straight until blue is seen, then stop
    result = drive_until_blue()

    if result == "blue":
        # 4) creep straight in until it's at the claw, stop
        creep_to_object()
        # 5) close the claw
        if not out_of_time():
            close_claw()
        stop_drive()
        status("Got it!")
    elif result == "not blue":
        hue = int(optical.hue())
        stop_drive()
        brain.screen.clear_screen()
        brain.screen.set_cursor(1, 1)
        brain.screen.print("[%s] Object NOT BLUE" % VERSION)
        brain.screen.next_row()
        brain.screen.print("Its hue: %d" % hue)
        brain.screen.next_row()
        brain.screen.print("Blue range: %d-%d" % (BLUE_HUE_MIN, BLUE_HUE_MAX))
    else:
        status("No blue found")

    stop_drive()
    # Keep holding the claw shut until the 30 seconds are over
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
