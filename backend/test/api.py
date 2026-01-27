import base64
import os
import random
import threading
import time
from typing import Any, Dict, Optional

import cv2
from dotenv import load_dotenv
from flask import Flask, Response, jsonify, request

load_dotenv()

# Constants
CAM_RGB_INDEX = 0
CAM_RGB_TOP_INDEX = 2
CAM_DEST = "./images"
CAMERA_WIDTH = 320
CAMERA_HEIGHT = 240
CAMERA_FPS = 10
API_PORT = int(os.getenv("API_PORT", "5000"))

app = Flask(__name__)

# Shared data
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
data_lock = threading.Lock()
stop_event = threading.Event()


class CameraThread(threading.Thread):
    def __init__(self, device_index):
        super().__init__(daemon=True)
        self.device_index = device_index
        self.fps = CAMERA_FPS

        self.capture = cv2.VideoCapture(device_index)
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
        self.capture.set(cv2.CAP_PROP_FPS, self.fps)

        self.lock = threading.Lock()
        self.frame = None

    def run(self):
        warned = False
        while not stop_event.is_set():
            status, frame = self.capture.read()
            if not status or frame is None or frame.size == 0:
                if not warned:
                    print(
                        f"[WARN] Camera {self.device_index} read failed (ret={status})"
                    )
                    warned = True
                time.sleep(0.1)
                continue
            with self.lock:
                self.frame = frame.copy()
            time.sleep(1.0 / self.fps)

    def get_frame(self):
        with self.lock:
            if self.frame is None:
                return None
            return self.frame.copy()

    def release(self):
        self.capture.release()


cam_thread = CameraThread(CAM_RGB_INDEX)
cam_top_thread = CameraThread(CAM_RGB_TOP_INDEX)
video_servers = [cam_thread, cam_top_thread]
cam_thread.start()
cam_top_thread.start()


def generate_frames(camera_thread: CameraThread):
    while not stop_event.is_set():
        frame = camera_thread.get_frame()
        if frame is None:
            time.sleep(0.01)
            continue
        success, buffer = cv2.imencode(".jpg", frame)
        if not success:
            print("[ERROR] imencode failed")
            continue
        frame_bytes = buffer.tobytes()
        yield (
            b"--frame\r\n" b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
        )
        time.sleep(1.0 / camera_thread.fps)


@app.route("/dashboard")
def serve_dashboard():
    with data_lock:
        return jsonify(data)


def set_with_padding(arr, index, item):
    if index >= len(arr):
        arr.extend([None] * (index + 1 - len(arr)))
    arr[index] = item
    return arr


@app.route("/dashboard/photos")
def serve_photos():
    PHOTOS_DIR = CAM_DEST
    FORMATS = (".jpg", ".jpeg", ".png")
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
    # photos: dict[str, list[Optional[Dict[str, Any]]]] = {key: [None] * limits[key] for key in limits}
    # print(photos)
    # Get all image files and sort them newest to oldest
    files = [file for file in os.listdir(PHOTOS_DIR) if file.lower().endswith(FORMATS)]
    files.sort(
        key=lambda file: os.path.getctime(os.path.join(PHOTOS_DIR, file)), reverse=True
    )

    if len(files) == 0:
        print("Tried serving photos but there's none")
        return jsonify({"photo_counts": limits, "photos": photos})

    latest_timestamp = extract_photo_name(files[0])[1]
    print(
        f"Latest timestamp found is {latest_timestamp} and found {len(files)} files in total"
    )
    for file in files:
        label, timestamp, step, ext = extract_photo_name(file)
        print(f"Comparing timestamps {timestamp} with latest {latest_timestamp}")
        if timestamp != latest_timestamp:
            continue

        if label not in photos:
            print(f"[WARN] File retreived with invalid label '{label}'. {file}")
            continue

        full_path = os.path.join(PHOTOS_DIR, file)
        print(f"Processing file {full_path}")
        with open(full_path, "rb") as image_file:
            content = base64.b64encode(image_file.read()).decode("utf-8")
        print(f"Adding file: {file}")
        set_with_padding(
            photos[label],
            int(step),
            {
                "filename": file,
                "content": content,
                "content_type": "image/jpeg" if ext == "jpg" else "image/png",
            },
        )
        # photos[label][int(step)] = {
        #    "filename": file,
        #    "content": content,
        #    "content_type": "image/jpeg" if ext == "jpg" else "image/png",
        # }

    return jsonify({"photo_counts": limits, "photos": photos})


