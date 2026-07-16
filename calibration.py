import time

from PyQt6.QtWidgets import QApplication

from motion_control.motion import get_position

class ScreenCalibration:
    def __init__(self):
        self.x_min = None
        self.x_max = None
        self.y_min = None
        self.y_max = None

        self.margin = 5.0 #in mm

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
        self.x_min = robot_x_min + self.margin_mm
        self.x_max = robot_x_max - self.margin_mm
        self.y_min = robot_y_min + self.margin_mm
        self.y_max = robot_y_max - self.margin_mm

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

        position = get_position(self.grbl)

        self.touch_logger.confirm_pressed = False

        print(f"{step_name}: {position}")

        return position

    def run(self):
        print("Starting manual screen calibration...")

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

        left = self.wait_for_confirmed_position("Set left bound")

        right = self.wait_for_confirmed_position("Set right bound")

        bottom = self.wait_for_confirmed_position("Set bottom bound")

        top = self.wait_for_confirmed_position("Set top bound")

        print(left)
        print(right)
        print(bottom)
        print(top)

        self.calibration.set_bounds(
            x_min = left["x"],
            x_max = right["x"],
            y_min = bottom["y"],
            y_max = top["y"]
        )

        print("Calibration complete.")
        print(f"X range: {self.calibration.x_min:.2f} to {self.calibration.x_max:.2f}")
        print(f"Y range: {self.calibration.y_min:.2f} to {self.calibration.y_max:.2f}")

        return self.calibration
