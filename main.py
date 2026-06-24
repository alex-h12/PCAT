import sys
import csv
import time
from pathlib import Path

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

from touch_logger import TouchLogger
from force_logger import ForceLogger
from grbl_controller import GRBLController

RESULTS_DIR = Path("data")
RESULTS_FILE = RESULTS_DIR / "touch_test_results.csv"

FORCE_PORT = "COM4"
GRBL_PORT = "COM5"

class MainController:
    def __init__(self):
        RESULTS_DIR.mkdir(exist_ok=True)

        self.touch_logger = TouchLogger()
        self.last_logged_touch = None

        self.force_logger = ForceLogger(port=FORCE_PORT)
        self.force_logger.connect()
        self.current_force = 0.0

        self.position_logger = GRBLController(port=GRBL_PORT)
        self.position_logger.connect()
        self.current_position = 0.0

        self.file = open(RESULTS_FILE, "w", newline="")
        self.writer = csv.writer(self.file)

        self.writer.writerow([
            "timestamp",
            "robot_x",
            "robot_y",
            "touch_event",
            "touch_x",
            "touch_y",
            "force",
            "error_x",
            "error_y"
        ])

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_system)
        self.timer.start(50)

    def update_system(self):
        robot_position = self.position_logger.update()
        
        touch_position = self.touch_logger.get_latest_touch()

        if touch_position is None:
            return

        if touch_position == self.last_logged_touch:
            return

        self.last_logged_touch = touch_position.copy()

        force_value = self.force_logger.update()

        if force_value is not None:
            self.current_force = force_value

        error_x = touch_position["x"] - robot_position["x"]
        error_y = touch_position["y"] - robot_position["y"]

        self.writer.writerow([
            time.time(),
            robot_position["x"],
            robot_position["y"],
            touch_position["event_type"],
            touch_position["x"],
            touch_position["y"],
            self.current_force,
            error_x,
            error_y
        ])

        self.file.flush()

        print(
            f"Robot=({robot['x']:.1f}, {robot['y']:.1f}) "
            f"Touch={touch['event_type']} "
            f"({touch['x']:.1f}, {touch['y']:.1f}) "
            f"Force={self.current_force:.2f} g "
            f"Error=({error_x:.1f}, {error_y:.1f})"
        )

    def close(self):
        self.force_logger.disconnect()
        self.file.close()

def main():
    app = QApplication(sys.argv)

    controller = MainController()

    try:
        exit_code = app.exec()
    finally:
        controller.close()

    sys.exit(exit_code)

if __name__ == "__main__":
    main()
