#!/usr/bin/env python3
# Show the next Manhattan-bound F train at 4 Av-9 St: an F in an orange ring,
# then the minutes until it arrives. The screen stays put and only the number
# changes as the train gets closer.
import os
import time

from base import BaseLED
from rgbmatrix import graphics

import subway

HERE = os.path.dirname(os.path.abspath(__file__))
LARGE_FONT = "7x14.bdf"
SMALL_FONT = "6x10.bdf"

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
MIN_Y = 13
LARGE_CHAR_W = 7


def find_font_dir(start=HERE):
    """Find rpi-rgb-led-matrix's fonts/ dir next to this file or in any parent."""
    path = start
    while True:
        candidate = os.path.join(path, "fonts")
        if os.path.isfile(os.path.join(candidate, LARGE_FONT)):
            return candidate
        parent = os.path.dirname(path)
        if parent == path:
            return None
        path = parent


def minutes_label(minutes):
    """Minutes until the next train, e.g. "4", or "--" if none are coming."""
    return str(minutes[0]) if minutes else "--"


class RunText(BaseLED):
    def __init__(self, *args, **kwargs):
        super(RunText, self).__init__(*args, **kwargs)
        self.parser.add_argument("--font-dir", help="Directory that holds %s and %s. Default: the first fonts/ dir found in this script's folder or a parent folder." % (LARGE_FONT, SMALL_FONT))
        self.arrivals = []
        self.last_fetch = None

    def run(self):
        self._set_screen_params()
        while True:
            self.run_once()
            time.sleep(REDRAW_SECS)

    def run_once(self, now=None):
        now = time.time() if now is None else now
        if self.last_fetch is None or now - self.last_fetch >= FETCH_SECS:
            self._fetch(now)
        self._draw(minutes_label(subway.minutes_away(self.arrivals, now=now)))

    def _fetch(self, now):
        # On failure, keep the old arrival times; they keep counting down.
        self.last_fetch = now
        try:
            self.arrivals = subway.arrival_times(subway.fetch_feed())
        except Exception as e:
            print("Subway fetch failed: %s" % e)

    def _draw(self, label):
        self.canvas.Clear()
        graphics.DrawCircle(self.canvas, RING_X, RING_Y, RING_R, self.ring_color)
        graphics.DrawText(self.canvas, self.small_font, F_X, F_Y, self.text_color, "F")
        x = MIN_LEFT + max(0, (MIN_WIDTH - LARGE_CHAR_W * len(label)) // 2)
        graphics.DrawText(self.canvas, self.large_font, x, MIN_Y, self.text_color, label)
        self.canvas = self.matrix.SwapOnVSync(self.canvas)

    def _set_screen_params(self):
        font_dir = self.args.font_dir or find_font_dir()
        if not font_dir:
            raise SystemExit("Could not find %s. Pass --font-dir /path/to/rpi-rgb-led-matrix/fonts" % LARGE_FONT)
        self.canvas = self.matrix.CreateFrameCanvas()
        self.large_font = graphics.Font()
        self.large_font.LoadFont(os.path.join(font_dir, LARGE_FONT))
        self.small_font = graphics.Font()
        self.small_font.LoadFont(os.path.join(font_dir, SMALL_FONT))
        self.ring_color = graphics.Color(*F_ORANGE)
        self.text_color = graphics.Color(*WHITE)


# Main function
if __name__ == "__main__":
    run_text = RunText()
    if (not run_text.process()):
        run_text.parser.print_help()
