import cv2
from fastapi import FastAPI
from fastapi.responses import JSONResponse, StreamingResponse
import uvicorn
import threading
import time
import random

# Constants
CAM_RGB_INDEX = 0
CAMERA_FPS = 15
API_PORT = 80

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
current_frame = None

# Thread functions
def start_api():
    uvicorn.run(app, host="0.0.0.0", port=API_PORT, log_level="info")

def capture_frame():
    global current_frame
    while not stop_event.is_set():
        with frame_lock:
            success, frame = rgb_camera.read()
            if success: current_frame = cv2.imencode('.jpg', frame)[1].tobytes()
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

@app.get("/video")
def serve_video():
    def generate():
        while True:
            with frame_lock:
                if current_frame is None: continue
                yield (
                    b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n' + current_frame + b'\r\n'
                )
    return StreamingResponse(generate(), media_type='multipart/x-mixed-replace; boundary=frame')

if __name__ == "__main__":
    api_thread = threading.Thread(target=start_api, daemon=True)
    camera_thread = threading.Thread(target=capture_frame, daemon=True)
    
    try:
        api_thread.start()
        camera_thread.start()
        while True:
            data["temp"] = random.uniform(10, 40)
            data["hum"] = random.uniform(20, 100)
            data["white_lux"] = random.uniform(0, 1000)
            data["ir_lux"] = random.uniform(0, 1000)
            data["uv_lux"] = random.uniform(0, 14)
            data["running"] = random.choice([True, False])
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        stop_event.set()
        camera_thread.join()
        rgb_camera.release()