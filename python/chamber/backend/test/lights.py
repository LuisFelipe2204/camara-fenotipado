import RPi.GPIO as GPIO # type: ignore
import time

# Pin I/O
LED = 26

# Pin definition
GPIO.setmode(GPIO.BCM)
GPIO.setup(LED, GPIO.OUT, pull_up_down=GPIO.PUD_UP)

# Variables
led = False

def main():
    global led
    input("Press Enter to toggle the LED...")

    led = not led
    GPIO.output(LED, led)
    print(f"LED {'on' if LED.value else 'off'}")

if __name__ == "__main__":
    try:
        while True:
            main()
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        GPIO.cleanup()