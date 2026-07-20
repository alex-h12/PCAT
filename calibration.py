import time

from PyQt6.QtWidgets import QApplication

from motion_control.motion import get_position, approach, press_until_force

CAL_TARGET_FORCE = 20.0

CAL_Z_STEP = 0.2
CAL_SAFE_Z = 0.0

CAL_Z_FEEDRATE = 50
CAL_XY_FEEDRATE = 50

#Time allowed for Windows to report a new touch
TOUCH_TIMEOUT = 3.0

class ScreenCalibration:
    def __init__(self):
        #Raw robot bounds
        self.robot_x_min = None
        self.robot_x_max = None
        self.robot_y_min = None
        self.robot_y_max = None

        #Touchscreen coordinates registered at robot bounds
        self.screen_x_min = None
        self.screen_x_max = None
        self.screen_y_min = None
        self.screen_y_max = None

        #Inset robot bounds used during testing
        self.x_min = None
        self.x_max = None
        self.y_min = None
        self.y_max = None

        self.safe_z = CAL_SAFE_Z
        self.margin_mm = 5.0 #in mm

    def set_bounds(self, robot_x_min, robot_x_max, robot_y_min, robot_y_max, screen_x_min, screen_x_max, screen_y_min, screen_y_max):
        self.robot_x_min = float(robot_x_min)
        self.robot_x_max = float(robot_x_max)
        self.robot_y_min = float(robot_y_min)
        self.robot_y_max = float(robot_y_max)

        self.screen_x_min = float(screen_x_min)
        self.screen_x_max = float(screen_x_max)
        self.screen_y_min = float(screen_y_min)
        self.screen_y_max = float(screen_y_max)
        
        #These bounds are used in testing to prevent the robot from touching the screen's edge
        #Add margins when using auto calibration
        self.x_min = robot_x_min # + self.margin_mm
        self.x_max = robot_x_max # - self.margin_mm
        self.y_min = robot_y_min # + self.margin_mm
        self.y_max = robot_y_max # - self.margin_mm

    #Uses linear interpolation to calculate expected touchscreen coordinates of the physical stylus
    def expected_touch_conversion(self, robot_x, robot_y):
        robot_x = float(robot_x)
        robot_y = float(robot_y)

        expected_x = self.screen_x_min + ((robot_x - self.robot_x_min) / (self.robot_x_max - self.robot_x_min)) * (self.screen_x_max - self.screen_x_min)
        expected_y = self.screen_y_min + ((robot_y - self.robot_y_min) / (self.robot_y_max - self.robot_y_min)) * (self.screen_y_max - self.screen_y_min)
        
        return expected_x, expected_y