@app.route("/dashboard/<string:key>", methods=["POST"])
def update_dashboard_var(key):
    try:
        value = float(request.args.get("value", 0))
    except ValueError:
        return {"error": "Invalid value"}, 400

    if key not in data:
        return {"error": f"{key} not found"}, 404

    with data_lock:
        data[key] = value
        return {key: data[key]}


@app.route("/video/<int:index>")
def video(index):
    if index >= len(video_servers) or index < 0:
        return Response()

    server = video_servers[index]
    return Response(
        generate_frames(server),
        mimetype="multipart/x-mixed-replace; boundary=frame",
    )


def save_rgb_image(prefix, frame, timestamp: float, step=0):
    filename = f"{prefix}-{time.strftime('%Y%m%d-%H%M%S', time.localtime(timestamp))}-{step}.png"
    cv2.imwrite(os.path.join(CAM_DEST, filename), frame)


def extract_photo_name(name: str):
    label, date, time, end = name.split("-")
    step, extension = end.split(".")
    return (label, f"{date}-{time}", step, extension)


# {
#       "label": label,
#      "timestamp": f"{date}-{time}",
#     "step": int(step),
#    "ext": extension,
# }


process_start = 0


def read_sensor_data():
    global data_lock, data, process_start
    while not stop_event.is_set():
        with data_lock:
            data["temp"] = round(random.uniform(10, 40), 1)
            data["hum"] = round(random.uniform(20, 100), 1)
            data["white_lux"] = round(random.uniform(0, 1000), 1)
            data["ir_lux"] = round(random.uniform(0, 1000), 1)
            data["uv_lux"] = round(random.uniform(0, 14), 1)
            data["angle"] = random.randint(0, 300)

            if data["progress"] == 0 and not data["running"]:
                photos_taken["side"] = 0
                photos_taken["top"] = 0
                photos_taken["ir"] = 0
                photos_taken["uv"] = 0
                process_start = time.time()

            if data["running"]:
                data["progress"] += 10

            if data["progress"] > 100:
                data["progress"] = 100
            elif data["progress"] == 100:
                data["progress"] = 0
                data["running"] = False
        time.sleep(0.5)


def main_loop():
    global photos_taken, last_update, last_picture, process_start
    last_picture = 0
    local_start = process_start
    steps = 0

    while not stop_event.is_set():
        with data_lock:
            if local_start != process_start:
                steps = 0
                local_start = process_start

            if data["running"] and time.time() - last_picture > 2:
                frame = cam_thread.get_frame()
                frame_top = cam_top_thread.get_frame()

                if frame is not None:
                    save_rgb_image("RGB", frame, process_start, steps)
                photos_taken["side"] += 1

                if frame_top is not None:
                    save_rgb_image("RGBT", frame_top, process_start, steps)
                photos_taken["top"] += 1

                last_picture = time.time()
                steps += 1  # Increment ONLY when photos are taken

        time.sleep(0.1)


if __name__ == "__main__":
    sensor_thread = threading.Thread(target=read_sensor_data, daemon=True)
    main_thread = threading.Thread(target=main_loop, daemon=True)
    sensor_thread.start()
    main_thread.start()
    try:
        app.run(host="0.0.0.0", port=API_PORT, threaded=True, use_reloader=False)
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        stop_event.set()
        cam_thread.release()
        cam_top_thread.release()
        os._exit(0)
