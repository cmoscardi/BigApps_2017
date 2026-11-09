class Font(object):
    def __init__(self):
        self.path = None

    def LoadFont(self, path):
        self.path = path


class Color(object):
    def __init__(self, r, g, b):
        self.rgb = (r, g, b)


def DrawText(canvas, font, x, y, color, text):
    canvas.texts.append((font.path.rsplit("/", 1)[-1], x, y, text))
    return len(text) * 6
