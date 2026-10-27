# ---------------------------------------------------------------------------
#  Stark Industries - VEX EXP Clawbot
#  30-second autonomous:
#    1. open the claw
#    2. turn left/right in small steps, stopping after each step to look,
#       UNTIL the optical sensor sees a BLUE object
#    3. stop, lock on (find both edges of the object, turn to the middle)
#    4. drive straight at it, staying locked on, and stop when it's in the claw
#    5. close the claw and stop
#  Everything stops at 30 seconds no matter what.
#
#  HOW TO USE (VEXcode EXP, Python):
#    1. Make a new Python project. Press Ctrl/Cmd+A then Delete so the
#       editor is completely empty.
#    2. Paste ALL of this file in, starting at line 1.
#    3. Change the ports in CONFIGURATION below to match your robot.
#    4. Start the robot with the arm DOWN and the claw CLOSED.
#    5. Put the blue object within about 10-20 cm in front of the robot -
#       the optical sensor can only see color up close.
#
#  TUNING (the brain screen shows hue, brightness and "BLUE: YES/no"):
#    - SENSOR_TEST_MODE = True -> robot does not move, screen shows what the
#      sensor sees. Hold the blue object in front of it. Set back to False.
#    - BLUE_HUE_MIN / BLUE_HUE_MAX -> match the hue your blue object shows.
#    - MIN_BRIGHTNESS -> lower it if the sensor won't say BLUE on your object.
#    - EXTRA_DRIVE_MM -> raise it if the robot stops before the object is
#      between the claw fingers.
#    - TURN_RIGHT_FIRST / SWEEP_HALF_ANGLE / STEP_ANGLE -> how it searches.
#    - *_REVERSED -> flip if a motor turns the wrong way.
# ---------------------------------------------------------------------------
from vex import *

# ===========================================================================
#  CONFIGURATION - change these to match YOUR robot
# ===========================================================================
# Ports - CHECK THESE. If OPTICAL_PORT is wrong the robot never sees blue.
LEFT_DRIVE_PORT = Ports.PORT6     # back-left wheel motor
RIGHT_DRIVE_PORT = Ports.PORT10   # back-right wheel motor
ARM_PORT = Ports.PORT3            # arm (up / down) motor
CLAW_PORT = Ports.PORT4           # claw (open / close) motor
OPTICAL_PORT = Ports.PORT2        # optical sensor (mounted at the front, facing forward,
                                  # centered with the claw)

# Motor directions - flip one of these if that motor turns the wrong way
LEFT_DRIVE_REVERSED = False
RIGHT_DRIVE_REVERSED = True
ARM_REVERSED = False
CLAW_REVERSED = False

# Robot geometry (EXP Clawbot defaults - measure yours for better turns)
WHEEL_TRAVEL_MM = 200.0           # distance the wheel rolls in one full turn
TRACK_WIDTH_MM = 176.0            # distance between the left and right wheels

# Sensor test mode: set to True, download, and the robot will NOT move. The
# screen just shows what the optical sensor reads. Hold your blue object in
# front of it to check BLUE_HUE_MIN/MAX and MIN_BRIGHTNESS, then set back to False.
SENSOR_TEST_MODE = False

# Timing
AUTON_TIME_LIMIT_S = 30.0         # the autonomous can never run longer than this

# Blue detection (optical sensor hue is 0-360; blue is roughly 190-250)
BLUE_HUE_MIN = 190
BLUE_HUE_MAX = 250
MIN_BRIGHTNESS = 3                # ignore dark readings (nothing in front of the sensor)
CONFIRM_READINGS = 3              # readings in a row needed to trust "blue"

# Searching - the robot turns a small step, stops, looks, and repeats
TURN_RIGHT_FIRST = True           # which way to turn first
SWEEP_HALF_ANGLE = 90             # look up to this many degrees left AND right of the start
STEP_ANGLE = 10                   # degrees per step
LOOK_PAUSE_MS = 150               # how long to stop and look after each step
SEARCH_TURN_SPEED = 15            # percent

# Locking on
LOCK_TURN_SPEED = 8               # percent - slow turn used to center on the object
LOCK_MAX_ANGLE = 40               # never turn more than this while centering
REACQUIRE_ANGLE = 20              # if blue is lost, look this far left/right to find it again

# Driving
DRIVE_SPEED = 20                  # percent - speed driving straight at the object
LOST_READINGS = 10                # readings in a row without blue before re-locking (10 = 0.1 s)
EXTRA_DRIVE_MM = 0                # drive this much further AFTER the sensor says the object is
                                  # close. Raise it if the robot stops before the object is
                                  # between the claw fingers; keep 0 if it is already inside.
EXTRA_DRIVE_SPEED = 10            # percent - speed for that extra bit
MAX_DRIVE_MM = 1500               # give up driving straight after this far

# Claw
CLAW_OPEN_DEGREES = 90            # how far the claw motor turns to open
CLAW_SPEED = 50                   # percent
CLAW_GRIP_TORQUE = 50             # percent torque used to squeeze the object
CLOSE_CLAW_AT_END = True          # close the claw on the object once the robot has stopped


