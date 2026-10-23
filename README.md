# Stark Industries – VEX EXP Clawbot

> **Don't paste this file into VEXcode** – it's instructions, not code.
> The robot code is [`src/main.py`](https://raw.githubusercontent.com/dariolotfi/Stark-Industires/claude/eager-pascal-rhmqxo/src/main.py) – open that link, select all, copy, and paste it into an empty VEXcode EXP Python project.

`src/main.py` is a VEXcode EXP **Python** program with a 30-second autonomous routine:

1. **Open the claw.**
2. **Turn** in place until the optical sensor sees a blue object, then stop right away. If the robot coasts past the object while braking, it swings back slowly until it sees blue again.
3. **Drive straight** at the object and stop as soon as the sensor says it is right in front of the claw.
4. **Close the claw** on it and stop.

A background timer stops every motor at 30 seconds, even mid-move. If the robot finishes early, it holds the object until time runs out.

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
| `MIN_BRIGHTNESS` | Raise it if the robot stops on things that aren't blue; lower it if it spins past the blue object. |
| `EXTRA_DRIVE_MM` | Raise it if the robot stops before the object is between the claw fingers. |
| `SEARCH_TURN_SPEED` | Lower it if the robot spins past the object before stopping. |
| `TURN_RIGHT` | Which way the robot spins while searching. |
| `CLAW_OPEN_DEGREES` | How far the claw motor turns to open. |
| `*_REVERSED` | Flip if a motor spins the wrong way. |
