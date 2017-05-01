#!/usr/bin/env python
# Display a runtext with double-buffering.
from base import BaseLED
from rgbmatrix import graphics
import time

import bus

class RunText(BaseLED):
    def __init__(self, *args, **kwargs):
        super(RunText, self).__init__(*args, **kwargs)
        self.parser.add_argument("-t", "--text", help="The text to scroll on the RGB LED panel", default="Hello world!")

    def run(self):
        canvas, large_font, small_font, color = self._set_screen_params()


        while True:
            cur_info = bus.nyc_current()
            strings = bus.get_time_strings(cur_info)[1]
            canvas.Clear()
	    length = graphics.DrawText(canvas, small_font, 0,  7, color, "NEXT")
	    length = graphics.DrawText(canvas, small_font, 0,  15, color, "BUS")
	    canvas = self.matrix.SwapOnVSync(canvas)
            time.sleep(7)
            for string in strings:
                canvas.Clear()
                line_name = string.split(":")[0]
                time_desc = string.split(":")[1].strip().upper()
                time_upper = time_desc.split(" ")[0]
                time_lower = time_desc.split(" ")[1] if len(time_desc.split(" ")) > 1 else "!!!"
                length = graphics.DrawText(canvas, large_font, 0,  15, color, line_name)
		canvas = self.matrix.SwapOnVSync(canvas)
                canvas.Clear()
                time.sleep(3)
                length = graphics.DrawText(canvas, small_font, 0,  7, color, time_upper)
                length = graphics.DrawText(canvas, small_font, 0,  15, color, time_lower)
		canvas = self.matrix.SwapOnVSync(canvas)
		time.sleep(6)
            time.sleep(3)


    def _set_screen_params(self):
        offscreen_canvas = self.matrix.CreateFrameCanvas()
        large_font = graphics.Font()
        large_font.LoadFont("../../fonts/7x14.bdf")
        small_font = graphics.Font()
        small_font.LoadFont("../../fonts/6x10.bdf")
        textColor = graphics.Color(255, 0, 0)
        return offscreen_canvas, large_font, small_font, textColor
        


# Main function
if __name__ == "__main__":
    run_text = RunText()
    if (not run_text.process()):
        run_text.print_help()