# ===========================================================================
#  DEVICES
# ===========================================================================
brain = Brain()
left_drive = Motor(LEFT_DRIVE_PORT, LEFT_DRIVE_REVERSED)
right_drive = Motor(RIGHT_DRIVE_PORT, RIGHT_DRIVE_REVERSED)
arm = Motor(ARM_PORT, ARM_REVERSED)
claw = Motor(CLAW_PORT, CLAW_REVERSED)
optical = Optical(OPTICAL_PORT)


# ===========================================================================
#  HELPERS
# ===========================================================================
def time_left():
    return AUTON_TIME_LIMIT_S - brain.timer.time(SECONDS)


def out_of_time():
    return time_left() <= 0


def sees_blue():
    """One reading: is the sensor looking at something blue?"""
    if optical.brightness() < MIN_BRIGHTNESS:
        return False
    hue = optical.hue()
    return BLUE_HUE_MIN <= hue <= BLUE_HUE_MAX


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
    brain.screen.print(line)
    brain.screen.next_row()
    brain.screen.print("Time left: %.1f" % max(0, time_left()))
    brain.screen.next_row()
    # handy for tuning BLUE_HUE_MIN/MAX and MIN_BRIGHTNESS
    brain.screen.print("Hue %d Bright %d" % (int(optical.hue()), int(optical.brightness())))
    brain.screen.next_row()
    brain.screen.print("BLUE: %s" % ("YES" if sees_blue() else "no"))


last_screen_update = [0]


def show_live(line):
    """Refresh the screen a few times a second (more often would slow the robot)."""
    now = brain.timer.time(MSEC)
    if now - last_screen_update[0] >= 250:
        last_screen_update[0] = now
        status(line)


def mm_to_wheel_degrees(mm):
    return mm / WHEEL_TRAVEL_MM * 360.0


WHEEL_DEGREES_PER_ROBOT_DEGREE = mm_to_wheel_degrees(3.1416 * TRACK_WIDTH_MM / 360.0)


def stop_drive():
    left_drive.stop()
    right_drive.stop()


def drive(speed):
    """Drive straight. Positive = forward."""
    left_drive.spin(FORWARD, speed, PERCENT)
    right_drive.spin(FORWARD, speed, PERCENT)


def turn(speed):
    """Turn in place. Positive = turn right (clockwise)."""
    left_drive.spin(FORWARD, speed, PERCENT)
    right_drive.spin(REVERSE, speed, PERCENT)


def heading():
    """Which way the robot points, in degrees from where it started (right = +)."""
    wheel = (left_drive.position(DEGREES) - right_drive.position(DEGREES)) / 2.0
    return wheel / WHEEL_DEGREES_PER_ROBOT_DEGREE


def drive_position():
    """How far the robot has driven forward (in wheel degrees)."""
    return (left_drive.position(DEGREES) + right_drive.position(DEGREES)) / 2.0


def turn_to_heading(target, speed, look=False):
    """Turn in place to a heading (degrees).
    If look=True, stop the moment blue is seen and return the heading where it
    was seen. Otherwise (or if no blue was seen) return None."""
    while not out_of_time():
        error = target - heading()
        if abs(error) <= 1.5:
            break
        # slow down near the target so we don't overshoot
        s = max(5, min(speed, abs(error) * 3))
        turn(s if error > 0 else -s)
        if look and sees_blue():
            seen_at = heading()
            stop_drive()
            if sees_blue_confirmed():
                return seen_at
        wait(10, MSEC)
    stop_drive()
    return None


def move_motor_to(motor, degrees):
    """Move the claw to a position, but never past the 30 s limit."""
    motor.spin_to_position(degrees, DEGREES, wait=False)
    start = brain.timer.time(MSEC)
    while not out_of_time() and not motor.is_done():
        if brain.timer.time(MSEC) - start > 2000:   # stuck - don't wait forever
            break
        wait(10, MSEC)
    motor.stop()


def optical_connected():
    try:
        return optical.installed()
    except AttributeError:
        return True   # this VEXcode version can't check - assume it's there


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
    left_drive.set_position(0, DEGREES)
    right_drive.set_position(0, DEGREES)
    arm.stop()   # hold the arm down where it is

    # Turn on the sensor's light so colors read the same in any room lighting
    optical.set_light(LedStateType.ON)
    optical.set_light_power(100, PERCENT)
    wait(100, MSEC)


def open_claw():
    status("Opening claw")
    claw.set_max_torque(100, PERCENT)
    move_motor_to(claw, CLAW_OPEN_DEGREES)


