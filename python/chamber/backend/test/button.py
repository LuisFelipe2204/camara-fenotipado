import RPi.GPIO as GPIO # type: ignore
import time

# Pin I/O
SWITCH = 5
BUTTON = 6

# Pin definition
GPIO.setmode(GPIO.BCM)
GPIO.setup(SWITCH, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(BUTTON, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Variables
switch = False

# Functions
def switch_callback(channel):
    global switch
    switch = GPIO.input(SWITCH)
    if switch == GPIO.LOW:
        print("Switch ON")
    else:
        print("Switch OFF")

def button_callback(channel):
    print("Button pressed")

GPIO.add_event_detect(SWITCH, GPIO.BOTH, callback=switch_callback, bouncetime=200)
GPIO.add_event_detect(BUTTON, GPIO.RISING, callback=button_callback, bouncetime=200)

try:
    while True:
        print(f'Switch: {switch} :: Button: {GPIO.input(BUTTON)}')
        time.sleep(0.1)
except KeyboardInterrupt:
    print("Program terminated.")
finally:
    GPIO.cleanup()