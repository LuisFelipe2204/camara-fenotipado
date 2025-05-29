import digitalio
from os import path, listdir, remove
import shutil
import time

class Pulse:
    DO_NOTHING = 0.001
    TAKE_PHOTO = 0.002
    TRANSFER = 0.0015

class Survey3():
    def __init__(self, pin: digitalio.DigitalInOut, id: str, origin: str, dest: str):
        self.pin = pin
        self.origin = origin
        self.dest = dest
        self.id = id
        self.pin.direction = digitalio.Direction.OUTPUT
        self.pin.value = False

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

        shutil.move(latest, f'{self.dest}/{self.id}-{time.strftime("%Y%m%d-%H%M%S")}.JPG')
        return True

    def transfer_n(self, n: int, steps: list[int], timestamp: float = 0):
        if timestamp == 0:
            timestamp = time.time()

        if not path.exists(self.origin):
            print(f"Error: The directory {self.origin} does not exist.")
            return False

        files = [f for f in listdir(self.origin) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        files = sorted(files, key=lambda x: path.getctime(path.join(self.origin, x)), reverse=True)

        if len(files) < n:
            print(f"Not enough files to transfer. Found {len(files)}, but expected {n}.")
            return False

        for i, file in enumerate(files[:n]):
            time_str = time.strftime("%Y%m%d-%H%M%S", time.localtime(timestamp))
            step_inverse = steps[i]
            shutil.move(path.join(self.origin, file), f'{self.dest}/{self.id}-{time_str}-step{step_inverse}.JPG')
        return True

    def clear_sd(self):
        if not path.exists(self.origin):
            print(f"Error: The directory {self.origin} does not exist.")
            return False

        for file in listdir(self.origin):
            name = path.join(self.origin, file)
            if not path.isfile(name): return False
        
            try:
                remove(name)
            except Exception as e:
                print(f"Failed to remove {name}: {e}")
                return False
        return True
