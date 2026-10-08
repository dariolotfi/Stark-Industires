# ---------------------------------------------------------------------------
#  Stark Industries - VEX EXP Clawbot
#  30-second autonomous: find a BLUE object with the optical sensor, line up
#  on it, open the claw, creep in slowly, and close the claw on it.
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
AUTON_TIME_LIMIT_S = 30.0         # total autonomous time

# Blue detection (optical sensor hue is 0-360; blue is roughly 190-250)
BLUE_HUE_MIN = 190
BLUE_HUE_MAX = 250
MIN_BRIGHTNESS = 3                # ignore very dark readings (nothing in front)
CONFIRM_READINGS = 3              # readings in a row needed to trust "blue"
NEAR_BRIGHTNESS = 30              # brightness when the object is right in front of the claw
                                  # (watch the brain screen while testing and tune this)

# Speeds (percent)
SEARCH_TURN_SPEED = 15            # spin speed while scanning for blue
ALIGN_TURN_SPEED = 10             # spin speed while finding the object's edges
APPROACH_SPEED = 20               # drive speed toward the object
CREEP_SPEED = 8                   # very slow speed once the claw is open
ARM_SPEED = 40
CLAW_SPEED = 40

# Distances / angles
SEARCH_STEP_MM = 150              # drive this far forward if a full spin finds nothing
CREEP_DISTANCE_MM = 120           # how far to creep in so the object is inside the claw
MAX_APPROACH_MM = 1000            # give up driving forward after this far
ARM_GRAB_ANGLE = 0                # arm position (motor degrees) for grabbing - 0 = all the way down
ARM_LIFT_ANGLE = 300              # arm position after grabbing (lift the object)
CLAW_OPEN_DEGREES = 90            # how far the claw motor turns to open
CLAW_GRIP_TORQUE = 50             # percent torque used to squeeze the object
LIFT_AFTER_GRAB = True            # lift the arm after grabbing


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
    # handy for tuning BLUE_HUE_MIN/MAX and NEAR_BRIGHTNESS
    brain.screen.print("Hue %d  Bright %d" % (optical.hue(), optical.brightness()))


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


def reset_drive_encoders():
    left_drive.set_position(0, DEGREES)
    right_drive.set_position(0, DEGREES)


def sees_blue():
    """One raw reading: is there a blue object right in front of the sensor?"""
    if not optical.is_near_object():
        return False
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


def turn_to(target, speed):
    """Spin in place until turn_position() reaches target (wheel degrees)."""
    tolerance = 3
    while not out_of_time():
        error = target - turn_position()
        if abs(error) <= tolerance:
            break
        # slow down near the target so we don't overshoot
        s = max(5, min(speed, abs(error) * 0.5))
        turn(s if error > 0 else -s)
        wait(10, MSEC)
    stop_drive()


def move_motor_to(motor, degrees):
    """Move the arm or claw to a position, but never past the 30 s limit."""
    motor.spin_to_position(degrees, DEGREES, wait=False)
    start = brain.timer.time(MSEC)
    while not out_of_time() and not motor.is_done():
        if brain.timer.time(MSEC) - start > 3000:   # stuck - don't wait forever
            break
        wait(10, MSEC)
    motor.stop()


def drive_distance(mm, speed):
    """Drive straight a set distance (negative mm = backwards)."""
    target = drive_position() + mm_to_wheel_degrees(mm)
    direction = 1 if mm >= 0 else -1
    while not out_of_time():
        if (target - drive_position()) * direction <= 0:
            break
        drive(speed * direction)
        wait(10, MSEC)
    stop_drive()


# ===========================================================================
#  AUTONOMOUS STEPS
# ===========================================================================
def setup():
    brain.timer.clear()

    left_drive.set_stopping(BRAKE)
    right_drive.set_stopping(BRAKE)
    arm.set_stopping(HOLD)
    claw.set_stopping(HOLD)

    arm.set_velocity(ARM_SPEED, PERCENT)
    claw.set_velocity(CLAW_SPEED, PERCENT)
    claw.set_max_torque(CLAW_GRIP_TORQUE, PERCENT)
    claw.set_timeout(2, SECONDS)   # never stall the claw forever
    arm.set_timeout(3, SECONDS)

    # The robot should START with the arm down and the claw closed.
    arm.set_position(0, DEGREES)
    claw.set_position(0, DEGREES)
    reset_drive_encoders()

    # Turn on the sensor's light so colors read the same in any room lighting
    optical.set_light(LedStateType.ON)
    optical.set_light_power(100, PERCENT)
    wait(200, MSEC)

    # Put the arm at grabbing height and keep the claw closed while searching
    move_motor_to(arm, ARM_GRAB_ANGLE)


def search_for_blue():
    """Spin slowly until the sensor sees blue. If a full spin finds nothing,
    drive forward a little and try again. Returns True when blue is found."""
    status("Searching for blue...")
    one_full_spin = mm_to_wheel_degrees(3.1416 * 180)  # ~ one robot rotation
    while not out_of_time():
        start = turn_position()
        turn(SEARCH_TURN_SPEED)
        while not out_of_time() and turn_position() - start < one_full_spin:
            if sees_blue_confirmed():
                stop_drive()
                return True
            wait(10, MSEC)
        stop_drive()
        # Nothing found this spin - move to a new spot and look again
        status("Nothing found, moving...")
        drive_distance(SEARCH_STEP_MM, APPROACH_SPEED)
    stop_drive()
    return False


