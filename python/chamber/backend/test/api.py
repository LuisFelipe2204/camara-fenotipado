import cv2
from flask import Flask, Response, request
import threading
import time
import random
from dotenv import load_dotenv
import os

load_dotenv()

# Constants
CAM_RGB_INDEX = 0
CAM_DEST = "/home/rpi4sise1/Desktop/pictures"
CAMERA_FPS = 15
API_PORT = int(os.getenv("API_PORT", "8000"))

# Library initialization
rgb_camera = cv2.VideoCapture(CAM_RGB_INDEX)
app = Flask(__name__)

# Variables
last_update = 0
last_picture = 0
data = {
    "temp": 0,
    "hum": 0,
    "white_lux": 0,
    "ir_lux": 0,
    "uv_lux": 0,
    "running": False
}

# Camera thread
frame_lock = threading.Lock()
stop_event = threading.Event()
current_frame: bytes = b""

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

def main():
    global last_update, last_picture

    if time.time() - last_update > 0.5:
        data["temp"] = round(random.uniform(10, 40), 1)
        data["hum"] = round(random.uniform(20, 100), 1)
        data["white_lux"] = round(random.uniform(0, 1000), 1)
        data["ir_lux"] = round(random.uniform(0, 1000), 1)
        data["uv_lux"] = round(random.uniform(0, 14), 1)
        last_update = time.time()
    
    if data["running"] and time.time() - last_picture > 2:
        with open(f"{CAM_DEST}/output-{time.time()}.jpg", "wb") as file:
            with frame_lock:
                ret, frame = rgb_camera.read()
            if not ret: return
            _, buffer = cv2.imencode('.jpg', frame)
            file.write(buffer.tobytes())
            print(f"Wrote to {CAM_DEST}/output-{time.time()}.jpg")
            last_picture = time.time()

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
        api_thread.join()