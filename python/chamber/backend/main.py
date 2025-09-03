import digitalio
import adafruit_tsl2561, adafruit_dht, adafruit_bh1750, adafruit_ltr390
import cv2
from cv2.typing import MatLike
from flask import Flask, Response, request, jsonify
import threading
from modules.survey3 import Survey3
from modules.ax12 import Ax12
import busio
import board
import time
from dotenv import load_dotenv
import os
import base64
from collections import defaultdict

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
#CAM_RGB_TOPVIEW = 1 # Cámara web top view
CAM_SRC_RGN = "/media/sise/0000-0001/DCIM/Photo"
CAM_SRC_RE = "/media/sise/0000-00011/DCIM/Photo"
CAM_DEST = "/home/sise/Desktop/pictures" # Donde se guardan las fotos RGN y RE
DXL_DEVICENAME = '/dev/ttyAMA0'
DXL_BAUDRATE = 1_000_000
DXL_ID = 1
DXL_SPEED = 50 # Velocidad en la que gira el motor
MOTOR_STEPS = 11 # En cuantos angulos se va a detener el motor para tomar la foto
MOTOR_STEP_TIME = 2 # Cuanto tiempo se demora en cambiar de angulo
MOTOR_RESET_TIME = 10 # Cuanto tiempo se demora en ir desde el ultimo angulo hasta el primero
ANGLES = [round(i * (300 / (MOTOR_STEPS - 1))) for i in range(MOTOR_STEPS)]
SENSOR_READ_TIME = 1 # Cada cuanto se actualiza el valor de los sensores
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
start = False # Estado del boton de start
stop = False # Estado del boton de stop
angle_index = 0 # Ultimo angulo ordenado al motor
rotated = True # Si el motor ya llegó a su angulo destino y tomó las fotos
transferred = True # Si el motor ha tomado fotos nuevas desde la ultima vez que las transfirio
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
bogos_binted_w = 0 # Numero de fotos tomadas con la RGB
bogos_binted_i = 0 # Numero de fotos tomadas con la RE
bogos_binted_u = 0 # Numero de fotos tomadas con la RGN

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
    """Start the Flask API server in a separate thread. El frontend redirige las peticiones de los datos acá."""
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
            data["white_lux"] = round(bh.lux, 1)
            data["ir_lux"] = round(tsl.infrared, 1)
            data["uv_lux"] = round(ltr.uvi,1)
        time.sleep(SENSOR_READ_TIME)

# API endpoints
@app.route("/dashboard")
def serve_dashboard():
    """Serve the current dashboard data. Retorna todas las variables de los sensores y actuadores
    Returns:
        dict: The current dashboard data.
    """
    with data_lock:
        return data

