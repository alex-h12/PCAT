import time

GRBL_SCALE_X = 50.0
GRBL_SCALE_Y = 50.0
GRBL_SCALE_Z = 1.0

def get_position(grbl): #Converts GRBL position to real world mm
    position = grbl.get_position()

    if position is None:
        raise RuntimeError("Could not read GRBL position.")
    
    x = position["x"] * GRBL_SCALE_X
    y = position["y"] * GRBL_SCALE_Y
    z = position["z"] * GRBL_SCALE_Z

    return {
        "x": x, 
        "y": y, 
        "z": z
    }

def move(grbl, x=None, y=None, z=None, feedrate = 100): #Converts real world mm measurements to managable GRBL steps
    if x is not None:
        x = x / 50
    else:
        x = None

    if y is not None:
        y = y / 50
    else:
        y = None

    if z is not None:
        z = z
    else:
        z = None

    grbl.move_to(x, y, z, feedrate)

def jog(grbl, dx=0.0, dy=0.0, dz=0.0, feedrate=500):
    position = get_position(grbl)

    move(
        grbl,
        x = position["x"] + dx,
        y = position["y"] + dy,
        z = position["z"] + dz,
        feedrate = feedrate
    )

def approach(x, y, safe_z, xy_feedrate, z_feedrate): #Moves above a point without unnecessary collision
    position = get_position()

    if position["z"] < safe_z:
        move(z=safe_z, feedrate=z_feedrate)

    move(x=x, y=y, feedrate=xy_feedrate)

def press_until_force(force_logger, target_force, z_step, z_feedrate): #Moves down until target force is reached
        position = get_position()
        z = position["z"]

        while True:
            force = force_logger.update_force()

            if force >= target_force:
                return

            z += z_step
            move(z=z, feedrate=z_feedrate)
