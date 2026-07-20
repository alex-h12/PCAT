import sys
import time

from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtCore import Qt, QEvent
from PyQt6.QtGui import QPainter, QFont, QColor, QPen

from motion_control.motion import jog

JOG_XY_DISTANCE = 50
JOG_Z_DISTANCE = 0.2

class TouchLogger(QWidget):
    def __init__(
        self,
        grbl=None,
        print_enabled=False
    ):
        super().__init__()

        if __name__ == "__main__": 
            print_enabled = True

        self.grbl = grbl

        self.latest_touch = None
        self.latest_force = None

        self.status = "Idle"
        self.instructions = []

        self.confirm_pressed = False
        self.print_enabled = print_enabled

        self.overlay_points = []   # [{x,y,status,label}]
        self.overlay_lines = []    # [{x1,y1,x2,y2,status}]
        self.touch_trace = []      # [(x,y), ...]

        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setWindowTitle("Touch Logger")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_AcceptTouchEvents, True)
        self.setFocus()

        self.showFullScreen()

        if self.print_enabled:
            print("Touch the screen...")
            print("Press ESC to close")
    
    #Sets the testing status (calibrating, touch testing, etc.) and user instructions
    def set_status(self, status, instructions=None):
        self.status = status

        if instructions is None:
            self.instructions = []
        else:
            self.instructions = instructions

        self.update()
    
    #Sets force to be printed on window
    def set_force(self, force):
        self.latest_force = force
        self.update()

    def store_touch(self, event_type, point):
        pos = point.position()

        self.latest_touch = {
            "event_type": event_type,
            "x": pos.x(),
            "y": pos.y(),
            "timestamp": time.time()
        }

        if event_type in ("DOWN", "MOVE"):
            self.touch_trace.append((pos.x(), pos.y()))

        self.update()

        if self.print_enabled:
            print(
                f"{event_type} "
                f"X={pos.x():.1f} "
                f"Y={pos.y():.1f}"
            )

    def get_latest_touch(self):
        return self.latest_touch

    def event(self, event):
        if event.type() == QEvent.Type.TouchBegin:
            for point in event.points():
                self.store_touch("DOWN", point)
            return True

        elif event.type() == QEvent.Type.TouchUpdate:
            for point in event.points():
                self.store_touch("MOVE", point)
            return True

        elif event.type() == QEvent.Type.TouchEnd:
            for point in event.points():
                self.store_touch("UP", point)
            return True

        return super().event(event)

    def keyPressEvent(self, event):
        key = event.key()

        if key == Qt.Key.Key_Escape:
            self.close()
            return

        if key == Qt.Key.Key_Enter:
            self.confirm_pressed = True
            self.update()
            return

        if self.grbl is None:
            return

        if key == Qt.Key.Key_Left:
            jog(self.grbl, dx=-JOG_XY_DISTANCE)

        elif key == Qt.Key.Key_Right:
            jog(self.grbl, dx=JOG_XY_DISTANCE)

        elif key == Qt.Key.Key_Up:
            jog(self.grbl, dy=JOG_XY_DISTANCE)

        elif key == Qt.Key.Key_Down:
            jog(self.grbl, dy=-JOG_XY_DISTANCE)

        elif key == Qt.Key.Key_PageUp:
            jog(self.grbl, dz=-JOG_Z_DISTANCE)

        elif key == Qt.Key.Key_PageDown:
            jog(self.grbl, dz=JOG_Z_DISTANCE)

        else:
            return
        self.update()

    def clear_overlay(self):
        self.overlay_points.clear()
        self.overlay_lines.clear()
        self.touch_trace.clear()
        self.update()

    def add_overlay_point(self, x, y, status="pending", label=None):
        self.overlay_points.append({
            "x": x, "y": y, "status": status, "label": label
        })
        self.update()

    def set_last_point_status(self, status):
        if self.overlay_points:
            self.overlay_points[-1]["status"] = status
            self.update()

    def add_overlay_line(self, x1, y1, x2, y2, status="pending"):
        self.overlay_lines.append({
            "x1": x1, "y1": y1, "x2": x2, "y2": y2, "status": status
        })
        self.update()

    def set_last_line_status(self, status):
        if self.overlay_lines:
            self.overlay_lines[-1]["status"] = status
            self.update()

    def _status_color(self, status):
        if status == "pass":
            return QColor(0, 200, 0)
        if status == "fail":
            return QColor(220, 0, 0)
        return QColor(220, 180, 0)  # pending

    def paintEvent(self, event):
        painter = QPainter(self)

        font = QFont()
        font.setPointSize(20)
        painter.setFont(font)

        # Left side: live touch/force data
        painter.drawText(20, 40, "Press ESC to close")

        if self.latest_touch is None:
            painter.drawText(20, 75, "X = ---")
            painter.drawText(20, 110, "Y = ---")
        else:
            painter.drawText(20, 75, f"X = {self.latest_touch['x']:.1f}")
            painter.drawText(20, 110, f"Y = {self.latest_touch['y']:.1f}")

        if self.latest_force is None:
            painter.drawText(20, 145, "Force = --- g")
        else:
            painter.drawText(20, 145, f"Force = {self.latest_force:.2f} g")

        # Right side: current mode and instructions
        metrics = painter.fontMetrics()

        status = f"Status: {self.status}"
        x = self.width() - metrics.horizontalAdvance(status) - 20
        painter.drawText(x, 40, status)

        y = 75

        for line in self.instructions:
            x = self.width() - metrics.horizontalAdvance(line) - 20
            painter.drawText(x, y, line)
            y += 35

        # Draw expected swipe lines
        for item in self.overlay_lines:
            pen = QPen(self._status_color(item["status"]), 3)
            painter.setPen(pen)
            painter.drawLine(
                int(item["x1"]), int(item["y1"]),
                int(item["x2"]), int(item["y2"])
            )

        # Draw expected tap points
        for item in self.overlay_points:
            color = self._status_color(item["status"])
            painter.setPen(QPen(color, 2))
            painter.setBrush(color)
            r = 6
            painter.drawEllipse(int(item["x"] - r), int(item["y"] - r), 2*r, 2*r)

        # Draw actual touch trace (cyan)
        if len(self.touch_trace) > 1:
            painter.setPen(QPen(QColor(0, 200, 255), 2))
            for i in range(1, len(self.touch_trace)):
                x1, y1 = self.touch_trace[i - 1]
                x2, y2 = self.touch_trace[i]
                painter.drawLine(int(x1), int(y1), int(x2), int(y2))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TouchLogger(print_enabled=True)
    sys.exit(app.exec())
