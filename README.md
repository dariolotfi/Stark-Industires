# Stark Industries – VEX EXP Clawbot

`src/main.py` is a VEXcode EXP **Python** program with a 30-second autonomous routine:

1. **Search** – spins slowly until the optical sensor sees a blue object (if a full spin finds nothing, it drives forward a bit and searches again).
2. **Line up** – sweeps left and right to find both edges of the blue object, then turns to the exact middle.
3. **Approach** – drives toward the object, re-centering if it drifts off the blue, and stops when the object is right in front of the claw.
4. **Grab** – opens the claw, creeps in slowly, and closes the claw (torque-limited so it squeezes without stalling forever), then lifts the arm.

The routine uses the full 30 seconds: if it loses the blue object or misses, it closes the claw, lowers the arm and starts over. A background timer stops every motor the moment 30 seconds are up, even mid-move. After a successful grab it keeps holding the object until time runs out.

## Setup

1. Open VEXcode EXP, create a new **Python** project, and paste in `src/main.py`.
2. Edit the **CONFIGURATION** section at the top so the ports match your robot (drive, arm, claw, optical).
3. Start the robot with the **arm down** and the **claw closed** – the program treats that as position 0.
4. Mount the optical sensor on the front, facing forward and centered with the claw.

## Tuning

The brain screen shows the current step, time left, and the optical sensor's hue and brightness.

| Setting | What to change it for |
| --- | --- |
| `BLUE_HUE_MIN` / `BLUE_HUE_MAX` | Hold your blue object in front of the sensor and read the hue. |
| `NEAR_BRIGHTNESS` | The brightness reading when the object is right at the claw opening. |
| `CREEP_DISTANCE_MM` | How far to creep so the object is fully inside the claw. |
| `CLAW_OPEN_DEGREES` | How far the claw motor turns to open. |
| `*_REVERSED` | Flip if a motor spins the wrong way. |
