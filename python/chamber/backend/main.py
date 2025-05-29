import digitalio
import adafruit_tsl2561, adafruit_dht, adafruit_bh1750, adafruit_ltr390
import cv2
from cv2.typing import MatLike
from flask import Flask, Response, request
import threading
from modules.survey3 import Survey3
from modules.ax12 import Ax12
import busio
import board
import time
from dotenv import load_dotenv
import os

load_dotenv()

# Pin I/O
i2c = busio.I2C(board.SCL, board.SDA)
DHT_PIN = board.D26
RE_CAMERA = digitalio.DigitalInOut(board.D23)
RGN_CAMERA = digitalio.DigitalInOut(board.D24)
WHITE_LIGHT = digitalio.DigitalInOut(board.D17)
UV_LIGHT = digitalio.DigitalInOut(board.D22)
IR_LIGHT = digitalio.DigitalInOut(board.D27)
START_BTN = digitalio.DigitalInOut(board.D5)
STOP_BTN = digitalio.DigitalInOut(board.D6)

# Set directions
for pin in [RE_CAMERA, RGN_CAMERA, WHITE_LIGHT, UV_LIGHT, IR_LIGHT]:
    pin.direction = digitalio.Direction.OUTPUT
for pin in [START_BTN, STOP_BTN]:
    pin.direction = digitalio.Direction.INPUT
    pin.pull = digitalio.Pull.UP

# Constants
CAM_RGB_INDEX = 0
CAM_SRC_RGN = "/media/sise/0000-0001/DCIM/Photo"
CAM_SRC_RE = "/media/sise/0000-00011/DCIM/Photo"
CAM_DEST = "/home/sise/Desktop/pictures"
DXL_DEVICENAME = '/dev/ttyAMA0'
DXL_BAUDRATE = 1_000_000
DXL_ID = 1
DXL_SPEED = 50
MOTOR_STEPS = 11
MOTOR_STEP_TIME = 2
ANGLES = [round(i * (300 / (MOTOR_STEPS - 1))) for i in range(MOTOR_STEPS)]
SENSOR_READ_TIME = 0.5
CAMERA_FPS = 15
API_PORT = int(os.getenv("API_PORT", "5000"))

# Class configuration
Ax12.DEVICENAME = DXL_DEVICENAME
Ax12.BAUDRATE = DXL_BAUDRATE
Ax12.connect()

# Library initialization
dxl = Ax12(DXL_ID)
dxl.set_moving_speed(DXL_SPEED)
dxl.set_goal_position(0)
dht = adafruit_dht.DHT22(DHT_PIN, use_pulseio=False)
tsl = adafruit_tsl2561.TSL2561(i2c)
bh = adafruit_bh1750.BH1750(i2c)
ltr = adafruit_ltr390.LTR390(i2c)
rgb_camera = cv2.VideoCapture(CAM_RGB_INDEX)
re_camera = Survey3(RE_CAMERA, "RE", CAM_SRC_RE, CAM_DEST)
rgn_camera = Survey3(RGN_CAMERA, "RGN", CAM_SRC_RGN, CAM_DEST)

app = Flask(__name__)

# Variables
start = False
stop = False
angle_index = 0
rotated = True
transferred = True
data = {
    "temp": 0,
    "hum": 0,
    "white_lux": 0,
    "ir_lux": 0,
    "uv_lux": 0,
    "running": False,
    "direction": 0,
    "angle": 0,
    "progress": 0,
}

# Time variables
rotation_start_time = 0
sensor_read_time = 0
process_start = 0

# Camera thread
frame_lock = threading.Lock()
stop_event = threading.Event()
current_frame = None

# Sensor thread
data_lock = threading.Lock()

# Thread functions
def start_api():
    """Start the Flask API server in a separate thread."""
    app.run(host="0.0.0.0", port=API_PORT, debug=False, use_reloader=False)

def generate_frames():
    """Generate frames from the RGB camera for video streaming.
    Yields:
        bytes: The JPEG-encoded frame data.
    """
    while not stop_event.is_set():
        with frame_lock:
            ret, frame = rgb_camera.read()
        if not ret: continue
        _, buffer = cv2.imencode('.jpg', frame)
        yield (
            b'--frame\r\n'
            b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n'
        )

def read_sensor_data():
    """Read data from the sensors and update the global data dictionary."""
    global data_lock
    while not stop_event.is_set():
        try:
            dht.measure()
        except RuntimeError as e:
            print(f"DHT Sensor error: {e}")
        with data_lock:
            data["temp"] = dht.temperature
            data["hum"] = dht.humidity
            data["white_lux"] = bh.lux
            data["ir_lux"] = tsl.infrared
            data["uv_lux"] = ltr.uvi
        time.sleep(SENSOR_READ_TIME)

