#!/usr/bin/env python3
# Show the next Manhattan-bound F trains at 4 Av-9 St, with double-buffering.
import os
import time

from base import BaseLED
from rgbmatrix import graphics

import subway

HERE = os.path.dirname(os.path.abspath(__file__))
LARGE_FONT = "7x14.bdf"
SMALL_FONT = "6x10.bdf"

# Seconds each screen stays up.
HEADER_SECS = 7
LINE_NAME_SECS = 3
TIME_SECS = 6
CYCLE_GAP_SECS = 3


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


def train_rows(minutes):
    """Top row: up to 2 arrival times, e.g. "3,11". Bottom row: "MIN"."""
    if not minutes:
        return "NONE", ""
    top = ",".join(str(m) for m in minutes[:2])
    if len(top) > 5:  # 6x10 font: 5 characters fit across 32 columns.
        top = str(minutes[0])
    return top, "MIN"


class RunText(BaseLED):
    def __init__(self, *args, **kwargs):
        super(RunText, self).__init__(*args, **kwargs)
        self.parser.add_argument("--font-dir", help="Directory that holds %s and %s. Default: the first fonts/ dir found in this script's folder or a parent folder." % (LARGE_FONT, SMALL_FONT))

    def run(self):
        self._set_screen_params()
        while True:
            self.run_once()

    def run_once(self):
        self._show_f_train()
        time.sleep(CYCLE_GAP_SECS)

    def _show_f_train(self):
        self._small("F TO", "MANH")
        time.sleep(HEADER_SECS)
        try:
            minutes = subway.next_trains()
        except Exception as e:
            print("Subway fetch failed: %s" % e)
            self._small("NO", "DATA")
        else:
            self._large("F")
            time.sleep(LINE_NAME_SECS)
            self._small(*train_rows(minutes))
        time.sleep(TIME_SECS)

    def _large(self, text):
        self.canvas.Clear()
        graphics.DrawText(self.canvas, self.large_font, 0, 15, self.color, text)
        self.canvas = self.matrix.SwapOnVSync(self.canvas)

    def _small(self, top, bottom):
        self.canvas.Clear()
        graphics.DrawText(self.canvas, self.small_font, 0, 7, self.color, top)
        graphics.DrawText(self.canvas, self.small_font, 0, 15, self.color, bottom)
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
        self.color = graphics.Color(255, 0, 0)


# Main function
if __name__ == "__main__":
    run_text = RunText()
    if (not run_text.process()):
        run_text.parser.print_help()
