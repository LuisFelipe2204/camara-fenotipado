import adafruit_ltr390
import board
import busio
import time

# Pin I/O
i2c = busio.I2C(board.SCL, board.SDA)

# Variables
sensor = adafruit_ltr390.LTR390(i2c)


def main():
    uv = sensor.uvi
    if uv is not None:
        print(f"Light Level: {uv:.2f} lux")
    else:
        print("Failed to read from LTR390 sensor!")
    time.sleep(2)


if __name__ == "__main__":
    try:
        while True:
            main()
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        pass
