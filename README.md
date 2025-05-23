# ProyectoCacao2024

## Components

The following tables lists all the components used in both the phenotyping chamber and the robotic arm systems.

### Phenotyping Chamber

| Tag | Component | Manufacturer | Description | Pin | GPIO | Type |
| --- | --------- | ------------ | ----------- | --- | ---- | ---- |
| DHT_PIN | [AM2301](https://www.haoyuelectronics.com/Attachment/AM2301/AM2301.pdf) | ASAIR | Digital temperature and humidity sensor | 25 | 37 | IN |
|  | [LTR390](https://cdn-learn.adafruit.com/downloads/pdf/adafruit-ltr390-uv-sensor.pdf) | Adafruit Industries | Ultraviolet light sensor board | SDA, SCL | 3, 5 | I2C |
|  | [BH1750FVI](https://www.mouser.com/datasheet/2/348/bh1750fvi-e-186247.pdf) | ROHM Semiconductor | Digital ambient light sensor IC | SDA, SCL | 3, 5 | I2C |
|  | [TSL2561](https://cdn-shop.adafruit.com/datasheets/TSL2561.pdf) | Adafruit Industries | Digital luminosity sensor for infrared light | SDA, SCL | 3, 5 | I2C |
| WHITE_LIGHT | [White Power LED](https://www.wayjun.com/Datasheet/Led/3W%20High%20Power%20LED.pdf) | | High power white colored LED | 17 | 11 | OUT |
| IR_LIGHT | [IR Power LED](https://www.led1.de/shop/files/Datenblaetter/PowerLEDs/WEPIR3-S2.pdf) | | High power infrared LED | 27 | 13 | OUT |
| UV_LIGHT | [UV Power LED](https://www.lc-led.com/products/lce-557uv365p.html) |  | High power ultraviolet LED | 22 | 15 | OUT |

### Robotic Arm

| Tag | Component | Manufacturer | Description | Pin | GPIO | Type |
| --- | --------- | ------------ | ----------- | --- | ---- | ---- |
| | [Dynamixel AX-12](https://emanual.robotis.com/docs/en/dxl/ax/ax-12a/) | ROBOTIS | Smart actuator with fully integrated DC Servo module | TX | 8 | UART |
| | RGB Camera | | RGB Camera for visible light | USB | | USB |
| RGN_CAMERA | [Survey3 RGN](https://drive.google.com/file/d/10gIzOjWVNoG9dvZwmAUG9fVqkEZHXEur/view) | MAPIR | Survey camera for Red, Green and Near-Infrared | 24, USB | 18 | OUT, USB |
| RE_CAMERA | [Survey3 RE](https://drive.google.com/file/d/10gIzOjWVNoG9dvZwmAUG9fVqkEZHXEur/view) | MAPIR | Survey camera for Red-Edge | 23, USB | 16 | OUT, USB |
| START_BTN | Button | | Generic button for single pulse input | 5 | 29 | IN |
| STOP_BTN | Button | | Generic button for single pulse input | 6 | 31 | IN |
| DIR_SWITCH | Switch | | Generic switch for continous input | | | IN |

## Architecture

![Architecture Diagram](./docs/architecture.png)

## Schematic

![Schematic Diagram](./schema/Schema.BMP)