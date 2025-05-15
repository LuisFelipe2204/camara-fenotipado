import RPi.GPIO as GPIO # type: ignore
import time

# Pin I/O
LED = 17

# Pin definition
GPIO.setmode(GPIO.BCM)
GPIO.setup(LED, GPIO.OUT)

# Variables
led = False

def main():
    global led
    input("Press Enter to toggle the LED...")

    led = not led
    GPIO.output(LED, led)
    print(f"LED {'on' if LED else 'off'}")

if __name__ == "__main__":
    try:
        while True:
            main()
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        GPIO.cleanup()