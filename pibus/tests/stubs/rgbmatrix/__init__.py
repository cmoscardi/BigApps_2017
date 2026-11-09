"""Fake rgbmatrix for tests. Records what would be drawn instead of driving GPIO."""
from . import graphics  # noqa: F401


class RGBMatrixOptions(object):
    pass


class Canvas(object):
    def __init__(self):
        self.texts = []
        self.circles = []
        self.pixels = {}

    def Clear(self):
        self.texts = []
        self.circles = []
        self.pixels = {}

    def SetPixel(self, x, y, r, g, b):
        self.pixels[(x, y)] = (r, g, b)


class RGBMatrix(object):
    def __init__(self, options=None):
        self.options = options
        self.frames = []  # one list of (font_file, x, y, text) per SwapOnVSync
        self.circle_frames = []  # one list of (x, y, r, rgb) per SwapOnVSync
        self.pixel_frames = []  # one {(x, y): rgb} per SwapOnVSync

    def CreateFrameCanvas(self):
        return Canvas()

    def SwapOnVSync(self, canvas):
        self.frames.append(list(canvas.texts))
        self.circle_frames.append(list(canvas.circles))
        self.pixel_frames.append(dict(canvas.pixels))
        return Canvas()
