# Stark Industries – VEX EXP Clawbot

> **Don't paste this file into VEXcode** – it's instructions, not code.
> The robot code is [`src/main.py`](https://raw.githubusercontent.com/dariolotfi/Stark-Industires/claude/eager-pascal-rhmqxo/src/main.py) – open that link, select all, copy, and paste it into an empty VEXcode EXP Python project.

`src/main.py` is a VEXcode EXP **Python** program with a 30-second autonomous routine:

1. **Open the claw.**
2. **Turn** left and right across the area in front of the robot in small steps (10° by default), stopping after each step to look, until the optical sensor sees blue. It stops the moment it sees blue.
3. **Lock on** – find both edges of the blue object and turn to the exact middle.
4. **Drive straight** at the object, staying locked on (if it drifts off the blue it stops, finds it again, and keeps going), and stop as soon as the object is right in front of the claw.
5. **Close the claw** on it and stop.

A background timer stops every motor at 30 seconds, even mid-move. If the robot finishes early, it holds the object until time runs out. If the optical sensor isn't found on `OPTICAL_PORT`, the robot doesn't move and the screen says so.

## Setup

1. Open VEXcode EXP, create a new **Python** project, and paste in `src/main.py`.
2. Edit the **CONFIGURATION** section at the top so the ports match your robot (drive, arm, claw, optical).
3. Start the robot with the **arm down** and the **claw closed** – the program treats that as position 0.
4. Mount the optical sensor on the front, facing forward and centered with the claw.

## Tuning

The brain screen shows the current step, time left, the optical sensor's hue and brightness, and whether it counts that as blue.

**Sensor test mode:** set `SENSOR_TEST_MODE = True` and download. The robot won't move; the screen just shows what the sensor reads. Hold the blue object in front of the sensor at different distances to see when it says `BLUE: YES`. Set it back to `False` for the real run.

| Setting | What to change it for |
| --- | --- |
| `BLUE_HUE_MIN` / `BLUE_HUE_MAX` | Hold your blue object in front of the sensor and read the hue. |
| `MIN_BRIGHTNESS` | Raise it if the robot stops on things that aren't blue; lower it if it spins past the blue object. |
| `EXTRA_DRIVE_MM` | Raise it if the robot stops before the object is between the claw fingers. |
| `TURN_RIGHT_FIRST` | Which way the robot turns first when searching. |
| `SWEEP_HALF_ANGLE` | How far left and right of its start the robot looks (degrees). |
| `STEP_ANGLE` / `LOOK_PAUSE_MS` | Size of each turn step and how long it stops to look. |
| `CLAW_OPEN_DEGREES` | How far the claw motor turns to open. |
| `*_REVERSED` | Flip if a motor spins the wrong way. |
