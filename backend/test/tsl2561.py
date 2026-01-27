import time

import adafruit_tsl2561
import board
import busio

# Pin I/O
i2c = busio.I2C(board.SCL, board.SDA)

# Variables
sensor = adafruit_tsl2561.TSL2561(i2c)


def main():
    ir = sensor.infrared
    if ir is not None:
        print(f"Light Level: {ir:.2f} lux")
    else:
        print("Failed to read from TSL2561 sensor!")
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
