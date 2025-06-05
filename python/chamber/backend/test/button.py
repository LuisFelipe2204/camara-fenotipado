import board
import digitalio
import time

# Pin I/O
SWITCH_PIN = board.D5
BUTTON_PIN = board.D6

# Pin setup
switch_io = digitalio.DigitalInOut(SWITCH_PIN)
switch_io.direction = digitalio.Direction.INPUT
switch_io.pull = digitalio.Pull.UP

button_io = digitalio.DigitalInOut(BUTTON_PIN)
button_io.direction = digitalio.Direction.INPUT
button_io.pull = digitalio.Pull.UP

# Variables
prev_switch = switch_io.value
prev_button = button_io.value

def main():
    global prev_switch, prev_button

    curr_switch = switch_io.value
    curr_button = button_io.value

    if curr_switch != prev_switch:
        if not curr_switch:
            print("Switch ON")
        else:
            print("Switch OFF")
        prev_switch = curr_switch

    if prev_button and not curr_button:
        print("Button pressed")
    prev_button = curr_button

if __name__ == "__main__":
    try:
        while True:
            main()
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("Exiting...")