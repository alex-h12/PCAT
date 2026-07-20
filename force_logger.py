import serial
import time

class ForceLogger:
    def __init__(self, port="COM9", baudrate=115200, timeout=0.05):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.ser = None

        self.latest_force = None
        self.last_update_time = None
        self.last_raw_line = None

    def connect(self):
        self.ser = serial.Serial(
            self.port,
            self.baudrate,
            timeout=self.timeout
        )

        time.sleep(2)
        self.ser.reset_input_buffer()

        print(f"Connected to force logger on {self.port}")

    def disconnect(self):
        if self.ser and self.ser.is_open:
            self.ser.close()
            print("Disconnected from force logger")

    def _parse_line(self, line):
        line = line.strip()

        if not line:
            return None

        try:
            value = float(line)
        except ValueError:
            print(f"Invalid force line: {line!r}")
            return None

        self.last_raw_line = line
        self.latest_force = value
        self.last_update_time = time.time()
        return value

    def update_force(self, drain_buffer=True):
        if not self.ser or not self.ser.is_open:
            raise RuntimeError("Force logger is not connected")

        latest_value = None

        raw = self.ser.readline().decode(errors="ignore")
        if raw:
            latest_value = self._parse_line(raw)

        if drain_buffer:
            while self.ser.in_waiting > 0:
                raw = self.ser.readline().decode(errors="ignore")
                if not raw:
                    break

                parsed = self._parse_line(raw)
                if parsed is not None:
                    latest_value = parsed

        return latest_value if latest_value is not None else self.latest_force

    def age_seconds(self):
        if self.last_update_time is None:
            return None
        return time.time() - self.last_update_time

    def is_stale(self, max_age=0.25):
        age = self.age_seconds()
        return age is None or age > max_age

if __name__ == "__main__":
    force = ForceLogger(port="COM9")

    try:
        force.connect()

        while True:
            value = force.update_force()

            if value is not None:
                print(f"Force: {value:.2f} g")

            time.sleep(0.05)

    except KeyboardInterrupt:
        print("Stopped force logger")

    finally:
        force.disconnect()
