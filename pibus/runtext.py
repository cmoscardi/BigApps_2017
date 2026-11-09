#!/usr/bin/env python3
# Show the next Manhattan-bound F trains at 4 Av-9 St: an F in an orange ring,
# then, stacked on the right, the minutes until the next F and the F after it.
# The screen stays put and only the numbers change as the trains get closer. Every 5 minutes a train drives across.
# When the room is dark (light sensor on GPIO21 reads 1), the panel dims.
import os
import time

try:
    import RPi.GPIO as GPIO
except ImportError:  # Not on a Pi (e.g. running the tests): never dim.
    GPIO = None

from base import BaseLED
from rgbmatrix import graphics

import subway

HERE = os.path.dirname(os.path.abspath(__file__))
FONT = "6x10.bdf"

# How often to pull the MTA feed, and how often to recount minutes from the
# arrival times we already have.
FETCH_SECS = 30
REDRAW_SECS = 5

F_ORANGE = (255, 99, 25)  # MTA F line orange, #FF6319.
WHITE = (255, 255, 255)

# Layout for a 32x16 panel: ring on the left half, minutes on the right half.
RING_X, RING_Y, RING_R = 7, 8, 7
F_X, F_Y = 5, 12              # 6x10 "F" is 5 px wide, 7 px tall: centered in the ring.
MIN_LEFT, MIN_WIDTH = 16, 16  # Right half of the panel.
# Baselines for the next train (top) and the one after (bottom). 6x10 digits
# are 7 px tall, so they fill rows 1-7 and 9-15, level with the ring.
MIN_YS = (8, 16)
CHAR_W = 6

# Train animation: how often it plays, and how long each 1 px step takes.
TRAIN_EVERY_SECS = 5 * 60
TRAIN_FRAME_SECS = 0.03

# Pixel art for one car. One character is one LED; "." is off.
TRAIN_CAR = [
    ".SSSSSSSSSSSS.",
    "SWWSWWSWWSWWSS",
    "SWWSWWSWWSWWSS",
    "SSSSSSSSSSSSSS",
    "OOOOOOOOOOOOOO",
    "SSSSSSSSSSSSSS",
    ".KK........KK.",
]
TRAIN_CARS = 3
TRAIN_COLORS = {
    "S": (140, 140, 150),  # Stainless steel body.
    "W": (255, 220, 120),  # Lit windows.
    "O": F_ORANGE,         # Line stripe.
    "K": (60, 60, 60),     # Wheels.
    "L": (255, 255, 200),  # Headlight.
}
TRAIN_Y = 4  # Top row of the train on the panel.

# Binary light sensor between physical pins 39 (GND) and 40 (GPIO21).
# It reads 1 when the room is dark.
LIGHT_SENSOR_PIN = 21  # BCM numbering
DARK = 1
DIM_BRIGHTNESS = 20  # Percent, 1..100.


def find_font_dir(start=HERE):
    """Find rpi-rgb-led-matrix's fonts/ dir next to this file or in any parent."""
    path = start
    while True:
        candidate = os.path.join(path, "fonts")
        if os.path.isfile(os.path.join(candidate, FONT)):
            return candidate
        parent = os.path.dirname(path)
        if parent == path:
            return None
        path = parent


def train_sprite(cars=TRAIN_CARS):
    """Rows of the whole train: cars joined by a 1 px gap, headlight up front."""
    rows = [".".join([row] * cars) for row in TRAIN_CAR]
    rows[1] = "L" + rows[1][1:]
    return rows


def minutes_labels(minutes, count=len(MIN_YS)):
    """Minutes until each of the next `count` trains, e.g. ["4", "12"].

    "--" stands in for a train that isn't coming.
    """
    labels = [str(m) for m in minutes[:count]]
    return labels + ["--"] * (count - len(labels))


