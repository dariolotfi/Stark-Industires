# ---------------------------------------------------------------------------
#  Stark Industries - VEX EXP Clawbot          (version v7 - finds optical port)
#
#  Latest version of this code (open, Cmd/Ctrl+A, copy, paste into VEXcode):
#  https://raw.githubusercontent.com/dariolotfi/Stark-Industires/claude/eager-pascal-rhmqxo/src/main.py
#
#  30-second autonomous:
#    1. open the claw
#    2. look straight ahead, then turn a small step at a time - right, then
#       left, then right - stopping after every step to look, UNTIL the
#       optical sensor sees a BLUE object. It never spins in a full circle.
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
#       (If the optical sensor isn't on OPTICAL_PORT, the code finds it on
#       any other port by itself - the screen shows which port it's using.)
#    4. Start the robot with the arm DOWN and the claw CLOSED.
#    5. Put the blue object within about 10-20 cm in front of the robot -
#       the optical sensor can only see color up close.
#    The brain screen starts with "[v7]" - if it doesn't, you're running
#    an old version of the code.
#
#  TUNING (the brain screen shows hue, brightness and "BLUE: YES/no"):
#    - SENSOR_TEST_MODE = True -> robot does not move, screen shows what the
#      sensor sees. Hold the blue object in front of it. Set back to False.
#    - BLUE_HUE_MIN / BLUE_HUE_MAX -> match the hue your blue object shows.
#    - MIN_BRIGHTNESS -> lower it if the sensor won't say BLUE on your object.
#    - STEP_TIME_MS -> bigger = bigger turn steps.
#      STEPS_PER_SIDE -> how many steps it looks to each side.
#    - EXTRA_DRIVE_MM -> raise it if the robot stops before the object is
#      between the claw fingers.
#    - *_REVERSED -> flip if a motor turns the wrong way.
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

# Motor directions - flip one of these if that motor turns the wrong way
LEFT_DRIVE_REVERSED = False
RIGHT_DRIVE_REVERSED = True
CLAW_REVERSED = False

# Wheel size (only used for the "drive this far" distances)
WHEEL_TRAVEL_MM = 200.0           # distance the wheel rolls in one full turn

# Sensor test mode: set to True, download, and the robot will NOT move. The
# screen just shows what the optical sensor reads. Hold your blue object in
# front of it to check BLUE_HUE_MIN/MAX and MIN_BRIGHTNESS, then set back to False.
SENSOR_TEST_MODE = False

# Timing
AUTON_TIME_LIMIT_S = 30.0         # the autonomous can never run longer than this

# Blue detection (optical sensor hue is 0-360; blue is roughly 180-260)
BLUE_HUE_MIN = 180
BLUE_HUE_MAX = 260
MIN_BRIGHTNESS = 2                # ignore dark readings (nothing in front of the sensor)
CONFIRM_READINGS = 3              # readings in a row needed to trust "blue"

# Searching - turn one small step, stop, look, repeat.
# The robot looks STEPS_PER_SIDE steps to one side, then sweeps back across
# to the same distance on the other side, and so on. It never goes all the
# way around.
TURN_RIGHT_FIRST = True           # which way to turn first
SEARCH_TURN_SPEED = 20            # percent
STEP_TIME_MS = 150                # how long each turn step lasts (bigger = bigger steps)
STEPS_PER_SIDE = 10               # how many steps to look to each side
LOOK_PAUSE_MS = 200               # how long to stop and look after each step

# Locking on
LOCK_TURN_SPEED = 10              # percent - slow turn used to center on the object
LOCK_MAX_MS = 1500                # never turn longer than this while centering
REACQUIRE_MS = 600                # if blue is lost, look this long left/right to find it again

# Driving
DRIVE_SPEED = 20                  # percent - speed driving straight at the object
LOST_READINGS = 10                # readings in a row without blue before re-locking (10 = 0.1 s)
EXTRA_DRIVE_MM = 0                # drive this much further AFTER the sensor says the object is
                                  # close. Raise it if the robot stops before the object is
                                  # between the claw fingers; keep 0 if it is already inside.
EXTRA_DRIVE_SPEED = 10            # percent - speed for that extra bit
MAX_DRIVE_MM = 1000               # give up driving straight after this far

# Claw
CLAW_OPEN_DEGREES = 90            # how far the claw motor turns to open
CLAW_SPEED = 50                   # percent
CLAW_GRIP_TORQUE = 50             # percent torque used to squeeze the object
CLOSE_CLAW_AT_END = True          # close the claw on the object once the robot has stopped

VERSION = "v7"


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
    # handy for tuning BLUE_HUE_MIN/MAX and MIN_BRIGHTNESS
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


def drive(speed):
    """Drive straight. Positive = forward."""
    run_motor(left_drive, LEFT_DRIVE_REVERSED, speed)
    run_motor(right_drive, RIGHT_DRIVE_REVERSED, speed)


def turn(speed):
    """Turn in place. Positive = turn right (clockwise)."""
    run_motor(left_drive, LEFT_DRIVE_REVERSED, speed)
    run_motor(right_drive, RIGHT_DRIVE_REVERSED, -speed)


