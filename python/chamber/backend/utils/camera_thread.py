"""Handler for reading camera data on separate threads"""

import threading
import time
import logging

import cv2

CAMERA_WIDTH = 320
CAMERA_HEIGHT = 240
CAMERA_FPS = 10


class CameraThread(threading.Thread):
    """Main class representing a Camera accessible via cv2"""

    def __init__(self, device_index, stop_event):
        super().__init__(daemon=True)
        self.device_index = device_index
        self.fps = CAMERA_FPS

        self.capture = cv2.VideoCapture(device_index)  # pylint: disable=no-member
        self.capture.set(
            cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH # pylint: disable=no-member
        )
        self.capture.set(
            cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT # pylint: disable=no-member
        )
        self.capture.set(cv2.CAP_PROP_FPS, self.fps)  # pylint: disable=no-member

        self.lock = threading.Lock()
        self.stop_event = stop_event
        self.frame = None

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
