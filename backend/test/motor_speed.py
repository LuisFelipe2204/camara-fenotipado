import time

from modules.ax12 import Ax12

# Class configuration
Ax12.DEVICENAME = "/dev/ttyAMA0"
Ax12.BAUDRATE = 1_000_000
Ax12.connect()

# Constants
MOTOR_ID = 1
MOTOR_SPEED_INIT = 50
LIMIT_BYTES = 1023

# Variables
motor_speed = MOTOR_SPEED_INIT
dxl = Ax12(MOTOR_ID)
dxl.set_moving_speed(MOTOR_SPEED_INIT)


def main():
    dxl.set_goal_position(0)
    motor_speed = int(input("Motor speed value: "))

    dxl.set_moving_speed(motor_speed)
    start_time = time.time()
    dxl.set_goal_position(LIMIT_BYTES)

    input("Press enter when the motor stops.")
    end_time = time.time()

    print(f"Result: Moved {LIMIT_BYTES} bytes in {end_time - start_time}s")


if __name__ == "__main__":
    main()
