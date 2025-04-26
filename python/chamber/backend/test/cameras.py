import RPi.GPIO as GPIO # type: ignore
from cv2 import VideoCapture, imwrite
from modules.survey3 import Survey3
import time

# Pin I/O
RE_CAMERA = 27
RGN_CAMERA = 26

# Pin definition
GPIO.setmode(GPIO.BCM)
GPIO.setup(RE_CAMERA, GPIO.OUT)
GPIO.setup(RGN_CAMERA, GPIO.OUT)

# Constants
RGB_CAMERA_INDEX = 0
SOURCE_RE = "/media/rpi4sise1/0000-0001/DCIM/Photo"
SOURCE_RGN = "/media/rpi4sise1/0000-00011/DCIM/Photo"
DESTINATION = "/home/rpi4sise1/Desktop/pictures"

# Variables
rgb_camera = VideoCapture(RGB_CAMERA_INDEX)
re_camera = Survey3(RE_CAMERA, "RE", SOURCE_RE, DESTINATION)
rgn_camera = Survey3(RGN_CAMERA, "RGN", SOURCE_RGN, DESTINATION)

# Functions
def save_rgb_image(frame):
    filename = f"RGB-{time.strftime('%Y%m%d-%H%M%S')}.png"
    imwrite(f"{DESTINATION}/{filename}", frame)

def main():
    cmd = int(input("[1] Trigger\n[2] Mount/Dismount\n[3] Transfer\n[4] Clear SD\n>> "))
    # Flow: Trigger => Dismount => Transfer => Clear
    # Takes the pictures, transfers one and deletes the rest

    # Flow: (Trigger => Dismount => Transfer)xN => Clear
    # Takes N pictures, transfers one for each burst (cameras take 10 pictures per trigger) and deletes the rest

    match cmd:
        case 1:
            print("Triggering...")
            re_camera.read()
            rgn_camera.read()
            success, frame = rgb_camera.read()
            if success: save_rgb_image(frame)
        case 2:
            print("Mount/Dismount")
            re_camera.toggle_mount()
            rgn_camera.toggle_mount()
        case 3:
            re_camera.transfer_latest()
            rgn_camera.transfer_latest()
        case _:
            print("Invalid.")

if __name__ == "__main__":
    try:
        while True:
            main()
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        GPIO.cleanup()
