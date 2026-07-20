import time
import threading

# Calculated conversion values between GRBL units and millimeters. Don't change unless you're changing units
GRBL_SCALE_X = 50.0
GRBL_SCALE_Y = 50.0
GRBL_SCALE_Z = 1.0

SAFE_Z = 0.0
MAX_Z = 2.0

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
def press_until_force(
    grbl,
    force_logger,
    target_force,
    z_step,
    z_feedrate,
    max_z=2.0,
    settle_time=0.01,
    status_poll_interval=0.01,
    debug=True
):
    position = get_position(grbl)
    z = position["z"]

    sample_count = 0
    start_time = time.time()

    if debug:
        print(
            f"[PRESS] start_z={z:.3f} mm "
            f"target={target_force:.2f} g "
            f"max_z={max_z:.3f} mm "
            f"step={z_step:.3f} mm "
            f"feed={z_feedrate}"
        )

    while True:
        force = force_logger.update_force(drain_buffer=True)
        sample_count += 1

        if debug:
            age = force_logger.age_seconds()
            age_text = f"{age:.3f}s" if age is not None else "None"
            print(
                f"[PRESS] sample={sample_count} "
                f"z={z:.3f} mm "
                f"force={force} g "
                f"age={age_text}"
            )

        if force is None:
            if debug:
                print("[PRESS] No valid force sample.")
            time.sleep(0.01)
            continue

        if force_logger.is_stale(max_age = 0.25):
            raise RuntimeError("Force sensor stopped providing fresh data.")
        
        if force >= target_force:
            if debug:
                print(
                    f"[PRESS] target reached at z={z:.3f} mm "
                    f"force={force:.2f} g "
                    f"elapsed={time.time() - start_time:.3f}s"
                )
            return z

        next_z = z + z_step
        if next_z > max_z:
            raise RuntimeError(
                f"Max Z reached before target force. "
                f"z={z:.3f} mm, force={force}, target={target_force}"
            )

        move(
            grbl,
            z=next_z,
            feedrate=z_feedrate
        )

        grbl.wait_until_idle(timeout=5.0)

        if settle_time > 0:
            time.sleep(settle_time)

        z = next_z