def turn_amount():
    """How far the robot has turned, in wheel degrees (right = +)."""
    return (motor_position(left_drive, LEFT_DRIVE_REVERSED)
            - motor_position(right_drive, RIGHT_DRIVE_REVERSED)) / 2.0


def drive_amount():
    """How far the robot has driven forward, in wheel degrees."""
    return (motor_position(left_drive, LEFT_DRIVE_REVERSED)
            + motor_position(right_drive, RIGHT_DRIVE_REVERSED)) / 2.0


def turn_for_time(direction, ms, speed, look=True):
    """Turn (1 = right, -1 = left) for a set time. If look=True, stop the
    moment blue is seen and return True."""
    start = now_ms()
    turn(speed * direction)
    while not out_of_time() and now_ms() - start < ms:
        if look and sees_blue():
            stop_drive()
            if sees_blue_confirmed():
                return True
            turn(speed * direction)
        wait(10, MSEC)
    stop_drive()
    return False


def turn_to_amount(target, speed):
    """Turn until turn_amount() reaches target (used to center on the object)."""
    start = now_ms()
    while not out_of_time() and now_ms() - start < 2000:
        error = target - turn_amount()
        if abs(error) <= 3:
            break
        s = max(5, min(speed, abs(error) * 0.5))
        turn(s if error > 0 else -s)
        wait(10, MSEC)
    stop_drive()


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


def look():
    """Stand still for a moment and take a steady reading."""
    wait(LOOK_PAUSE_MS, MSEC)
    return sees_blue_confirmed()


def search_for_blue():
    """Look straight ahead, then turn one small step at a time, stopping to
    look after every step: STEPS_PER_SIDE steps one way, then back across to
    the other side, and so on. Returns the direction it was turning when it
    saw blue (1 = right, -1 = left), or 0 if time ran out."""
    direction = 1 if TURN_RIGHT_FIRST else -1
    status("Looking ahead")
    if look():
        return direction

    steps = STEPS_PER_SIDE          # first: from the middle out to one side
    while not out_of_time():
        for _ in range(steps):
            show_live("Looking for blue")
            if turn_for_time(direction, STEP_TIME_MS, SEARCH_TURN_SPEED):
                return direction    # saw blue while turning - already stopped
            if out_of_time():
                return 0
            if look():
                return direction
        direction = -direction
        steps = 2 * STEPS_PER_SIDE  # then all the way across to the other side
    return 0


def reacquire():
    """Blue was lost - look a little left and right to find it again."""
    status("Lost blue - looking nearby")
    for direction, ms in ((-1, REACQUIRE_MS), (1, 2 * REACQUIRE_MS), (-1, REACQUIRE_MS)):
        if turn_for_time(direction, ms, LOCK_TURN_SPEED):
            return True
    return False


def find_edge(direction):
    """Turn slowly (1 = right, -1 = left) across the object until blue
    disappears. Returns the last turn_amount() that still saw blue."""
    start = now_ms()
    last_blue = turn_amount()
    seen_any = False
    lost = 0
    turn(LOCK_TURN_SPEED * direction)
    while not out_of_time() and now_ms() - start < LOCK_MAX_MS:
        if sees_blue():
            seen_any = True
            lost = 0
            last_blue = turn_amount()
        elif seen_any:
            lost += 1
            if lost >= CONFIRM_READINGS:
                break
        wait(10, MSEC)
    stop_drive()
    wait(50, MSEC)
    return last_blue


def lock_on(direction):
    """Find both edges of the object, then turn to exactly halfway between
    them so the object is centered on the sensor and claw."""
    status("Locking on")
    wait(100, MSEC)   # let the robot settle
    if not sees_blue_confirmed():
        # braked a little past it - swing back slowly
        if not turn_for_time(-direction, REACQUIRE_MS, LOCK_TURN_SPEED):
            if not reacquire():
                return False
    edge_a = find_edge(direction)
    edge_b = find_edge(-direction)
    turn_to_amount((edge_a + edge_b) / 2.0, LOCK_TURN_SPEED)
    wait(100, MSEC)
    if sees_blue_confirmed():
        return True
    return reacquire()


def drive_to_blue():
    """Drive straight at the object, staying locked on, until it's right in
    front of the claw. Then stop."""
    status("Driving to blue")
    start = drive_amount()
    limit = mm_to_wheel_degrees(MAX_DRIVE_MM)
    lost = 0
    drive(DRIVE_SPEED)
    while not out_of_time():
        if optical.is_near_object():
            break
        if drive_amount() - start > limit:
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
        target = drive_amount() + mm_to_wheel_degrees(EXTRA_DRIVE_MM)
        drive(EXTRA_DRIVE_SPEED)
        while not out_of_time() and drive_amount() < target:
            wait(10, MSEC)
        stop_drive()

    return not out_of_time()


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

    while not out_of_time():
        # 2) turn step by step UNTIL blue is seen, then stop
        direction = search_for_blue()
        if direction == 0:
            break
        # 3) lock on to the middle of the object
        if not lock_on(direction):
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
