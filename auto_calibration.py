import time

from motion_control.motion import get_position, approach, press_until_force

CAL_TARGET_FORCE = 20.0

CAL_Z_STEP = 0.2
CAL_SAFE_Z = 0.5
CAL_Z_FEEDRATE = 20

CAL_XY_STEP = 1.0
CAL_XY_FEEDRATE = 50

LOST_TOUCH_LIMIT = 5

class ScreenCalibration:
    def __init__(self):
        self.x_min = None
        self.x_max = None
        self.y_min = None
        self.y_max = None

        self.margin = 5.0 #in mm

    def set_bounds(self, x_min, x_max, y_min, y_max):
        self.x_min = float(x_min) + self.margin
        self.x_max = float(x_max) - self.margin
        self.y_min = float(y_min) + self.margin
        self.y_max = float(y_max) - self.margin

    def expected_touch_conversion(self, robot_x, robot_y):
        expected_x = (robot_x - self.x_min) / (self.x_max - self.x_min)
        expected_y = (robot_y - self.y_min) / (self.y_max - self.y_min)

        return expected_x, expected_y

class CalibrationRunner:
    def __init__(self, grbl, force_logger, touch_logger):
        self.grbl = grbl
        self.force_logger = force_logger
        self.touch_logger = touch_logger
        self.center_position = None

        self.calibration = ScreenCalibration()

    def touch_screen(self):
        press_until_force(
            grbl = self.grbl,
            force_logger = self.force_logger,
            target_force = CAL_TARGET_FORCE,
            z_step = CAL_Z_STEP,
            z_feedrate = CAL_Z_FEEDRATE
        )

    def center(self):
        approach(
            grbl = self.grbl,
            x = self.center_position["x"],
            y = self.center_position["y"],
            safe_z = CAL_SAFE_Z,
            xy_feedrate = CAL_XY_FEEDRATE,
            z_feedrate = CAL_Z_FEEDRATE
        )

    def scan_direction(self, axis, direction):
        last_valid_position = None
        last_touch_time = None
        lost_touch_count = 0
        distance = 0.0

        while True:
            position = self.grbl.get_position()

            x = position["x"]
            y = position["y"]

            if axis == "x":
                x += direction * CAL_XY_STEP
            elif axis == "y":
                y += direction * CAL_XY_STEP

            self.grbl.move_to(x=x, y=y, feedrate=CAL_XY_FEEDRATE)
            time.sleep(0.05)

            touch = self.touch_logger.get_latest_touch()

            if touch is None:
                touch_time = None
            else:
                touch_time = touch.get("timestamp")

            if touch is not None and touch_time != last_touch_time:
                last_valid_position = self.grbl.get_position()
                last_touch_time = touch_time
                lost_touch_count = 0
            else:
                lost_touch_count += 1

            if lost_touch_count >= LOST_TOUCH_LIMIT:
                break

            distance += CAL_XY_STEP

        if last_valid_position is None:
            raise RuntimeError("No valid touch points found during scan")
        
        return  last_valid_position
    
    def run(self):
        print("Starting screen calibration...")

        self.center_position = self.grbl.get_position()
        
        self.touch_screen()
        print("Scanning left...")
        left = self.scan_direction(axis="x", direction=-1)
        self.center()

        self.touch_screen()
        print("Scanning right...")
        right = self.scan_direction(axis="x", direction=1)
        self.center()

        self.touch_screen()
        print("Scanning down...")
        down = self.scan_direction(axis="y", direction=-1)
        self.center()

        self.touch_screen()
        print("Scanning up...")
        up = self.scan_direction(axis="y", direction=1)
        self.center()

        self.calibration.set_bounds(
            x_min=left["x"],
            x_max=right["x"],
            y_min=down["y"],
            y_max=up["y"]
        )

        print("Calibration complete.")
        print(f"X range: {self.calibration.x_min:.2f} to {self.calibration.x_max:.2f}")
        print(f"Y range: {self.calibration.y_min:.2f} to {self.calibration.y_max:.2f}")

        return self.calibration
