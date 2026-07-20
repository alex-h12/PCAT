import time
import serial

class GRBLController:
    def __init__(self, port: str, baudrate: int = 115200, timeout: float = 1.0):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.ser = None

    def connect(self):
        self.ser = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
        time.sleep(2)       # GRBL resets after serial connection

        self.ser.write(b"\r\n\r\n")

        time.sleep(2)
        self.ser.reset_input_buffer()

        print(f"Connected to GRBL on {self.port}")

    def disconnect(self):
        if self.ser and self.ser.is_open:
            self.ser.close()
            print("Disconnected from GRBL")

    def send_command(self, command: str, wait_for_ok: bool = True):
        if not self.ser or not self.ser.is_open:
            raise RuntimeError("GRBL is not connected")

        command = command.strip()
        print(f">> {command}")

        self.ser.write((command + "\n").encode())

        if wait_for_ok:
            return self._wait_for_response()

    def _wait_for_response(self):
        responses = []      #Store responses for troubleshooting

        while True:
            line = self.ser.readline().decode(errors="ignore").strip()

            if line:
                print(f"<< {line}")
                responses.append(line)

                if line == "ok":
                    return responses

                if line.startswith("error"):
                    raise RuntimeError(f"GRBL error: {line}")

    def unlock(self):
        self.send_command("$X")

    def home(self):
        self.send_command("$H")       #Only use if limit switches are installed

    def set_work_origin(self):
        self.send_command("G10 L20 P1 X0 Y0 Z0")

    def set_absolute_mode(self):
        self.send_command("G90")

    def set_relative_mode(self):
        self.send_command("G91")

    def set_units_mm(self):
        self.send_command("G21")

    def move_to(self, x=None, y=None, z=None, feedrate=200):
        parts = ["G1"]

        if x is not None:
            parts.append(f"X{x:.3f}")
        if y is not None:
            parts.append(f"Y{y:.3f}")
        if z is not None:
            parts.append(f"Z{z:.3f}")

        parts.append(f"F{feedrate}")

        self.send_command(" ".join(parts))

    def rapid_to(self, x=None, y=None, z=None):
        parts = ["G0"]

        if x is not None:
            parts.append(f"X{x:.3f}")
        if y is not None:
            parts.append(f"Y{y:.3f}")
        if z is not None:
            parts.append(f"Z{z:.3f}")

        self.send_command(" ".join(parts))

    def get_status(self):
        if not self.ser or not self.ser.is_open:
            raise RuntimeError("GRBL is not connected")

        self.ser.reset_input_buffer()
        self.ser.write(b"?")
        
        start = time.time()

        while time.time() - start < 2.0:
            line = self.ser.readline().decode(errors="ignore").strip()

            if line.startswith("<") and ("WPos:" in line or "MPos:" in line):
                return line
            
        raise RuntimeError("Timed out waiting for valid GRBL status.")

    def get_position(self):
        line = self.get_status()
        print("RAW STATUS: ", line)
        
        if "WPos:" in line:
            position = line.split("WPos:")[1].split("|")[0]
        elif "MPos:" in line:
            position = line.split("MPos:")[1].split("|")[0]
        else:
            return None   

        x, y, z = map(float, position.split(","))

        return {
            "x": x,
            "y": y,
            "z": z
        }
    
    def set_z_origin(self):
        self.send_command("G10 L20 P1 Z0")

    def wait_until_idle(self, timeout = 15.0):
        start_time = time.time()

        while time.time() - start_time < timeout:
            status = self.get_status()

            if status is None:
                time.sleep(0.02)
                continue

            if status.startswith("<Idle"):
                return

            if status.startswith("<Alarm"):
                raise RuntimeError(f"GRBL entered alarm state: {status}")

            time.sleep(0.02)

        raise RuntimeError("Timed out waiting for GRBL motion to complete.")

    def dwell(self, seconds: float):
        self.send_command(f"G4 P{seconds:.3f}")

if __name__ == "__main__":
    print("TESTING")
    grbl = GRBLController(port="COM5")      # Change to Arduino's port

    try:
        grbl.connect()

        grbl.unlock()
        grbl.home()       # Use with limit switches
        grbl.set_units_mm()
        grbl.set_absolute_mode()

        print("\nRunning XY motion test...")

        grbl.move_to(x=7, y=0, z=0, feedrate=200)
        grbl.dwell(0.5)
        grbl.move_to(x=7, y=4, z=0, feedrate=200)
        grbl.dwell(0.5)
        grbl.move_to(x=7, y=4, z=2, feedrate=200)
        grbl.dwell(0.5)
        grbl.move_to(x=0, y=4, z=2, feedrate=200)
        grbl.dwell(0.5)
        grbl.move_to(x=0, y=0, z=2, feedrate=200)
        grbl.dwell(0.5)
        grbl.move_to(x=0, y=0, z=0, feedrate=200)
        grbl.dwell(0.5)

    finally:
        grbl.disconnect()
