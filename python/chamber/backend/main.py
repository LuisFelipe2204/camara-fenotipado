"""Main module of the system"""

import base64
import logging
import os
import threading
import time

import adafruit_bh1750
import adafruit_dht
import adafruit_ltr390
import adafruit_tsl2561
import board
import busio
import cv2
import digitalio
from cv2.typing import MatLike
from dotenv import load_dotenv
from flask import Flask, Response, jsonify, request

from modules.ax12 import Ax12
from modules.survey3 import Survey3
from utils.CameraThread import CameraThread

load_dotenv()

logging.basicConfig(
    format=(
        "\033[90m%(asctime)s\033[0m "
        + "[\033[36m%(levelname)s\033[0m] "
        + "[\033[33m%(module)s::%(funcName)s\033[0m] "
        + "%(message)s"
    ),
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO,
    handlers=[logging.StreamHandler()],
)

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
CAM_RGBT_INDEX = 2
CAM_SRC_RGN = "/media/sise/0000-0001/DCIM/Photo"
CAM_SRC_RE = "/media/sise/0000-00011/DCIM/Photo"
CAM_DEST = "/home/sise/Desktop/pictures"
DXL_DEVICENAME = "/dev/ttyAMA0"
DXL_BAUDRATE = 1_000_000
DXL_ID = 1
DXL_SPEED = 50
MOTOR_STEPS = 11
MOTOR_STEP_TIME = 2
MOTOR_RESET_TIME = 10
ANGLES = [round(i * (300 / (MOTOR_STEPS - 1))) for i in range(MOTOR_STEPS)]
SENSOR_READ_TIME = 1
TOTAL_CAMERAS = 4
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
try:
    tsl = adafruit_tsl2561.TSL2561(i2c)
except ValueError:
    logging.warning("Sensor TSL2561 not recognized in I2C bus.")
    tsl = None
try:
    bh = adafruit_bh1750.BH1750(i2c)
except ValueError:
    logging.warning("Sensor BH1750 not recognized in I2C bus.")
    bh = None
try:
    ltr = adafruit_ltr390.LTR390(i2c)
except ValueError:
    logging.warning("Sensor LTR390 not recognized in I2C bus.")
    ltr = None
stop_event = threading.Event()
rgb_camera = CameraThread(CAM_RGB_INDEX, stop_event)
rgbt_camera = CameraThread(CAM_RGBT_INDEX, stop_event)
preview_cameras = [rgb_camera, rgbt_camera]
re_camera = Survey3(RE_CAMERA, "RE", CAM_SRC_RE, CAM_DEST)
rgn_camera = Survey3(RGN_CAMERA, "RGN", CAM_SRC_RGN, CAM_DEST)

app = Flask(__name__)

# Variables
states = {
    "start": False,
    "stop": False,
    "rotated": True,
    "transferred": True,
    "angle": 0,
}
data = {
    "temp": 0,
    "hum": 0,
    "white_lux": 0,
    "ir_lux": 0,
    "uv_lux": 0,
    "running": False,
    "angle": 0,
    "progress": 0,
}
photos_taken = {"side": 0, "top": 0, "ir": 0, "uv": 0}

# Time variables
times = {"rotation_start": 0.0, "sensor_read": 0.0, "process_start": 0.0}


# Sensor thread
data_lock = threading.Lock()


# Thread functions
def start_api():
    """Start the Flask API server in a separate thread."""
    app.run(host="0.0.0.0", port=API_PORT, debug=False, use_reloader=False)


def generate_frames(camera_thread: CameraThread):
    """Constantly triggers the camera to get the latest frames and formats it for streaming.
    Args:
        camera_thread: The camera object configured to manage an RGB camera
    Returns:
        The HTTP streaming formatted frame
    """
    while not stop_event.is_set():
        frame = camera_thread.get_frame()
        if frame is None:
            time.sleep(0.01)
            continue

        success, buffer = cv2.imencode(".jpg", frame)  # pylint: disable=no-member
        if not success:
            logging.error(
                "Camera %d failed during image encoding.", camera_thread.device_index
            )
            continue

        frame_bytes = buffer.tobytes()
        yield (
            b"--frame\r\n" b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
        )
        time.sleep(1.0 / camera_thread.fps)


def read_sensor_data():
    """Read data from the sensors and update the global data dictionary."""
    while not stop_event.is_set():
        try:
            dht.measure()
        except RuntimeError as e:
            logging.error("Failed while reading DHT. %s", e)

        with data_lock:
            data["temp"] = dht.temperature
            data["hum"] = dht.humidity
            data["white_lux"] = round(bh.lux, 1) if bh is not None else -1
            data["ir_lux"] = round(tsl.infrared, 1) if tsl is not None else -1
            data["uv_lux"] = round(ltr.uvi, 1) if ltr is not None else -1
        time.sleep(SENSOR_READ_TIME)


