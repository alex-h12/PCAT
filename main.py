import sys
import csv
import time
import math
from pathlib import Path

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

from hardware_control.touch_logger import TouchLogger
from hardware_control.force_logger import ForceLogger
from hardware_control.grbl_controller import GRBLController

from motion_control.worker import TestWorker
from motion_control.motion import get_position

RESULTS_DIR = Path("data")
RESULTS_FILE = RESULTS_DIR / "touch_test_results.csv"

FORCE_PORT = "COM9"
GRBL_PORT = "COM5"
UPDATE_PERIOD = 50

class MainController:
    def __init__(self):
        RESULTS_DIR.mkdir(exist_ok=True)

        self.calibration = None
        self.worker = None

        self.force_logger = ForceLogger(port=FORCE_PORT)
        self.force_logger.connect()
        self.current_force = 0.0

        self.current_robot_position = {
            "x": 0.0,
            "y": 0.0,
            "z": 0.0
        }

        self.grbl = GRBLController(port=GRBL_PORT)
        self.grbl.connect()
        self.grbl.unlock()
        self.grbl.home()       # Use with limit switches
        self.grbl.set_work_origin()
        self.grbl.set_units_mm()
        self.grbl.set_absolute_mode()
        
        self.touch_logger = TouchLogger(grbl=self.grbl)
        self.last_logged_touch = None

        self.file = open(RESULTS_FILE, "w", newline="")
        self.writer = csv.writer(self.file)

        self.writer.writerow([
            "log_time",

            "robot_x",
            "robot_y",
            "robot_z",

            "expected_x",
            "expected_y",

            "touch_event",
            "touch_x",
            "touch_y",
            "touch_time",

            "force",
            
            "error_x",
            "error_y",
            "position_error"
        ])

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_system)
        self.timer.start(UPDATE_PERIOD)

    def set_robot_position(self, position):
        self.current_robot_position = position

    def set_calibration(self, calibration):
        self.calibration = calibration
        print("Calibration stored in MainController.")

    def start_worker(self):
        self.worker = TestWorker(self)
        self.worker.finished.connect(self.worker_finished)
        self.worker.start()

    def worker_finished(self):
        print("Testing complete.")

    def update_system(self):
        log_time = time.time()

        force = self.force_logger.get_latest_force()

        if force is not None:
            self.current_force = force
            self.touch_logger.set_force(force)

        touch = self.touch_logger.get_latest_touch()

        if touch is None:
            return

        if touch == self.last_logged_touch:
            return
        
        if self.calibration is None:
            return

        self.last_logged_touch = touch.copy()

        robot_position = self.current_robot_position
        
        if robot_position is None:
            return
        
        robot_x = robot_position["x"]
        robot_y = robot_position["y"]
        robot_z = robot_position["z"]

        expected_x, expected_y = self.calibration.expected_touch_conversion(robot_x, robot_y) #convert mm to pixels

        touch_event = touch["event_type"]
        touch_x = touch["x"]
        touch_y = touch["y"]
        touch_time = touch.get("timestamp", log_time)

        error_x = touch_x - expected_x
        error_y = touch_y - expected_y
        position_error = math.sqrt(error_x**2 + error_y**2)

        self.writer.writerow([
            log_time,

            robot_x,
            robot_y,
            robot_z,

            expected_x,
            expected_y,

            touch_event,
            touch_x,
            touch_y,
            touch_time,

            force,

            error_x,
            error_y,
            position_error,
        ])

        self.file.flush()

        print(
            f"Robot=({robot_x:.1f}, {robot_y:.1f}, {robot_z:.1f}) "
            f"Expected=({expected_x:.1f}, {expected_y:.1f})"
            f"Touch={touch_event} "
            f"({touch_x:.1f}, {touch_y:.1f}) "
            f"Force={force:.2f} g "
            f"Error=({error_x:.1f}, {error_y:.1f})"
        )

    def close(self):
        self.timer.stop()
        self.grbl.disconnect()
        self.force_logger.disconnect()
        self.file.close()

def main():
    app = QApplication(sys.argv)

    controller = MainController()

    QTimer.singleShot(1000, controller.start_worker)

    try:
        exit_code = app.exec()
    finally:
        controller.close()

    sys.exit(exit_code)

if __name__ == "__main__":
    main()
