import time

# Calculated conversion values between GRBL units and millimeters. Don't change unless you're changing units
GRBL_SCALE_X = 50.0
GRBL_SCALE_Y = 50.0
GRBL_SCALE_Z = 1.0

#Converts GRBL position to real world mm
def get_position(grbl): 
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

#Converts real world mm measurements back to GRBL units
def move(grbl, x=None, y=None, z=None, feedrate = 100): 
    if x is not None:
        x = x / GRBL_SCALE_X
    else:
        x = None

    if y is not None:
        y = y / GRBL_SCALE_Y
    else:
        y = None

    if z is not None:
        z = z / GRBL_SCALE_Z
    else:
        z = None

    grbl.move_to(x, y, z, feedrate)

#Used to jog the motors via keyboard inputs (keyPressEvent function in touch_logger.py)
def jog(grbl, dx=0.0, dy=0.0, dz=0.0, feedrate=500):
    position = get_position(grbl)

    move(
        grbl,
        x = position["x"] + dx,
        y = position["y"] + dy,
        z = position["z"] + dz,
        feedrate = feedrate
    )

#Moves above an xy point at a safe z position
def approach(grbl, x, y, safe_z, xy_feedrate, z_feedrate): 
    move(
        grbl,
        z = safe_z, 
        feedrate = z_feedrate
    )

    move(
        grbl,
        x = x, 
        y = y, 
        feedrate = xy_feedrate
    )

#Moves z axis down until target force is reached
def press_until_force(grbl, force_logger, target_force, z_step, z_feedrate): 
        position = get_position(grbl)
        z = position["z"]

        while True:
            force = force_logger.update_force()

            if force >= target_force:
                return

            z += z_step

            move(
                grbl,
                z = z, 
                feedrate = z_feedrate
            )
