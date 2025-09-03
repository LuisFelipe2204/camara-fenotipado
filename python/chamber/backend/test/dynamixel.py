from modules.ax12 import Ax12
import time

# Class configuration
Ax12.DEVICENAME = '/dev/ttyAMA0' # e.g 'COM3' for Windows or '/dev/ttyUSB0' for Linux
Ax12.BAUDRATE = 1_000_000 
Ax12.connect() # Sets baudrate and opens com port

# Constants
MOTOR_ID = 1
MOTOR_SPEED = 50

# Variables
dxl = Ax12(MOTOR_ID)
dxl.set_moving_speed(MOTOR_SPEED)

def main():
    pos = input("Enter an angle (0-300): ")
    if pos == 'n':
        exit(0)

    pos = min(max(int(pos) * 1023 // 300, 0), 1023)
    dxl.set_goal_position(pos)

if __name__ == "__main__":
    try:
        while True:
            main()
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        dxl.set_torque_enable(0)
        Ax12.disconnect()