def search_for_blue():
    """Turn back and forth across the area in front of the robot, one small
    step at a time, stopping after each step to look.
    Returns (heading where blue was first seen, direction we were turning),
    or (None, direction) if time ran out."""
    side = 1 if TURN_RIGHT_FIRST else -1
    while not out_of_time():
        edge = side * SWEEP_HALF_ANGLE
        while not out_of_time() and (edge - heading()) * side > 1.5:
            step = heading() + side * STEP_ANGLE
            if (step - edge) * side > 0:
                step = edge
            seen_at = turn_to_heading(step, SEARCH_TURN_SPEED, look=True)
            if seen_at is not None:
                return seen_at, side
            # stop and look
            show_live("Looking for blue")
            wait(LOOK_PAUSE_MS, MSEC)
            if sees_blue_confirmed():
                return heading(), side
        side = -side   # reached the edge of the sweep - turn back the other way
    return None, side


def reacquire():
    """Blue was lost - look a little left and right to find it again."""
    status("Lost blue - looking nearby")
    center = heading()
    for target in (center - REACQUIRE_ANGLE, center + REACQUIRE_ANGLE, center):
        if turn_to_heading(target, LOCK_TURN_SPEED, look=True) is not None:
            return True
    return False


def find_edge(direction):
    """Turn slowly (1 = right, -1 = left) across the object until blue
    disappears. Returns the last heading that still saw blue."""
    start = heading()
    last_blue = start
    seen_any = False
    lost = 0
    turn(LOCK_TURN_SPEED * direction)
    while not out_of_time() and abs(heading() - start) < LOCK_MAX_ANGLE:
        if sees_blue():
            seen_any = True
            lost = 0
            last_blue = heading()
        elif seen_any:
            lost += 1
            if lost >= CONFIRM_READINGS:
                break
        wait(10, MSEC)
    stop_drive()
    wait(50, MSEC)
    return last_blue


def lock_on(first_seen, side):
    """Find both edges of the object, then turn to exactly halfway between
    them so the object is centered on the sensor and claw."""
    status("Locking on")
    if not sees_blue_confirmed():
        # braked a little past it - swing back to where it was seen
        if turn_to_heading(first_seen, LOCK_TURN_SPEED, look=True) is None:
            if not reacquire():
                return False
    edge_a = find_edge(side)
    edge_b = find_edge(-side)
    turn_to_heading((edge_a + edge_b) / 2.0, LOCK_TURN_SPEED)
    wait(100, MSEC)   # let the robot settle
    if sees_blue_confirmed():
        return True
    return reacquire()


def drive_to_blue():
    """Drive straight at the object, staying locked on, until it's right in
    front of the claw. Then stop."""
    status("Driving to blue")
    start = drive_position()
    limit = mm_to_wheel_degrees(MAX_DRIVE_MM)
    lost = 0
    drive(DRIVE_SPEED)
    while not out_of_time():
        if optical.is_near_object():
            break
        if drive_position() - start > limit:
            stop_drive()
            return False
        if sees_blue():
            lost = 0
        else:
            lost += 1
            if lost >= LOST_READINGS:
                # drifted off the object - stop, find it again, keep going
                stop_drive()
                if not reacquire():
                    return False
                status("Driving to blue")
                lost = 0
                drive(DRIVE_SPEED)
        show_live("Driving to blue")
        wait(10, MSEC)
    stop_drive()

    if EXTRA_DRIVE_MM > 0 and not out_of_time():
        target = drive_position() + mm_to_wheel_degrees(EXTRA_DRIVE_MM)
        drive(EXTRA_DRIVE_SPEED)
        while not out_of_time() and drive_position() < target:
            wait(10, MSEC)
        stop_drive()

    return not out_of_time()


def close_claw():
    status("Closing claw")
    claw.set_max_torque(CLAW_GRIP_TORQUE, PERCENT)
    # Close until the claw squeezes the object (the motor stalls)
    claw.spin(REVERSE, CLAW_SPEED, PERCENT)
    start = brain.timer.time(MSEC)
    wait(300, MSEC)
    while not out_of_time() and abs(claw.velocity(PERCENT)) > 2:
        if brain.timer.time(MSEC) - start > 2000:
            break
        wait(20, MSEC)
    claw.stop()   # HOLD keeps squeezing the object


# ===========================================================================
#  AUTONOMOUS (30 seconds max)
# ===========================================================================
def autonomous():
    setup()
    if not optical_connected():
        status("NO OPTICAL SENSOR - check OPTICAL_PORT")
        return
    Thread(watchdog)

    # 1) start with the claw open
    open_claw()

    while not out_of_time():
        # 2) turn step by step UNTIL blue is seen, then stop
        first_seen, side = search_for_blue()
        if first_seen is None:
            break
        # 3) lock on to the middle of the object
        if not lock_on(first_seen, side):
            continue   # couldn't hold on to it - keep searching
        # 4) drive straight at it and stop when it's in the claw
        if drive_to_blue():
            # 5) close the claw
            if CLOSE_CLAW_AT_END:
                close_claw()
            stop_drive()
            status("Got it!")
            break
        # lost it on the way - go back to searching

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
        brain.screen.print("SENSOR TEST (no driving)")
        brain.screen.next_row()
        if not optical_connected():
            brain.screen.print("NO OPTICAL SENSOR on port")
        else:
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
