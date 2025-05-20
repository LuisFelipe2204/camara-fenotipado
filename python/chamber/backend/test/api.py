import cv2
from fastapi import FastAPI
from fastapi.responses import JSONResponse, StreamingResponse
import uvicorn
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
app = FastAPI()

# Variables
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
    uvicorn.run(app, host="0.0.0.0", port=API_PORT, log_level="info")

def capture_frame():
    global current_frame
    while not stop_event.is_set():
        success, frame = rgb_camera.read()
        if success:
            f = cv2.imencode('.jpg', frame)[1].tobytes()
            frame_lock.acquire()
            current_frame = f
            frame_lock.release()
        time.sleep(1 / CAMERA_FPS)

@app.get("/dashboard")
def serve_dashboard():
    return JSONResponse(content=data)

@app.get("/dashboard/{id}")
def serve_dashboard_var(id: str):
    value = data.get(id)
    if value is not None: 
        return JSONResponse(content={id: data[id]})
    return JSONResponse(content={"error": f"{id} not found"}, status_code=404)

@app.post("/dashboard/{id}")
def update_dashboard_var(id: str, value: float):
    if id in data:
        data[id] = value
        return JSONResponse(content={id: data[id]})
    return JSONResponse(content={"error": f"{id} not found"}, status_code=404)

@app.get("/video")
def serve_video():
    def generate():
        while True:
            frame_lock.acquire()
            if current_frame is None:
                frame_lock.release()
                continue
            data = (
                b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + current_frame + b'\r\n'
            )
            frame_lock.release()
            yield data
            time.sleep(1 / CAMERA_FPS)
    return StreamingResponse(generate(), media_type='multipart/x-mixed-replace; boundary=frame')

if __name__ == "__main__":
    api_thread = threading.Thread(target=start_api, daemon=True)
    camera_thread = threading.Thread(target=capture_frame, daemon=True)
    
    try:
        api_thread.start()
        camera_thread.start()
        while True:
            data["temp"] = round(random.uniform(10, 40), 1)
            data["hum"] = round(random.uniform(20, 100), 1)
            data["white_lux"] = round(random.uniform(0, 1000), 1)
            data["ir_lux"] = round(random.uniform(0, 1000), 1)
            data["uv_lux"] = round(random.uniform(0, 14), 1)
            if data["running"]:
                with open(f"{CAM_DEST}/output-{time.time()}.jpg", "wb") as file:
                    print(f"Wrote to {CAM_DEST}/output-{time.time()}.jpg")
                    if current_frame is not None:
                        file.write(current_frame)
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        stop_event.set()
        camera_thread.join()
        rgb_camera.release()