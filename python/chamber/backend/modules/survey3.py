import shutil
import time
from os import listdir, path, remove
import logging

import digitalio
from utils.utils import generate_photo_name, get_session_dirpath


class Pulse:
    DO_NOTHING = 0.001
    TAKE_PHOTO = 0.002
    TRANSFER = 0.0015


class Survey3:
    def __init__(self, pin: digitalio.DigitalInOut, id: str, origin: str, dest: str):
        self.pin = pin
        self.origin = origin
        self.dest = dest
        self.id = id
        self.pin.direction = digitalio.Direction.OUTPUT
        self.pin.value = False

        if path.isdir(self.origin):
            logging.warning("Found existing path for camera %s, mounting back the SD.", self.id)
            self.toggle_mount()

    def pulse(self, pulse: float):
        self.pin.value = True
        time.sleep(pulse)
        self.pin.value = False
        time.sleep(0.1)

    def read(self):
        self.pulse(Pulse.DO_NOTHING)
        self.pulse(Pulse.TAKE_PHOTO)
        self.pulse(Pulse.DO_NOTHING)
        time.sleep(3)

    def toggle_mount(self):
        self.pulse(Pulse.DO_NOTHING)
        self.pulse(Pulse.TRANSFER)
        self.pulse(Pulse.DO_NOTHING)
        time.sleep(4)

    def transfer_latest(self):
        if not path.exists(self.origin):
            print(f"Error: The directory {self.origin} does not exist.")
            return False

        latest = None
        for file in listdir(self.origin):
            name = path.join(self.origin, file)
            if not path.isfile(name):
                continue
            if latest is None or path.getctime(name) > path.getctime(latest):
                latest = name
        if latest is None:
            print(f"No files found in {self.origin}.")
            return False

        shutil.copy2(
            latest, path.join(self.dest, generate_photo_name(self.id, time.time(), 0))
        )
        remove(latest)
        return True

    def transfer_n(self, n: int, session: int, timestamp: float = 0):
        if timestamp == 0:
            timestamp = time.time()

        if not path.exists(self.origin):
            print(f"Error: The directory {self.origin} does not exist.")
            return False

        files = [
            f
            for f in listdir(self.origin)
            if f.lower().endswith((".jpg", ".jpeg", ".png"))
        ]
        files = sorted(
            files, key=lambda x: path.getctime(path.join(self.origin, x)), reverse=True
        )

        if len(files) < n:
            print(
                f"Not enough files to transfer. Found {len(files)}, but expected {n}."
            )
            return False

        for i, file in enumerate(files[:n]):
            shutil.copy2(
                path.join(self.origin, file),
                path.join(get_session_dirpath(self.dest, session), generate_photo_name(self.id, timestamp, i))
            )
            remove(path.join(self.origin, file))
        return True

    def clear_sd(self):
        if not path.exists(self.origin):
            print(f"Error: The directory {self.origin} does not exist.")
            return False

        for file in listdir(self.origin):
            name = path.join(self.origin, file)
            if not path.isfile(name):
                continue

            try:
                remove(name)
            except Exception as e:
                print(f"Failed to remove {name}: {e}")
        return True
