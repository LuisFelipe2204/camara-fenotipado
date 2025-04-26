import adafruit_bh1750
import board
import busio
import time

# Pin I/O
i2c = busio.I2C(board.SCL, board.SDA)

# Variables
sensor = adafruit_bh1750.BH1750(i2c)

def main():
    lux = sensor.lux
    if lux is not None:
        print(f"Light Level: {lux:.2f} lux")
    else:
        print("Failed to read from BH1750 sensor!")
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