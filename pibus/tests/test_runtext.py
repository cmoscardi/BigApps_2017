import os
import sys
import tempfile
import unittest
from unittest import mock

import runtext

NOW = 1_800_000_000


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
        self.assertEqual(rt.font.path, "/fonts/6x10.bdf")

    def test_minutes_labels(self):
        self.assertEqual(runtext.minutes_labels([3, 11, 19]), ["3", "11"])
        self.assertEqual(runtext.minutes_labels([0]), ["0", "--"])
        self.assertEqual(runtext.minutes_labels([]), ["--", "--"])

    def test_find_font_dir_walks_up(self):
        with tempfile.TemporaryDirectory() as root:
            os.makedirs(os.path.join(root, "fonts"))
            open(os.path.join(root, "fonts", "6x10.bdf"), "w").close()
            deep = os.path.join(root, "bindings", "python", "samples", "pibus")
            os.makedirs(deep)
            self.assertEqual(runtext.find_font_dir(deep), os.path.join(root, "fonts"))

    def test_no_bus(self):
        self.assertNotIn("bus", sys.modules["runtext"].__dict__)

    @mock.patch("runtext.subway.fetch_feed")
    @mock.patch("runtext.subway.arrival_times", return_value=[NOW + 250, NOW + 730])
    def test_static_screen_counts_down(self, arrival_times, fetch_feed):
        rt = make_display()
        rt.run_once(now=NOW)          # fetch: 4 and 12 min
        rt.run_once(now=NOW + 5)      # no fetch, same numbers
        rt.run_once(now=NOW + 70)     # refetch, one minute closer
        self.assertEqual(arrival_times.call_count, 2)
        self.assertEqual(texts(rt), [["F", "4", "12"], ["F", "4", "12"], ["F", "3", "11"]])
        # Orange F-line ring around the F on every frame.
        ring = (runtext.RING_X, runtext.RING_Y, runtext.RING_R, runtext.F_ORANGE)
        self.assertEqual(rt.matrix.circle_frames, [[ring]] * 3)

    @mock.patch("runtext.subway.arrival_times", return_value=[NOW + 130])
    def test_draw_positions(self, _):
        rt = make_display()
        with mock.patch("runtext.subway.fetch_feed"):
            rt.run_once(now=NOW)
        self.assertEqual(rt.matrix.frames[0], [
            ("6x10.bdf", runtext.F_X, runtext.F_Y, "F"),
            ("6x10.bdf", 21, 8, "2"),    # next train on top, centered in right half
            ("6x10.bdf", 18, 16, "--"),  # no train after it yet
        ])
        rt._draw(runtext.minutes_labels([12, 5]))
        self.assertEqual(rt.matrix.frames[1][1:], [
            ("6x10.bdf", 18, 8, "12"),
            ("6x10.bdf", 21, 16, "5"),
        ])

    @mock.patch("runtext.subway.fetch_feed", side_effect=OSError("network down"))
    def test_fetch_error_keeps_old_times(self, _):
        rt = make_display()
        with mock.patch("builtins.print"):
            rt.run_once(now=NOW)      # nothing cached yet
            rt.arrivals = [NOW + 400]
            rt.run_once(now=NOW + 40) # fetch fails again; old time still counts down
        self.assertEqual(texts(rt), [["F", "--", "--"], ["F", "6", "--"]])

if __name__ == "__main__":
    unittest.main()
