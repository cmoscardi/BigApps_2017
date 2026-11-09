"""Fake rgbmatrix for tests. Records what would be drawn instead of driving GPIO."""
from . import graphics  # noqa: F401


class RGBMatrixOptions(object):
    pass


class Canvas(object):
    def __init__(self):
        self.texts = []

    def Clear(self):
        self.texts = []


class RGBMatrix(object):
    def __init__(self, options=None):
        self.options = options
        self.frames = []  # one list of (font_file, x, y, text) per SwapOnVSync

    def CreateFrameCanvas(self):
        return Canvas()

    def SwapOnVSync(self, canvas):
        self.frames.append(list(canvas.texts))
        return Canvas()