def find_edge(direction):
    """Turn (direction 1 = right, -1 = left) until blue is lost.
    Returns the turn position of that edge of the object."""
    max_sweep = mm_to_wheel_degrees(150)   # safety: don't spin forever
    start = turn_position()
    turn(ALIGN_TURN_SPEED * direction)
    lost_count = 0
    edge = start
    while not out_of_time() and abs(turn_position() - start) < max_sweep:
        if sees_blue():
            lost_count = 0
            edge = turn_position()      # last spot that still saw blue
        else:
            lost_count += 1
            if lost_count >= CONFIRM_READINGS:
                break
        wait(10, MSEC)
    stop_drive()
    wait(100, MSEC)
    return edge


def align_on_blue():
    """Center the robot on the blue object: find its left edge, find its
    right edge, then turn to exactly halfway between them."""
    status("Lining up...")
    left_edge = find_edge(-1)
    right_edge = find_edge(1)
    turn_to((left_edge + right_edge) / 2.0, ALIGN_TURN_SPEED)
    wait(150, MSEC)  # let the robot settle
    return sees_blue_confirmed()


def approach_blue():
    """Drive toward the object until it's right in front of the claw.
    If we drift off the blue, stop and re-align."""
    status("Approaching...")
    start = drive_position()
    max_degrees = mm_to_wheel_degrees(MAX_APPROACH_MM)
    while not out_of_time():
        if drive_position() - start > max_degrees:
            return False
        if not sees_blue():
            stop_drive()
            wait(50, MSEC)
            if not sees_blue_confirmed():
                # lost it - sweep a little to find it again, then re-center
                if not small_sweep_for_blue() or not align_on_blue():
                    return False
                status("Approaching...")
        # optical sensor is very close and still blue -> we're there
        if optical.brightness() >= NEAR_BRIGHTNESS and sees_blue():
            stop_drive()
            return True
        drive(APPROACH_SPEED)
        wait(20, MSEC)
    stop_drive()
    return False


def small_sweep_for_blue():
    """Look left and right a little to re-find the object."""
    status("Re-finding blue...")
    center = turn_position()
    sweep = mm_to_wheel_degrees(60)
    for target in (center - sweep, center + sweep):
        direction = 1 if target > turn_position() else -1
        turn(ALIGN_TURN_SPEED * direction)
        while not out_of_time() and (target - turn_position()) * direction > 0:
            if sees_blue_confirmed():
                stop_drive()
                return True
            wait(10, MSEC)
        stop_drive()
    turn_to(center, ALIGN_TURN_SPEED)
    return False


def open_claw():
    status("Opening claw...")
    claw.set_max_torque(100, PERCENT)
    move_motor_to(claw, CLAW_OPEN_DEGREES)


def creep_in():
    """Drive very slowly so the object slides into the open claw."""
    status("Creeping in...")
    drive_distance(CREEP_DISTANCE_MM, CREEP_SPEED)
    wait(150, MSEC)


def close_claw():
    status("Grabbing!")
    claw.set_max_torque(CLAW_GRIP_TORQUE, PERCENT)
    # Close until the claw squeezes the object (the motor stalls) or times out
    claw.spin(REVERSE, CLAW_SPEED, PERCENT)
    wait(300, MSEC)
    while not out_of_time() and abs(claw.velocity(PERCENT)) > 2:
        wait(20, MSEC)
    # HOLD keeps squeezing the object
    claw.stop()


def lift_arm():
    status("Lifting...")
    move_motor_to(arm, ARM_LIFT_ANGLE)


def stop_everything():
    stop_drive()
    arm.stop()
    claw.stop()


def reset_for_retry():
    """Close the claw and put the arm back down before trying again."""
    stop_drive()
    claw.set_max_torque(100, PERCENT)
    move_motor_to(claw, 0)
    move_motor_to(arm, ARM_GRAB_ANGLE)


def watchdog():
    """Runs in the background: stops EVERYTHING the moment 30 s are up,
    even if the robot is in the middle of a move."""
    while not out_of_time():
        wait(20, MSEC)
    stop_everything()
    status("Time's up!")


# ===========================================================================
#  AUTONOMOUS (30 seconds)
# ===========================================================================
def try_to_grab():
    """One full attempt: find, line up, approach, grab. True if it grabbed."""
    if not search_for_blue():
        return False
    if not align_on_blue():
        return False
    if not approach_blue():
        return False

    # Final re-center right in front of the object before opening the claw
    if not sees_blue_confirmed():
        small_sweep_for_blue()
    if not align_on_blue():
        return False

    # 1) open the claw  2) creep in slowly  3) close the claw
    open_claw()
    creep_in()
    close_claw()
    return not out_of_time()


def autonomous():
    setup()
    Thread(watchdog)

    # Keep trying for the whole 30 seconds - if something goes wrong
    # (lost the blue, couldn't line up) reset and start over.
    attempt = 1
    grabbed = False
    while not out_of_time():
        status("Attempt %d" % attempt)
        if try_to_grab():
            grabbed = True
            break
        if out_of_time():
            break
        status("Missed - retrying")
        reset_for_retry()
        attempt += 1

    if grabbed:
        if LIFT_AFTER_GRAB:
            lift_arm()
        stop_drive()
        status("Got it!")
        # Keep squeezing the object until the 30 seconds are over
        while not out_of_time():
            wait(20, MSEC)

    stop_everything()
    status("Auton done")


# ===========================================================================
#  START - runs the autonomous as soon as the program starts
# ===========================================================================
autonomous()