@app.route("/dashboard/<string:key>", methods=["POST"])
def update_dashboard_var(key):
    """Update a dashboard variable with a new value. Retorna una sola variable
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
    """Serve the video stream from the RGB camera. Retorna el video en vivo de 1 camara RGB
        Si se añade otra camara toca copiar y renombrar todas las funciones usadas o que alguien lo parametrice
    """
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route("/dashboard/photos")
def serve_photos():
    """Retorna todas las fotos tomadas"""
    photos_dir = CAM_DEST

    # Define the limits per category
    category_limits = {
        "RGB": bogos_binted_w,
        "RGN": bogos_binted_u,
        "RE": bogos_binted_i
    }

    # Store photos per category
    categorized_files = defaultdict(list)

    try:
        # Filter only image files
        files = [f for f in os.listdir(photos_dir) if f.lower().endswith((".jpg", ".jpeg", ".png"))]

        # Categorize and sort by timestamp
        for f in files:
            parts = f.split("-")
            if len(parts) < 3:
                continue  # Skip bad format

            category = parts[0].upper()
            timestamp = parts[1] + "-" + parts[2]
            if category in category_limits:
                # Use timestamp as sort key
                categorized_files[category].append((timestamp, f))

        # Prepare payload
        photos_payload = []

        for category, items in categorized_files.items():
            # Sort by timestamp (descending) and take the last N
            items = sorted(items, key=lambda x: x[0], reverse=True)[:category_limits[category]]

            for _, file in items:
                full_path = os.path.join(photos_dir, file)
                with open(full_path, "rb") as image_file:
                    encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
                photos_payload.append({
                    "filename": file,
                    "content": encoded_string,
                    "content_type": "image/jpeg" if file.lower().endswith(".jpg") else "image/png"
                })

        response = {
            "photo_counts": category_limits,
            "photos": photos_payload
        }

        return jsonify(response)

    except Exception as e:
        return {"error": str(e)}, 500

# Functions
def save_rgb_image(frame: MatLike, timestamp: float, step=0):
    """Save the RGB image to the specified directory CAM_DEST with a timestamp and step number.
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
    global start, stop, angle_index, rotated, transferred, rotation_start_time, sensor_read_time, process_start, bogos_binted_w, bogos_binted_i, bogos_binted_u

    # Actualiza los botones START y STOP
    new_start = debounce_button(START_BTN, start)
    new_stop = debounce_button(STOP_BTN, stop)

    # Si se esta ejecutando para cuando se presione STOP y si esta parado empieza se presione START
    if data["running"]:
        data["running"] = not (new_stop and not stop)
    else:
        data["running"] = new_start and not start

    if data["running"]:
        # Si ya llego a su angulo destino, le ordena al motor el siguiente angulo 
        if rotated:
            print(f"Starting rotation at angle {ANGLES[angle_index]} degrees.")
            angle = ANGLES[angle_index]
            dxl.set_goal_position(degree_to_byte(angle))
            print(f"degree: {degree_to_byte(angle)}")
            rotation_start_time = time.time()
            rotated = False

            with data_lock:
                data["angle"] = angle
            # Si se va a regresar a la posicion inicial espera un rato
            if angle_index == 0:
                time.sleep(MOTOR_RESET_TIME)
                process_start = time.time()

        # Cuando ya pasa el tiempo de MOTOR_STEP_TIME desde que se ordeno el nuevo angulo, o sea cuando acaba de llegar
        if time.time() - rotation_start_time > MOTOR_STEP_TIME:
            print(f"Step {angle_index}/{MOTOR_STEPS} started.")

            with data_lock:
                data["progress"] = int((angle_index + 1*0.33) * 100 / MOTOR_STEPS)
            # Prende LEDs blancos y toma foto RGB, actualiza el contador RGB
            WHITE_LIGHT.value = True
            UV_LIGHT.value = False
            IR_LIGHT.value = False
            time.sleep(0.5)
            with frame_lock:
                ret, frame = rgb_camera.read()
            if ret:
                save_rgb_image(frame, process_start, angle_index)
                bogos_binted_w += 1

            with data_lock:
                data["progress"] = int((angle_index + 1*0.66) * 100 / MOTOR_STEPS)
            # Prende LEDs infrarojos y toma foto RE, actualiza el contador RE
            WHITE_LIGHT.value = False
            IR_LIGHT.value = True
            UV_LIGHT.value = False
            time.sleep(0.5)
            # re_camera.read()
            # bogos_binted_i += 1

            with data_lock:
                data["progress"] = int((angle_index + 1)*100/MOTOR_STEPS)
            # Prende LEDs uv y toma foto RGN, actualiza el contador RGN
            WHITE_LIGHT.value = False
            IR_LIGHT.value = False
            UV_LIGHT.value = True
            time.sleep(0.5)
            rgn_camera.read()
            bogos_binted_u += 1

            # Ya tomó las fotos y que hay fotos sin transferir
            rotated = True
            transferred = False
            angle_index += 1

            IR_LIGHT.value = False
            UV_LIGHT.value = False
            WHITE_LIGHT.value = False

    # Si hay fotos sin transferir y si, o ya llegó al final o se detuvo manualmente, entonces transfiere las imagenes
    if not transferred and (angle_index >= MOTOR_STEPS or not data["running"]):
        print(f"Transferring {angle_index} images.")
        # Desmonta la SD de las multiespectrales
        # re_camera.toggle_mount()
        rgn_camera.toggle_mount()  

        # Transfiere las ultimas fotos tomadas
        # re_camera.transfer_n(angle_index, ANGLES, process_start)
        # re_camera.clear_sd()
        rgn_camera.transfer_n(angle_index, ANGLES, process_start)
        rgn_camera.clear_sd()

        # Vuelve a montar las SD
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
