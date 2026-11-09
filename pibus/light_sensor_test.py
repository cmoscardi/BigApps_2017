#!/usr/bin/env python3
"""Print the value of a binary light sensor once per second.

Wiring (40-pin header, far edge of the board):
    physical pin 39 -> GND
    physical pin 40 -> GPIO21 (sensor signal)

If your board has the older 26-pin header, the far-edge pins are
physical pin 25 (GND) and physical pin 26 (GPIO7). Set SENSOR_PIN = 7.

Run with:  python3 light_sensor_test.py
Stop with: Ctrl+C
"""

import time

import RPi.GPIO as GPIO

SENSOR_PIN = 21  # BCM numbering


def main():
    GPIO.setmode(GPIO.BCM)
    # Pull-up so the pin reads a stable 1 when the sensor is not pulling it to GND.
    GPIO.setup(SENSOR_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    try:
        while True:
            value = GPIO.input(SENSOR_PIN)
            print(f"{time.strftime('%H:%M:%S')}  sensor = {value}", flush=True)
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        GPIO.cleanup()


if __name__ == "__main__":
    main()
