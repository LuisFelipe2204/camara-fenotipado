import adafruit_dht
import board
import time

# Pin I/O
DHT_PIN = board.D26

# Variables
sensor = adafruit_dht.DHT22(DHT_PIN, use_pulseio=False)
sucess = 0
fail = 0


def main():
    global sucess, fail

    try:
        sensor.measure()
        sucess += 1
    except RuntimeError as e:
        print(f"DHT Sensor error: {e}")
        fail += 1

    temp = sensor.temperature
    hum = sensor.humidity
    if hum is not None and temp is not None:
        print(f"Temperature: {temp:.1f} C, Humidity: {hum:.1f} %")
    else:
        print("Failed to read from DHT sensor!")

    time.sleep(0.4)


if __name__ == "__main__":
    try:
        while True:
            main()
            time.sleep(0.1)
    except KeyboardInterrupt:
        print(f"Success: {sucess}, Fail: {fail}")
        print(f"Ratio: {sucess / (sucess + fail):.2f}")
        print("Exiting...")