# Functions
def save_rgb_image(prefix: str, frame: MatLike, timestamp: float, step=0):
    """Save the RGB image to the specified directory with a timestamp and step number.
    Args:
        prefix: The label of the image to identify the camera
        frame: The image frame to save.
        timestamp: The timestamp to use for the filename.
        step: The step number for the filename. Defaults to 0.
    """
    filename = f"{prefix}-{time.strftime('%Y%m%d-%H%M%S', time.localtime(timestamp))}-{step}.png"
    cv2.imwrite(os.path.join(CAM_DEST, filename), frame)  # pylint: disable=no-member


def extract_photo_name(name: str):
    """Extract data from the image names created in save_rgb_image function.
    Args:
        name: The file name
    """
    label, date, hour, end = name.split("-")
    step, extension = end.split(".")
    return (label, f"{date}-{hour}", step, extension)


def insert_array_padded(array: list, index: int, item) -> list:
    """Inserts an item in a list in any position, padding with None if out of range.
    Args:
        array: The list to modify
        index: The position to insert the item on
        item: The item to put on the list
    Returns
        The modified list
    """
    if index >= len(array):
        array.extend([None] * (index + 1 - len(array)))
    array[index] = item
    return array


def degree_to_byte(degree: int) -> int:
    """Convert a degree value to a byte value for the servo motor.
    Args:
        degree: The degree value to convert.
    Returns:
        The converted byte value, clamped between 0 and 1023.
    """
    return min(max(degree * 1023 // 300, 0), 1023)


def debounce_button(digital_pin: digitalio.DigitalInOut, old_state: bool) -> bool:
    """Debounce a button press to avoid false triggers.
    Args:
        pin: The pin connected to the button.
        old_state: The previous state of the button.
    Returns:
        The new state of the button if it has changed, otherwise returns the old state.
    """
    if digital_pin.value != old_state:
        time.sleep(0.05)
        return digital_pin.value
    return old_state


def update_progress(angle_index: int, prev_camera: int):
    """Returns the current progress made based on number of steps and cameras
    Args:
        angle_index: The index of the current angle of the motor
        prev_camera: The number of the camera that took the last photo
    """
    with data_lock:
        data["progress"] = round((
            (angle_index / MOTOR_STEPS) + (prev_camera / TOTAL_CAMERAS) / MOTOR_STEPS
        ) * 100)
        logging.info("Changed progress to %d%", data["progress"])


def toggle_lights(state_white: bool, state_ir: bool, state_uv: bool):
    """Toggle the state of all the lights
    Args:
        state_white: The new state of the white LEDs
        state_ir: The new state of the infrarred LEDs
        state_uv: The new state of the ultravioled LEDs
    """
    WHITE_LIGHT.value = state_white
    IR_LIGHT.value = state_ir
    UV_LIGHT.value = state_uv
    time.sleep(0.1)


def transfer_survey_cameras(camera: Survey3):
    """Run the transfer protocol for the Survey3 cameras
    Args:
        camera: The camera object from Survey3 module
    """
    camera.toggle_mount()
    camera.transfer_n(states["angle"], ANGLES, times["process_start"])
    camera.clear_sd()
    camera.toggle_mount()


# API endpoints
@app.route("/dashboard")
def serve_dashboard():
    """Serve the current dashboard data.
    Returns:
        dict: The current dashboard data.
    """
    with data_lock:
        return jsonify(data)


@app.route("/dashboard/<string:key>", methods=["POST"])
def update_dashboard_var(key: str):
    """Update a dashboard variable with a new value.
    Args:
        key: The key of the variable to update.
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


@app.route("/video/<int:index>")
def serve_video(index):
    """Get the connection for generated frames
    Args:
        index: The camera index
    Returns:
        The generator wrapped in a HTTP response
    """
    if index >= len(preview_cameras) or index < 0:
        return Response()

    server = preview_cameras[index]
    return Response(
        generate_frames(server),
        mimetype="multipart/x-mixed-replace; boundary=frame",
    )


@app.route("/dashboard/photos")
def serve_photos():
    """Get all the photos taken on the last execution
    Returns:
        dict: All the photo contents stored by all cameras
    """
    photos_dir = CAM_DEST
    formats = (".jpg", ".jpeg", ".png")
    limits = {
        "RGBT": photos_taken["top"],
        "RGB": photos_taken["side"],
        "RGN": photos_taken["uv"],
        "RE": photos_taken["ir"],
    }
    photos = {
        "RGBT": [],
        "RGB": [],
        "RGN": [],
        "RE": [],
    }

    # Get all image files and sort them newest to oldest
    files = [file for file in os.listdir(photos_dir) if file.lower().endswith(formats)]
    files.sort(
        key=lambda file: os.path.getctime(os.path.join(photos_dir, file)), reverse=True
    )

    if len(files) == 0:
        logging.error("Tried serving photos via API but there's none stored.")
        return jsonify({"photo_counts": limits, "photos": photos})

    latest_timestamp = extract_photo_name(files[0])[1]
    logging.debug(
        "Latest timestamp found is [%s]. Found %d files.", latest_timestamp, len(files)
    )
    for file in files:
        label, timestamp, step, ext = extract_photo_name(file)
        if timestamp != latest_timestamp:
            continue

        if label not in photos:
            logging.warning("Found a file with an unrecognized label: %s", file)
            continue

        full_path = os.path.join(photos_dir, file)
        with open(full_path, "rb") as image_file:
            content = base64.b64encode(image_file.read()).decode("utf-8")
        insert_array_padded(
            photos[label],
            int(step),
            {
                "filename": file,
                "content": content,
                "content_type": "image/jpeg" if ext == "jpg" else "image/png",
            },
        )

    return jsonify({"photo_counts": limits, "photos": photos})


def move_motor_next():
    """Order the motor to move to the next angle, update roation start time
    If it's moving to the starting position block the main thread and update starting time
    """
    angle = ANGLES[states["angle"]]
    logging.info(
        "Began moving towards %d° (%d in bytes).", angle, degree_to_byte(angle)
    )
    dxl.set_goal_position(degree_to_byte(angle))
    with data_lock:
        data["angle"] = angle

    times["rotation_start"] = time.time()
    if states["angle"] == 0:
        time.sleep(MOTOR_RESET_TIME)  # Ensures the motor reaches starting position
        times["process_start"] = time.time()


def main():
    """Main function to handle the chamber operations."""
    new_start = debounce_button(START_BTN, states["start"])
    new_stop = debounce_button(STOP_BTN, states["stop"])

    if data["running"]:
        data["running"] = not (new_stop and not states["stop"])
    else:
        data["progress"] = 0
        data["running"] = new_start and not states["start"]

    if data["running"]:
        if states["rotated"]:
            move_motor_next()
            states["rotated"] = False  # Rotation just started so it hasn't finished yet

        if time.time() - times["rotation_start"] > MOTOR_STEP_TIME:
            logging.info("Step %d / %d started.", states["angle"], MOTOR_STEPS)

            toggle_lights(True, False, False)
            frame = rgb_camera.get_frame()
            photos_taken["side"] += 1
            if frame is not None:
                save_rgb_image("RGB", frame, times["process_start"], states["angle"])
            update_progress(states["angle"], 1)

            frame_top = rgbt_camera.get_frame()
            photos_taken["top"] += 1
            if frame_top is not None:
                save_rgb_image(
                    "RGBT", frame_top, times["process_start"], states["angle"]
                )
            update_progress(states["angle"], 2)

            toggle_lights(False, True, False)
            re_camera.read()
            photos_taken["ir"] += 1
            update_progress(states["angle"], 3)
            # At least one multispectral camera took a picture
            states["transferred"] = False

            toggle_lights(False, False, True)
            rgn_camera.read()
            photos_taken["uv"] += 1
            update_progress(states["angle"], 4)

            states["rotated"] = True
            states["angle"] += 1
            toggle_lights(False, False, False)

    completed_steps = states["angle"] >= MOTOR_STEPS
    if not states["transferred"] and (completed_steps or not data["running"]):
        logging.info("Began transferring %d images from the cameras.", states["angle"])

        # Transfer both multispectral cameras at the same time
        threads = [
            threading.Thread(target=transfer_survey_cameras, args=(cam,))
            for cam in (re_camera, rgn_camera)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        states["angle"] = 0
        states["transferred"] = True
        data["running"] = False

    # Update states
    states["start"] = new_start
    states["stop"] = new_stop


if __name__ == "__main__":
    api_thread = threading.Thread(target=start_api, daemon=True)
    sensor_thread = threading.Thread(target=read_sensor_data, daemon=True)
    try:
        api_thread.start()
        sensor_thread.start()
        rgb_camera.start()
        rgbt_camera.start()
        while True:
            main()
            time.sleep(0.1)
    except KeyboardInterrupt:
        logging.info("Exiting program.")
    finally:
        stop_event.set()
        rgb_camera.release()
        dxl.set_torque_enable(0)
        Ax12.disconnect()
        for pin in [RE_CAMERA, RGN_CAMERA, WHITE_LIGHT, UV_LIGHT, IR_LIGHT]:
            pin.value = False
