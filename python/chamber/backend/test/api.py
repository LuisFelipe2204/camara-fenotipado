import cv2
from flask import Flask, Response, request, jsonify
import threading
import time
import random
from dotenv import load_dotenv
import os
import base64
from collections import defaultdict

load_dotenv()

# Constants
CAM_RGB_INDEX    = 0
CAM_RGB_TOP_INDEX= 2
CAM_DEST         = "./"
CAMERA_WIDTH     = 320
CAMERA_HEIGHT    = 240
CAMERA_FPS       = 10
API_PORT         = int(os.getenv("API_PORT", "5000"))

app = Flask(__name__)

# Shared data
data = {
    "temp":      0,
    "hum":       0,
    "white_lux": 0,
    "ir_lux":    0,
    "uv_lux":    0,
    "running":   False,
    "direction": 0,
    "angle":     0,
    "progress":  0,
}
bogos_binted_w = 0
bogos_binted_i = 0
bogos_binted_u = 0

data_lock = threading.Lock()
stop_event = threading.Event()

# Threaded camera capture
class CameraThread(threading.Thread):
    def __init__(self, device_index, width, height, fps):
        super().__init__(daemon=True)
        self.device_index = device_index
        self.width  = width
        self.height = height
        self.fps    = fps
        self.capture = cv2.VideoCapture(device_index)
        # set capture parameters
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH,  width)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self.capture.set(cv2.CAP_PROP_FOURCC,
                         cv2.VideoWriter_fourcc(*'MJPG'))
        self.capture.set(cv2.CAP_PROP_FPS, fps)
        self.lock   = threading.Lock()
        self.frame  = None

    def run(self):
        while not stop_event.is_set():
            ret, frm = self.capture.read()
            if not ret or frm is None or frm.size == 0:
                # log once maybe
                print(f"[WARN] Camera {self.device_index} read failed (ret={ret})")
                time.sleep(0.1)
                continue
            with self.lock:
                self.frame = frm.copy()
            # limit the rate
            time.sleep(1.0 / self.fps)

    def get_frame(self):
        with self.lock:
            if self.frame is None:
                return None
            return self.frame.copy()

    def release(self):
        self.capture.release()


# Create two camera threads
cam0_thread = CameraThread(CAM_RGB_INDEX,     CAMERA_WIDTH, CAMERA_HEIGHT, CAMERA_FPS)
cam1_thread = CameraThread(CAM_RGB_TOP_INDEX, CAMERA_WIDTH, CAMERA_HEIGHT, CAMERA_FPS)

cam0_thread.start()
cam1_thread.start()

def generate_frames(camera_thread: CameraThread):
    while not stop_event.is_set():
        frame = camera_thread.get_frame()
        if frame is None:
            # no frame yet
            time.sleep(0.01)
            continue
        success, buffer = cv2.imencode('.jpg', frame)
        if not success:
            print("[ERROR] imencode failed")
            continue
        jpg_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' +
               jpg_bytes +
               b'\r\n')
        # optional sleep to pace streaming
        time.sleep(1.0 / camera_thread.fps)

# Routes for dashboard and photos (unchanged logic)
@app.route("/dashboard")
def serve_dashboard():
    with data_lock:
        return jsonify(data)

@app.route("/dashboard/photos")
def serve_photos():
    photos_dir = CAM_DEST
    category_limits = {
        "RGB": bogos_binted_w,
        "RGN": bogos_binted_u,
        "RE":  bogos_binted_i
    }

    categorized_files = defaultdict(list)
    try:
        files = [f for f in os.listdir(photos_dir) if f.lower().endswith((".jpg",".jpeg",".png"))]
        for f in files:
            parts = f.split("-")
            if len(parts) < 3:
                continue
            category  = parts[0].upper()
            timestamp = parts[1] + "-" + parts[2]
            if category in category_limits:
                categorized_files[category].append((timestamp, f))

        photos_payload = []
        for category, items in categorized_files.items():
            items = sorted(items, key=lambda x: x[0], reverse=True)[:category_limits[category]]
            for _, file in items:
                full_path = os.path.join(photos_dir, file)
                with open(full_path, "rb") as image_file:
                    encoded = base64.b64encode(image_file.read()).decode("utf-8")
                photos_payload.append({
                    "filename":     file,
                    "content":      encoded,
                    "content_type": "image/jpeg" if file.lower().endswith(".jpg") else "image/png"
                })

        response = {
            "photo_counts": category_limits,
            "photos":       photos_payload
        }
        return jsonify(response)
    except Exception as e:
        return {"error": str(e)}, 500

@app.route("/dashboard/<string:key>", methods=["POST"])
def update_dashboard_var(key):
    try:
        value = float(request.args.get("value", 0))
    except ValueError:
        return {"error": "Invalid value"}, 400

    if key in data:
        with data_lock:
            data[key] = value
            return {key: data[key]}
    return {"error": f"{key} not found"}, 404

# Video streaming routes
@app.route("/video/0")
def video0():
    return Response(generate_frames(cam0_thread),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route("/video/1")
def video1():
    return Response(generate_frames(cam1_thread),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

# Main monitoring loop if you still use one
def main_loop():
    global bogos_binted_w, last_update, last_picture
    last_picture = 0
    while not stop_event.is_set():
        process_start = time.time()
        with data_lock:
            if data["running"] and process_start - last_picture > 2:
                # get frames
                f0 = cam0_thread.get_frame()
                f1 = cam1_thread.get_frame()
                if f0 is not None:
                    save_rgb_image("RGB",  f0, process_start)
                    bogos_binted_w += 1
                if f1 is not None:
                    save_rgb_image("RGBT", f1, process_start)
                last_picture = process_start
        time.sleep(0.1)

def save_rgb_image(prefix, frame, timestamp: float, step=0):
    filename = f"{prefix}-{time.strftime('%Y%m%d-%H%M%S', time.localtime(timestamp))}-step{step}.png"
    cv2.imwrite(os.path.join(CAM_DEST, filename), frame)

if __name__ == "__main__":
    sensor_thread = threading.Thread(target=lambda: read_sensor_data_loop(), daemon=True)
    sensor_thread.start()
    try:
        # Start Flask
        app.run(host="0.0.0.0", port=API_PORT, threaded=True, use_reloader=False)
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        stop_event.set()
        cam0_thread.release()
        cam1_thread.release()
        os._exit(0)
