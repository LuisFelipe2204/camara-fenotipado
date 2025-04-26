import adafruit_dht
import board
import time

# Pin I/O
DHT_PIN = board.D26

# Variables
sensor = adafruit_dht.DHT22(DHT_PIN, use_pulseio=False)

def main():
    try:
        sensor.measure()
        temp, hum = sensor.temperature, sensor.humidity
    except RuntimeError:
        temp, hum = None, None

    if hum is not None and temp is not None:
        print(f"Temperature: {temp:.1f} C, Humidity: {hum:.1f} %")
    else:
        print("Failed to read from DHT sensor!")

    time.sleep(2)

if __name__ == "__main__":
    try:
        while True:
            main()
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("Exiting...")