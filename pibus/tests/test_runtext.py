import os
import sys
import tempfile
import unittest
from unittest import mock

import runtext


def make_display():
    """A RunText wired to the fake matrix, with fonts 'loaded'."""
    with mock.patch.object(sys, "argv", ["runtext.py", "-r", "16", "--led-cols", "32",
                                         "--font-dir", "/fonts"]), \
            mock.patch.object(runtext.RunText, "run"):
        rt = runtext.RunText()
        rt.process()
    rt._set_screen_params()
    return rt


def texts(rt):
    return [[t[3] for t in frame] for frame in rt.matrix.frames]


class RunTextTest(unittest.TestCase):
    def test_led_options(self):
        rt = make_display()
        self.assertEqual(rt.matrix.options.rows, 16)
        self.assertEqual(rt.matrix.options.cols, 32)
        self.assertEqual(rt.large_font.path, "/fonts/7x14.bdf")

    def test_train_rows(self):
        self.assertEqual(runtext.train_rows([3, 11, 19]), ("3,11", "MIN"))
        self.assertEqual(runtext.train_rows([0]), ("0", "MIN"))
        self.assertEqual(runtext.train_rows([45, 120]), ("45", "MIN"))
        self.assertEqual(runtext.train_rows([]), ("NONE", ""))

    def test_find_font_dir_walks_up(self):
        with tempfile.TemporaryDirectory() as root:
            os.makedirs(os.path.join(root, "fonts"))
            open(os.path.join(root, "fonts", "7x14.bdf"), "w").close()
            deep = os.path.join(root, "bindings", "python", "samples", "pibus")
            os.makedirs(deep)
            self.assertEqual(runtext.find_font_dir(deep), os.path.join(root, "fonts"))

    def test_no_bus(self):
        self.assertNotIn("bus", sys.modules["runtext"].__dict__)

    @mock.patch("runtext.time.sleep")
    @mock.patch("runtext.subway.next_trains", return_value=[4, 12])
    def test_run_once(self, *_):
        rt = make_display()
        rt.run_once()
        self.assertEqual(texts(rt), [
            ["F TO", "MANH"],
            ["F"], ["4,12", "MIN"],
        ])

    @mock.patch("runtext.time.sleep")
    @mock.patch("runtext.subway.next_trains", side_effect=OSError("network down"))
    def test_fetch_error_shows_no_data(self, *_):
        rt = make_display()
        with mock.patch("builtins.print"):
            rt.run_once()
        self.assertEqual(texts(rt), [
            ["F TO", "MANH"], ["NO", "DATA"],
        ])


if __name__ == "__main__":
    unittest.main()
