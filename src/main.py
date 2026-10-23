# ---------------------------------------------------------------------------
#  Stark Industries - VEX EXP Clawbot
#  30-second autonomous:
#    1. open the claw
#    2. turn in place UNTIL the optical sensor sees a BLUE object
#    3. stop, then drive straight at it
#    4. stop when it's inside the claw, close the claw, and stop
#  Everything stops at 30 seconds no matter what.
#
#  Written for VEXcode EXP (Python).  Paste into a new VEXcode EXP Python
#  project, or open this file directly, and download it to the brain.
# ---------------------------------------------------------------------------
from vex import *

# ===========================================================================
#  CONFIGURATION - change these to match YOUR robot
# ===========================================================================
# Ports
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

# Robot geometry (EXP Clawbot defaults)
WHEEL_TRAVEL_MM = 200.0           # distance the wheel rolls in one full turn

# Timing
AUTON_TIME_LIMIT_S = 30.0         # the autonomous can never run longer than this

# Blue detection (optical sensor hue is 0-360; blue is roughly 190-250)
BLUE_HUE_MIN = 190
BLUE_HUE_MAX = 250
MIN_BRIGHTNESS = 5                # ignore dark readings (nothing in front of the sensor)
CONFIRM_READINGS = 3              # readings in a row needed to trust "blue"

# Turning
TURN_RIGHT = True                 # True = spin clockwise while searching, False = counter-clockwise
SEARCH_TURN_SPEED = 15            # percent - slower spins stop closer to the object
NUDGE_TURN_SPEED = 8              # percent - used to swing back if the robot coasts past the blue

# Driving
DRIVE_SPEED = 25                  # percent - speed driving straight at the object
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


def status(line):
    brain.screen.clear_screen()
    brain.screen.set_cursor(1, 1)
    brain.screen.print(line)
    brain.screen.next_row()
    brain.screen.print("Time left: %.1f" % max(0, time_left()))
    brain.screen.next_row()
    # handy for tuning BLUE_HUE_MIN/MAX and MIN_BRIGHTNESS
    brain.screen.print("Hue %d  Bright %d" % (int(optical.hue()), int(optical.brightness())))


def mm_to_wheel_degrees(mm):
    return mm / WHEEL_TRAVEL_MM * 360.0


def stop_drive():
    left_drive.stop()
    right_drive.stop()


def drive(speed):
    """Drive straight. Positive = forward."""
    left_drive.spin(FORWARD, speed, PERCENT)
    right_drive.spin(FORWARD, speed, PERCENT)


def turn(speed):
    """Spin in place. Positive = turn right (clockwise)."""
    left_drive.spin(FORWARD, speed, PERCENT)
    right_drive.spin(REVERSE, speed, PERCENT)


def turn_position():
    """How far the robot has turned (in wheel degrees). Grows when turning right."""
    return (left_drive.position(DEGREES) - right_drive.position(DEGREES)) / 2.0


def drive_position():
    """How far the robot has driven forward (in wheel degrees)."""
    return (left_drive.position(DEGREES) + right_drive.position(DEGREES)) / 2.0


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


def move_motor_to(motor, degrees):
    """Move the claw to a position, but never past the 30 s limit."""
    motor.spin_to_position(degrees, DEGREES, wait=False)
    start = brain.timer.time(MSEC)
    while not out_of_time() and not motor.is_done():
        if brain.timer.time(MSEC) - start > 2000:   # stuck - don't wait forever
            break
        wait(10, MSEC)
    motor.stop()


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


def turn_until_blue():
    """Spin in place until the sensor sees blue, then stop right away."""
    status("Turning - looking for blue")
    direction = 1 if TURN_RIGHT else -1
    turn(SEARCH_TURN_SPEED * direction)
    while not out_of_time():
        if sees_blue_confirmed():
            stop_drive()
            return True
        wait(10, MSEC)
    stop_drive()
    return False


def face_blue():
    """The robot can coast a little past the object while braking. If the
    sensor no longer sees blue, swing back slowly until it does."""
    wait(100, MSEC)   # let the robot settle
    if sees_blue():
        return True
    status("Swinging back to blue")
    direction = -1 if TURN_RIGHT else 1
    start = turn_position()
    limit = mm_to_wheel_degrees(60)   # don't swing back more than a little
    turn(NUDGE_TURN_SPEED * direction)
    while not out_of_time() and abs(turn_position() - start) < limit:
        if sees_blue():
            stop_drive()
            return True
        wait(10, MSEC)
    stop_drive()
    return False


def drive_to_blue():
    """Drive straight until the object is right in front of the claw, then stop."""
    status("Driving to blue")
    start = drive_position()
    limit = mm_to_wheel_degrees(MAX_DRIVE_MM)
    drive(DRIVE_SPEED)
    while not out_of_time():
        if optical.is_near_object():
            break
        if drive_position() - start > limit:
            stop_drive()
            return False
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
    Thread(watchdog)

    # 1) start with the claw open
    open_claw()

    while not out_of_time():
        # 2) turn UNTIL blue is seen, then stop
        if not turn_until_blue():
            break
        if not face_blue():
            continue   # coasted off it and couldn't find it again - keep turning

        # 3) drive straight at it and 4) stop when it's in the claw
        if drive_to_blue():
            if CLOSE_CLAW_AT_END:
                close_claw()
            status("Got it!")
            break
        # drove too far without reaching it - go back to searching

    stop_drive()
    # Keep holding the claw shut until the 30 seconds are over
    while not out_of_time():
        wait(20, MSEC)
    stop_everything()


# ===========================================================================
#  START - runs the autonomous as soon as the program starts
# ===========================================================================
autonomous()
