import time

from motion_control.motion import move, approach, press_until_force

TEST_TARGET_FORCE = 10.0

TEST_Z_STEP = 0.2
TEST_SAFE_Z = 0.0

TEST_XY_FEEDRATE = 50
TEST_Z_FEEDRATE = 50

GRID_COLUMNS = 15
GRID_ROWS = 10

SLEEP_TIME = 2

def create_grid(start, end, points):
    step = (end - start) / (points - 1)

    return [
        start + i * step
        for i in range(points)
    ]

def tap_test(grbl, force_logger, calibration, controller):
    print("Starting tap test...")
    
    x_points = create_grid(
        calibration.x_min,
        calibration.x_max,
        GRID_COLUMNS
    )

    y_points = create_grid(
        calibration.y_min,
        calibration.y_max,
        GRID_ROWS
    )

    for row_index, y in enumerate(y_points):
        if row_index % 2 == 0:
            row_x_points = x_points
        else:
            row_x_points = reversed(x_points)

        for x in row_x_points:
            approach(
                grbl = grbl,
                x = x,
                y = y,
                safe_z = TEST_SAFE_Z,
                xy_feedrate = TEST_XY_FEEDRATE,
                z_feedrate = TEST_Z_FEEDRATE
            )

            press_until_force(
                grbl,
                force_logger,
                target_force = TEST_TARGET_FORCE,
                z_step = TEST_Z_STEP,
                z_feedrate = TEST_Z_FEEDRATE
            )

            approach(
                grbl = grbl,
                x = x,
                y = y,
                safe_z = TEST_SAFE_Z,
                xy_feedrate = TEST_XY_FEEDRATE,
                z_feedrate = TEST_Z_FEEDRATE
            )

            controller.set_robot_position({
                "x": x,
                "y": y,
                "z": TEST_SAFE_Z
            })

            time.sleep(SLEEP_TIME)

    approach(
        grbl,
        x = calibration.x_min,
        y = calibration.y_min,
        safe_z = TEST_SAFE_Z,
        xy_feedrate = TEST_XY_FEEDRATE,
        z_feedrate = TEST_Z_FEEDRATE
    )

    print("Tap test complete.")

def swipe_test(grbl, force_logger, calibration, direction, controller):
    print(f"Starting {direction} swipe test...")

    if direction == "horizontal":
        y_points = create_grid(
            calibration.y_min,
            calibration.y_max,
            GRID_ROWS
        )

        x_min = calibration.x_min
        x_max = calibration.x_max

        for row_index, y in enumerate(y_points):
            if row_index % 2 == 0:
                x_start = x_min
                x_end = x_max
            else:
                x_start = x_max
                x_end = x_min

            approach(
                grbl,
                x = x_start,
                y = y,
                safe_z = TEST_SAFE_Z,
                xy_feedrate = TEST_XY_FEEDRATE,
                z_feedrate = TEST_Z_FEEDRATE
            )

            press_until_force(
                grbl,
                force_logger,
                target_force = TEST_TARGET_FORCE,
                z_step = TEST_Z_STEP,
                z_feedrate = TEST_Z_FEEDRATE
            )
            
            time.sleep(SLEEP_TIME)

            move(
                grbl,
                x = x_end,
                y = y,
                feedrate = TEST_XY_FEEDRATE
            )

            time.sleep(SLEEP_TIME)

    if direction == "vertical":
        x_points = create_grid(
            calibration.x_min,
            calibration.x_max,
            GRID_COLUMNS
        )

        y_min = calibration.y_min
        y_max = calibration.y_max

        for row_index, x in enumerate(x_points):
            if row_index % 2 == 0:
                y_start = y_min
                y_end = y_max
            else:
                y_start = y_max
                y_end = y_min

            approach(
                grbl,
                x = x,
                y = y_start,
                safe_z = TEST_SAFE_Z,
                xy_feedrate = TEST_XY_FEEDRATE,
                z_feedrate = TEST_Z_FEEDRATE
            )

            press_until_force(
                grbl,
                force_logger,
                target_force = TEST_TARGET_FORCE,
                z_step = TEST_Z_STEP,
                z_feedrate = TEST_Z_FEEDRATE
            )

            time.sleep(SLEEP_TIME)

            move(
                grbl,
                x = x,
                y = y_end,
                feedrate = TEST_XY_FEEDRATE
            )

            time.sleep(SLEEP_TIME)

    approach(
        grbl,
        x = calibration.x_min,
        y = calibration.y_min,
        safe_z = TEST_SAFE_Z,
        xy_feedrate = TEST_XY_FEEDRATE,
        z_feedrate = TEST_Z_FEEDRATE
    )

    print(f"Completed {direction} swipe test")
