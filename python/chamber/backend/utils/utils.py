"""Helper functions used on the main module"""

import time

import digitalio


def generate_photo_name(prefix: str, timestamp: float, step: int) -> str:
    """Return a string representation of the photo data with camera label, time and step
    Args:
        prefix: The label to identify the camera type
        timestamp: The unix time in which the process of the photo started
        step: The index of the angle in which the photo was taken
    Returns:
        All the data stored in a string filename (PNG) "RGB-20251119_013323-4.png"
    """
    time_str = time.strftime("%Y%m%d_%H%M%S", time.localtime(timestamp))
    return f"{prefix}-{time_str}-{step}.png"


def extract_photo_name(name: str):
    """Extract data from the image names created in save_rgb_image function.
    Args:
        name: The file name
    """
    label, date, hour, end = name.split("-")
    step, extension = end.split(".")
    return (label, f"{date}-{hour}", step, extension)


def insert_array_padded(array: list, index: int, item) -> list:
    """Inserts an item in a list in any position, padding with None if out of range.
    Args:
        array: The list to modify
        index: The position to insert the item on
        item: The item to put on the list
    Returns
        The modified list
    """
    if index >= len(array):
        array.extend([None] * (index + 1 - len(array)))
    array[index] = item
    return array


def degree_to_byte(degree: int) -> int:
    """Convert a degree value to a byte value for the servo motor.
    Args:
        degree: The degree value to convert.
    Returns:
        The converted byte value, clamped between 0 and 1023.
    """
    return min(max(degree * 1023 // 300, 0), 1023)


def debounce_button(digital_pin: digitalio.DigitalInOut, old_state: bool) -> bool:
    """Debounce a button press to avoid false triggers.
    Args:
        pin: The pin connected to the button.
        old_state: The previous state of the button.
    Returns:
        The new state of the button if it has changed, otherwise returns the old state.
    """
    if digital_pin.value != old_state:
        time.sleep(0.05)
        return digital_pin.value
    return old_state
