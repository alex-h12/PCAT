from PyQt6.QtCore import QThread, pyqtSignal

from motion_control.calibration import CalibrationRunner
from motion_control.tests import tap_test, swipe_test

class TestWorker(QThread):
    finished = pyqtSignal()

    def __init__(self, controller):
        super().__init__()
        self.controller = controller

    def run(self):
        calibration_runner = CalibrationRunner(
            grbl = self.controller.grbl,
            force_logger = self.controller.force_logger,
            touch_logger = self.controller.touch_logger
        )
        
        calibration = calibration_runner.run()
        self.controller.set_calibration(calibration)

        self.controller.touch_logger.set_status("Tap testing")

        tap_test(
            grbl = self.controller.grbl,
            force_logger = self.controller.force_logger,
            calibration = self.controller.calibration,
            controller = self.controller
        )

        self.controller.touch_logger.set_status("Swipe testing")

        swipe_test(
            grbl = self.controller.grbl,
            force_logger = self.controller.force_logger,
            calibration = self.controller.calibration,
            direction = "horizontal",
            controller = self.controller
        )

        swipe_test(
            grbl = self.controller.grbl,
            force_logger = self.controller.force_logger,
            calibration = self.controller.calibration,
            direction = "vertical",
            controller = self.controller
        )

        self.finished.emit()