class CalibrationRunner:
    def __init__(self, grbl, force_logger=None, touch_logger=None):
        self.grbl = grbl
        self.force_logger = force_logger
        self.touch_logger = touch_logger

        self.calibration = ScreenCalibration()

    #Allows user to manually jog X/Y position before logging robot position
    def wait_for_confirmed_position(self, step_name):
        self.touch_logger.confirm_pressed = False

        self.touch_logger.set_status(
            "Calibrating",
            [
                step_name,
                "Arrow keys: Jog X/Y",
                "Press 'Enter' to confirm"
            ]
        )

        while not self.touch_logger.confirm_pressed:
            QApplication.processEvents()
            time.sleep(0.01)

        position = get_position(self.grbl).copy()

        self.touch_logger.confirm_pressed = False

        print(f"{step_name}: {position}")

        return position
    
    #Returns the timestamp of most recent stored touch
    def get_current_touch_time(self):
        touch = self.touch_logger.get_latest_touch()

        if touch is None:
            return None
        
        return touch.get("timestamp")

    #Waits for a touch event with a timestamp different from the event previous of the stylus lowering
    def wait_for_new_touch(self, previous_timestamp, timeout = TOUCH_TIMEOUT):
        start_time = time.time()

        while time.time() - start_time < timeout:
            QApplication.processEvents()

            touch = self.touch_logger.get_latest_touch()

            if touch is not None:
                timestamp = touch.get("timestamp")

                if timestamp != previous_timestamp:
                    if touch.get("x") is None or touch.get("y") is None:
                        raise RuntimeError("Touch event did not contain X/Y coordinates.")
                    
                    return touch.copy()
                
            time.sleep(0.01)

        raise RuntimeError("Timed out waiting for a new touchscreen event.")
    
    #Raises Z after a press
    def retract(self, position):
        approach(
            grbl = self.grbl,
            x = position["x"],
            y = position["y"],
            safe_z = CAL_SAFE_Z,
            xy_feedrate = CAL_XY_FEEDRATE,
            z_feedrate = CAL_Z_FEEDRATE
        )

        self.grbl.wait_until_idle(timeout = 10.0)

    #Records touchscreen coordinate at manually set bound by lowering stylus to target force
    def measure_bound(self, step_name):
        while True:
            robot_position = self.wait_for_confirmed_position(step_name)

            timestamp = self.get_current_touch_time()

            self.touch_logger.set_status(
                "Calibrating",
                [
                    f"{step_name} confirmed",
                    "Lowering stylus...",
                ]
            )

            try:
                press_until_force(
                    grbl = self.grbl,
                    force_logger = self.force_logger,
                    target_force = CAL_TARGET_FORCE,
                    z_step = CAL_Z_STEP,
                    z_feedrate = CAL_Z_FEEDRATE
                )

                touch = self.wait_for_new_touch(previous_timestamp = timestamp)

                print(
                    f"{step_name} touch: "
                    f"X = {touch['x']}, "
                    f"Y = {touch['y']}"
                )

                return{
                    "robot": robot_position,
                    "touch": touch
                }
            
            except RuntimeError as error:
                if "Timed out waiting for a new touchscreen event." not in str(error):
                    raise

                print(f"{step_name} failed: {error}")

                self.touch_logger.set_status(
                    "Calibrating",
                    [
                        "No touch was detected.",
                        "Move to a nearby point and press Enter to retry."
                    ]
                )
            
            finally:
                self.retract(robot_position)

            #Waits for user to acknowledge touch failure before restarting loop
            self.touch_logger.confirm_pressed = False

            while not self.touch_logger.confirm_pressed:
                QApplication.processEvents()
                time.sleep(0.01)

            self.touch_logger.confirm_pressed = False
            

    def run(self):
        print("Starting manual screen calibration...")
        
        self.touch_logger.confirm_pressed = False

        self.touch_logger.set_status(
            "Calibrating",
            [
                "Raise Z to safe height",
                "Page up/down: Jog Z",
                "Press 'Enter' to confirm"
            ]
        )

        while not self.touch_logger.confirm_pressed:
            QApplication.processEvents()
            time.sleep(0.01)

        self.grbl.set_z_origin()
        self.calibration.safe_z = CAL_SAFE_Z

        self.touch_logger.confirm_pressed = False

        left = self.measure_bound("Set left bound")

        right = self.measure_bound("Set right bound")

        bottom = self.measure_bound("Set bottom bound")

        top = self.measure_bound("Set top bound")

        print(left)
        print(right)
        print(bottom)
        print(top)

        self.calibration.set_bounds(
            robot_x_min = left["robot"]["x"],
            robot_x_max = right["robot"]["x"],
            robot_y_min = bottom["robot"]["y"],
            robot_y_max = top["robot"]["y"],

            screen_x_min = left["touch"]["x"],
            screen_x_max = right["touch"]["x"],
            screen_y_min = bottom["touch"]["y"],
            screen_y_max = top["touch"]["y"]
        )

        print("Calibration complete.")
        print(f"Robot X range: {self.calibration.robot_x_min:.2f} to {self.calibration.robot_x_max:.2f}")
        print(f"Robot Y range: {self.calibration.robot_y_min:.2f} to {self.calibration.robot_y_max:.2f}")
        print(f"Screen X range: {self.calibration.screen_x_min:.2f} to {self.calibration.screen_x_max:.2f}")
        print(f"Screen Y range: {self.calibration.screen_y_min:.2f} to {self.calibration.screen_y_max:.2f}")

        return self.calibration
