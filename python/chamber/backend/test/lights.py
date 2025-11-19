import digitalio
import board
import time

# Pin I/O
LED_W = digitalio.DigitalInOut(board.D17)
LED_R = digitalio.DigitalInOut(board.D22)
LED_U = digitalio.DigitalInOut(board.D27)

# Set pin directions
for pin in [LED_W, LED_R, LED_U]:
    pin.direction = digitalio.Direction.OUTPUT

# Variables
led_w = False
led_r = False
led_u = False


def main():
    global led_w, led_r, led_u
    pin_number = int(input("Enter the pin number to toggle the LED (17, 22, or 27): "))

    if pin_number == 17:
        led_w = not led_w
        LED_W.value = led_w
        state = led_w
    elif pin_number == 22:
        led_r = not led_r
        LED_R.value = led_r
        state = led_r
    elif pin_number == 27:
        led_u = not led_u
        LED_U.value = led_u
        state = led_u
    else:
        print("Invalid pin number. Please enter 17, 22, or 27.")
        return

    print(f"LED {pin_number} is now {'ON' if state else 'OFF'}.")


if __name__ == "__main__":
    try:
        while True:
            main()
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("Exiting...")
