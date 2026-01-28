"""Handler for reading camera data on separate threads"""

import logging
import threading
import time

import cv2
import numpy as np

CAMERA_WIDTH = 320
CAMERA_HEIGHT = 240
CAMERA_FPS = 10


def create_blank_jpeg():
    """Create a 1x1 black pixel (uint8, BGR)"""
    img = np.zeros((1, 1, 3), dtype=np.uint8)

    success, buffer = cv2.imencode(".jpg", img)
    if not success:
        return b""  # fallback
    return buffer.tobytes()


class CameraThread(threading.Thread):
    """Main class representing a Camera accessible via cv2"""
    cameras: list["CameraThread"] = []

    def __init__(self, device_index, stop_event, width, height):
        super().__init__(daemon=True)
        self.device_index = device_index
        self.fps = CAMERA_FPS
        self.width = width
        self.height = height

        self.capture = cv2.VideoCapture(device_index)  # pylint: disable=no-member
        self.capture.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
        self.capture.set(
            cv2.CAP_PROP_FRAME_WIDTH, self.width  # pylint: disable=no-member
        )
        self.capture.set(
            cv2.CAP_PROP_FRAME_HEIGHT, self.height  # pylint: disable=no-member
        )
        self.capture.set(cv2.CAP_PROP_FPS, self.fps)  # pylint: disable=no-member

        self.lock = threading.Lock()
        self.stop_event = stop_event
        self.frame = None
        CameraThread.cameras.append(self)

    def run(self):
        """The main thread of the instance, updates the latest frame"""
        warned = False
        while not self.stop_event.is_set():
            status, frame = self.capture.read()
            if not status or frame is None or frame.size == 0:
                if not warned:
                    logging.warning(
                        "Camera %d failed during reading.", self.device_index
                    )
                    warned = True
                time.sleep(0.1)
                continue
            with self.lock:
                self.frame = frame.copy()
            time.sleep(1.0 / self.fps)

    def get_frame(self):
        """Create a copy of the latest frame"""
        with self.lock:
            if self.frame is None:
                return None
            return self.frame.copy()

    def release(self):
        """Release the physical camera"""
        self.capture.release()

    def generate_frames(self):
        """Constantly triggers the camera to get the latest frames and formats it for streaming.
        Args:
            camera_thread: The camera object configured to manage an RGB camera
        Returns:
            The HTTP streaming formatted frame
        """
        blank = (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" + create_blank_jpeg() + b"\r\n"
        )
        while not self.stop_event.is_set():
            frame = self.get_frame()
            if frame is None:
                yield blank
                time.sleep(1.0 / self.fps)
                continue

            try:
                success, buffer = cv2.imencode(".jpg", frame)  # pylint: disable=no-member
                frame_bytes = buffer.tobytes()
            except:
                logging.error(
                    "Camera %d failed during image encoding.", self.device_index
                )
                yield blank
                time.sleep(1.0 / self.fps)
                continue

            yield (
                b"--frame\r\n" b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
            )
            time.sleep(1.0 / self.fps)