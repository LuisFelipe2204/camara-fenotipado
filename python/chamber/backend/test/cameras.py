import digitalio
import board
from cv2 import VideoCapture, imwrite
from cv2.typing import MatLike
from modules.survey3 import Survey3
import time

from utils import utils

# Pin I/O
RE_CAMERA_PIN = digitalio.DigitalInOut(board.D24)
RGN_CAMERA_PIN = digitalio.DigitalInOut(board.D23)

# Set pin directions
RE_CAMERA_PIN.direction = digitalio.Direction.OUTPUT
RGN_CAMERA_PIN.direction = digitalio.Direction.OUTPUT

# Constants
RGB_CAMERA_INDEX = 0
RGBTOP_CAMERA_INDEX = 2
SOURCE_RE = "/media/sise/0000-0001/DCIM/Photo"
SOURCE_RGN = "/media/sise/0000-00011/DCIM/Photo"
DESTINATION = "/home/sise/Desktop/pictures"

# Variables
rgb_camera = VideoCapture(RGB_CAMERA_INDEX)
rgb_cameratop = VideoCapture(RGB_CAMERA_INDEX)
re_camera = Survey3(RE_CAMERA_PIN, "RE", SOURCE_RE, DESTINATION)
rgn_camera = Survey3(RGN_CAMERA_PIN, "RGN", SOURCE_RGN, DESTINATION)
process_start = 0


# Functions
def save_rgb_image(prefix: str, frame: MatLike, timestamp: float, step=0):
    """Save the RGB image to the specified directory with a timestamp and step number.
    Args:
        prefix: The label of the image to identify the camera
        frame: The image frame to save.
        timestamp: The timestamp to use for the filename.
        step: The step number for the filename. Defaults to 0.
    """
    filename = utils.generate_photo_name(prefix, timestamp, step)
    dirpath = utils.get_session_dirpath(CAM_DEST, states["session"])
    cv2.imwrite(os.path.join(dirpath, filename), frame)  # pylint: disable=no-member


def main():
    cmd = int(
        input(
            """Commands
- (1) Trigger
- (2) Toggle mount
- (3) Transfer latest
- (4) Mimick main
  Command >> """
        )
    )
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
            successtop, frametop = rgb_cameratop.read()
            if success:
                save_rgb_image("RGB", frame, time.time())
            if successtop:
                save_rgb_image("RGBT", frametop, time.time())
        case 2:
            print("Mount/Dismount")
            re_camera.toggle_mount()
            rgn_camera.toggle_mount()
        case 3:
            re_camera.transfer_latest()
            rgn_camera.transfer_latest()
        case 4:
            print("Mimicking main...")
            process_start = time.time() * 1
            for i in range(10):
                print(f"Iteration {i + 1}")
                re_camera.read()
                # rgn_camera.read()
                success, frame = rgb_camera.read()
                if success:
                    save_rgb_image(frame, process_start, i)
            re_camera.toggle_mount()
            re_camera.transfer_n(10, list(range(0, 10)), process_start)
            re_camera.toggle_mount()
            # rgn_camera.toggle_mount()
            # rgn_camera.transfer_n(10, list(range(0, 10)), process_start)
            # rgn_camera.toggle_mount()
            print("Done.")
        case _:
            print("Invalid.")


if __name__ == "__main__":
    try:
        while True:
            main()
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("Exiting...")
