import RPi.GPIO as GPIO # type: ignore
import adafruit_tsl2561, adafruit_dht, adafruit_bh1750, adafruit_ltr390
import cv2
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
DHT_PIN = board.D25
RE_CAMERA = 23
RGN_CAMERA = 24
WHITE_LIGHT = 17
UV_LIGHT = 22
IR_LIGHT = 27
START_BTN = 5
STOP_BTN = 6
DIR_SWITCH = 16

# Pin definition
GPIO.setmode(GPIO.BCM)
GPIO.setup(RE_CAMERA, GPIO.OUT)
GPIO.setup(RGN_CAMERA, GPIO.OUT)
GPIO.setup(WHITE_LIGHT, GPIO.OUT)
GPIO.setup(UV_LIGHT, GPIO.OUT)
GPIO.setup(IR_LIGHT, GPIO.OUT)
GPIO.setup(START_BTN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(STOP_BTN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(DIR_SWITCH, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Constants
CAM_RGB_INDEX = 0
CAM_SRC_RE = "/media/rpi4sise1/0000-0001/DCIM/Photo"
CAM_SRC_RGN = "/media/rpi4sise1/0000-00011/DCIM/Photo"
CAM_DEST = "/home/rpi4sise1/Desktop/pictures"
DXL_DEVICENAME = '/dev/ttyAMA0'
DXL_BAUDRATE = 1_000_000
DXL_ID = 1
DXL_SPEED = 50
MOTOR_STEPS = 11
MOTOR_STEP_TIME = 1.5
ANGLES = [round(i * (300 / (MOTOR_STEPS - 1))) for i in range(MOTOR_STEPS)]
SENSOR_READ_TIME = 0.5
CAMERA_FPS = 15
API_PORT = int(os.getenv("API_PORT", "8000"))


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
    "direction": 0
}

# Time variables
rotation_start_time = 0
sensor_read_time = 0

# Camera thread
frame_lock = threading.Lock()
stop_event = threading.Event()
current_frame = None

# Thread functions
def start_api():
    app.run(host="0.0.0.0", port=API_PORT, debug=False, use_reloader=False)

def generate_frames():
    while not stop_event.is_set():
        with frame_lock:
            ret, frame = rgb_camera.read()
        if not ret: continue
        _, buffer = cv2.imencode('.jpg', frame)
        yield (
            b'--frame\r\n'
            b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n'
        )

# API endpoints
@app.route("/dashboard")
def serve_dashboard():
    return data

@app.route("/dashboard/<string:key>", methods=["POST"])
def update_dashboard_var(key):
    try:
        value = float(request.args.get("value", 0))
    except ValueError:
        return {"error": "Invalid value"}, 400

    if key in data:
        data[key] = value
        return {key: data[key]}
    return {"error": f"{key} not found"}, 404

@app.route("/video")
def serve_video():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

# Functions
def save_rgb_image(frame: bytes):
    """Save RGB image to disk"""
    filename = f"RGB-{time.strftime('%Y%m%d-%H%M%S')}.png"
    with open(f"{CAM_DEST}/{filename}", "wb") as file:
        file.write(frame)

def degree_to_byte(degree: int) -> int:
    """Convert degree to byte value for AX-12 motor"""
    return min(max(degree * 1023 // 300, 0), 1023)

def debounce_button(pin: int, old_state: bool) -> bool:
    """Debounce button press"""
    if GPIO.input(pin) != old_state:
        time.sleep(0.05)
        return GPIO.input(pin)
    return old_state

def main():
    global start, stop, angle_index, rotated, transferred, rotation_start_time, sensor_read_time

    # Read sensors
    if time.time() - sensor_read_time > SENSOR_READ_TIME:
        try:
            dht.measure()
        except RuntimeError as e:
            print(f"DHT Sensor error: {e}")
        data["temp"] = dht.temperature
        data["hum"] = dht.humidity
        data["white_lux"] = bh.lux
        data["ir_lux"] = tsl.infrared
        data["uv_lux"] = ltr.uvi
        sensor_read_time = time.time()
    
    new_start = debounce_button(START_BTN, start)
    new_stop = debounce_button(STOP_BTN, stop)

    # Update running state
    if data["running"]:
        data["running"] = not (new_stop and not stop)
    else:
        data["running"] = new_start and not start

    if data["running"]:
        if rotated:
            # Move to the next angle
            angle = ANGLES[angle_index]
            dxl.set_goal_position(degree_to_byte(angle))
            rotation_start_time = time.time()
            rotated = False

        if time.time() - rotation_start_time > MOTOR_STEP_TIME:
            # Capture images with the white LEDs and RGB camera
            GPIO.output(WHITE_LIGHT, GPIO.HIGH)
            GPIO.output(UV_LIGHT, GPIO.LOW)
            GPIO.output(IR_LIGHT, GPIO.LOW)
            with frame_lock:
                ret, frame = rgb_camera.read()
            if ret:
                _, buffer = cv2.imencode('.jpg', frame)
                with open(f"{CAM_DEST}/RGB-{time.time()}.jpg", "wb") as file:
                    file.write(buffer.tobytes())
                
            frame_lock.acquire()
            if current_frame is not None:
                save_rgb_image(current_frame)
            frame_lock.release()

            # Capture images with the IR LEDs and RE camera
            GPIO.output(WHITE_LIGHT, GPIO.LOW)
            GPIO.output(UV_LIGHT, GPIO.LOW)
            GPIO.output(IR_LIGHT, GPIO.HIGH)
            re_camera.read()
            
            # Capture images with the UV LEDs and RNG camera
            GPIO.output(WHITE_LIGHT, GPIO.LOW)
            GPIO.output(UV_LIGHT, GPIO.LOW)
            GPIO.output(IR_LIGHT, GPIO.HIGH)
            rgn_camera.read()

            rotated = True
            transferred = False
            angle_index += 1
            
    if not transferred and (angle_index >= MOTOR_STEPS or not data["running"]):
        re_camera.toggle_mount()
        rgn_camera.toggle_mount()

        re_camera.transfer_n(angle_index, ANGLES)
        re_camera.clear_sd()
        rgn_camera.transfer_n(angle_index, ANGLES)
        rgn_camera.clear_sd()

        re_camera.toggle_mount()
        rgn_camera.toggle_mount()
        angle_index = 0
        transferred = True
        data["running"] = False

    # Update states
    start = new_start
    stop = new_stop

if __name__ == "__main__":
    api_thread = threading.Thread(target=start_api, daemon=True)
    try:
        api_thread.start()
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
        GPIO.cleanup()