class RunText(BaseLED):
    def __init__(self, *args, **kwargs):
        super(RunText, self).__init__(*args, **kwargs)
        self.parser.add_argument("--font-dir", help="Directory that holds %s. Default: the first fonts/ dir found in this script's folder or a parent folder." % FONT)
        self.parser.add_argument("--dim-brightness", type=int, default=DIM_BRIGHTNESS, help="Brightness (1..100) when the room is dark. Default: %d" % DIM_BRIGHTNESS)
        self.arrivals = []
        self.last_fetch = None
        self.brightness = 100
        # Set up the sensor now, before process() creates the matrix: the
        # matrix drops root privileges, and after that we can't open the GPIO.
        self.sensor_ready = False
        if GPIO is not None:
            try:
                GPIO.setwarnings(False)
                GPIO.setmode(GPIO.BCM)
                GPIO.setup(LIGHT_SENSOR_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
                self.sensor_ready = True
            except Exception as e:
                print("Light sensor setup failed, will not dim: %s" % e)

    def run(self):
        self._set_screen_params()
        last_train = 0  # Play once at startup, then every TRAIN_EVERY_SECS.
        while True:
            self._update_brightness()
            if time.time() - last_train >= TRAIN_EVERY_SECS:
                self.animate_train()
                last_train = time.time()
            self.run_once()
            time.sleep(REDRAW_SECS)

    def animate_train(self):
        """Drive a train across the panel from right to left. Blocks until it's gone."""
        sprite = train_sprite()
        width = self.matrix.width
        for left in range(width, -len(sprite[0]) - 1, -1):
            self._clear()
            for dy, row in enumerate(sprite):
                for dx, ch in enumerate(row):
                    x = left + dx
                    if ch in TRAIN_COLORS and 0 <= x < width:
                        self.canvas.SetPixel(x, TRAIN_Y + dy, *TRAIN_COLORS[ch])
            self.canvas = self.matrix.SwapOnVSync(self.canvas)
            time.sleep(TRAIN_FRAME_SECS)

    def run_once(self, now=None):
        now = time.time() if now is None else now
        if self.last_fetch is None or now - self.last_fetch >= FETCH_SECS:
            self._fetch(now)
        self._draw(minutes_labels(subway.minutes_away(self.arrivals, now=now)))

    def _fetch(self, now):
        # On failure, keep the old arrival times; they keep counting down.
        self.last_fetch = now
        try:
            self.arrivals = subway.arrival_times(subway.fetch_feed())
        except Exception as e:
            print("Subway fetch failed: %s" % e)

    def _is_dark(self):
        return self.sensor_ready and GPIO.input(LIGHT_SENSOR_PIN) == DARK

    def _update_brightness(self):
        bright = self.args.led_brightness
        dim = min(self.args.dim_brightness, bright)
        self.brightness = dim if self._is_dark() else bright

    def _clear(self):
        # Brightness is applied as pixels are drawn, so set it on whichever
        # canvas we're about to draw into (SwapOnVSync hands back the other one).
        self.canvas.Clear()
        self.canvas.brightness = self.brightness

    def _draw(self, labels):
        self._clear()
        graphics.DrawCircle(self.canvas, RING_X, RING_Y, RING_R, self.ring_color)
        graphics.DrawText(self.canvas, self.font, F_X, F_Y, self.text_color, "F")
        for label, y in zip(labels, MIN_YS):
            x = MIN_LEFT + max(0, (MIN_WIDTH - CHAR_W * len(label)) // 2)
            graphics.DrawText(self.canvas, self.font, x, y, self.text_color, label)
        self.canvas = self.matrix.SwapOnVSync(self.canvas)

    def _set_screen_params(self):
        font_dir = self.args.font_dir or find_font_dir()
        if not font_dir:
            raise SystemExit("Could not find %s. Pass --font-dir /path/to/rpi-rgb-led-matrix/fonts" % FONT)
        self.canvas = self.matrix.CreateFrameCanvas()
        self.font = graphics.Font()
        self.font.LoadFont(os.path.join(font_dir, FONT))
        self.ring_color = graphics.Color(*F_ORANGE)
        self.text_color = graphics.Color(*WHITE)
        self.brightness = self.args.led_brightness


# Main function
if __name__ == "__main__":
    run_text = RunText()
    if (not run_text.process()):
        run_text.parser.print_help()
