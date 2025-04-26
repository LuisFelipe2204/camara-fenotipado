import RPi.GPIO as GPIO # type: ignore
from os import path, listdir
import shutil
import time

class Pulse:
    DO_NOTHING = 0.001
    TAKE_PHOTO = 0.002
    TRANSFER = 0.0015

class Survey3():
    def __init__(self, pin: int, id: str, origin: str, dest: str):
        self.pin = pin
        self.origin = origin
        self.dest = dest
        self.id = id

    def pulse(self, pulse: int):
        GPIO.output(self.pin, GPIO.HIGH)
        time.sleep(pulse)
        GPIO.output(self.pin, GPIO.LOW)
        time.sleep(0.1)

    def read(self):
        self.pulse(Pulse.DO_NOTHING)
        self.pulse(Pulse.TAKE_PHOTO)
        self.pulse(Pulse.DO_NOTHING)
        time.sleep(1.5)

    def toggle_mount(self):
        self.pulse(Pulse.DO_NOTHING)
        self.pulse(Pulse.TRANSFER)
        self.pulse(Pulse.DO_NOTHING)
        time.sleep(2)

    def transfer_latest(self):
        if not path.exists(self.origin):
            print(f"Error: The directory {self.origin} does not exist.")
            return False
        
        lastest = None
        for file in listdir(self.origin):
            name = path.join(self.origin, file)
            if not path.isfile(name): continue

            if lastest is None or path.getctime(name) > path.getctime(lastest):
                lastest = name
        if lastest is None:
            print(f"No files found in {self.origin}.")
            return False
        
        shutil.move(lastest, f'{self.dest}/{self.id}-{time.strftime("%Y%m%d-%H%M%S")}.JPG')
        return True