# API endpoints
@app.route("/dashboard")
def serve_dashboard():
    """Serve the current dashboard data.
    Returns:
        dict: The current dashboard data.
    """
    with data_lock:
        return data

@app.route("/dashboard/<string:key>", methods=["POST"])
def update_dashboard_var(key):
    """Update a dashboard variable with a new value.
    Args:
        key (str): The key of the variable to update.
    Returns:
        dict: The updated variable or an error message.
    """
    try:
        value = float(request.args.get("value", 0))
    except ValueError:
        return {"error": "Invalid value"}, 400

    if key in data:
        with data_lock:
            data[key] = value
            return {key: data[key]}
    return {"error": f"{key} not found"}, 404

@app.route("/video")
def serve_video():
    """Serve the video stream from the RGB camera."""
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

# Functions
def save_rgb_image(frame: MatLike, timestamp: float, step=0):
    """Save the RGB image to the specified directory with a timestamp and step number.
    Args:
        frame (MatLike): The image frame to save.
        timestamp (float): The timestamp to use for the filename.
        step (int, optional): The step number for the filename. Defaults to 0.
    """
    filename = f"RGB-{time.strftime('%Y%m%d-%H%M%S', time.localtime(timestamp))}-step{step}.png"
    cv2.imwrite(f"{CAM_DEST}/{filename}", frame)

def degree_to_byte(degree: int) -> int:
    """Convert a degree value to a byte value for the servo motor.
    Args:
        degree (int): The degree value to convert.
    Returns:
        int: The converted byte value, clamped between 0 and 1023.
    """
    return min(max(degree * 1023 // 300, 0), 1023)

def debounce_button(pin, old_state) -> bool:
    """Debounce a button press to avoid false triggers.
    Args:
        pin (DigitalInOut): The pin connected to the button.
        old_state (bool): The previous state of the button.
    Returns:
        bool: The new state of the button if it has changed, otherwise returns the old state.
    """
    if pin.value != old_state:
        time.sleep(0.05)
        return pin.value
    return old_state

def main():
    """Main function to handle the chamber operations.
    Reads sensor data, manages button states, controls the servo motor, and handles camera operations.
    """
    global start, stop, angle_index, rotated, transferred, rotation_start_time, sensor_read_time, process_start

    new_start = debounce_button(START_BTN, start)
    new_stop = debounce_button(STOP_BTN, stop)

    if data["running"]:
        data["running"] = not (new_stop and not stop)
    else:
        data["running"] = new_start and not start

    if data["running"]:
        if rotated:
            print(f"Starting rotation at angle {ANGLES[angle_index]} degrees.")
            angle = ANGLES[angle_index]
            dxl.set_goal_position(degree_to_byte(angle))
            rotation_start_time = time.time()
            rotated = False
            if angle_index == 0:
                process_start = time.time()
                time.sleep(5)

        if time.time() - rotation_start_time > MOTOR_STEP_TIME:
            print(f"Step {angle_index}/{MOTOR_STEPS} started.")
            WHITE_LIGHT.value = True
            UV_LIGHT.value = False
            IR_LIGHT.value = False
            time.sleep(0.5)
            with frame_lock:
                ret, frame = rgb_camera.read()
            if ret:
                save_rgb_image(frame, process_start, angle_index)

            WHITE_LIGHT.value = False
            IR_LIGHT.value = True
            UV_LIGHT.value = False
            time.sleep(0.5)
            # re_camera.read()

            WHITE_LIGHT.value = False
            IR_LIGHT.value = False
            UV_LIGHT.value = True
            time.sleep(0.5)
            rgn_camera.read()

            rotated = True
            transferred = False
            angle_index += 1

            IR_LIGHT.value = False
            UV_LIGHT.value = False
            WHITE_LIGHT.value = False

    if not transferred and (angle_index >= MOTOR_STEPS or not data["running"]):
        print(f"Transferring {angle_index} images.")
        # re_camera.toggle_mount()
        rgn_camera.toggle_mount()  

        # re_camera.transfer_n(angle_index, ANGLES, process_start)
        # re_camera.clear_sd()
        rgn_camera.transfer_n(angle_index, ANGLES, process_start)
        rgn_camera.clear_sd()

        # re_camera.toggle_mount()
        rgn_camera.toggle_mount()
        angle_index = 0
        transferred = True
        data["running"] = False

    # Update states
    start = new_start
    stop = new_stop

if __name__ == "__main__":
    api_thread = threading.Thread(target=start_api, daemon=True)
    sensor_thread = threading.Thread(target=read_sensor_data, daemon=True)
    try:
        api_thread.start()
        sensor_thread.start()
        while True:
            main()
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        stop_event.set()
        rgb_camera.release()
        dxl.set_torque_enable(0)
        Ax12.disconnect()
        for pin in [RE_CAMERA, RGN_CAMERA, WHITE_LIGHT, UV_LIGHT, IR_LIGHT]:
            pin.value = False