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
        self.assertEqual(rt.font.path, "/fonts/4x6.bdf")

    def test_minutes_labels(self):
        self.assertEqual(runtext.minutes_labels([3, 11, 19]), ["3", "11"])
        self.assertEqual(runtext.minutes_labels([0]), ["0", "--"])
        self.assertEqual(runtext.minutes_labels([]), ["--", "--"])

    def test_find_font_dir_walks_up(self):
        with tempfile.TemporaryDirectory() as root:
            os.makedirs(os.path.join(root, "fonts"))
            open(os.path.join(root, "fonts", runtext.FONT), "w").close()
            deep = os.path.join(root, "bindings", "python", "samples", "pibus")
            os.makedirs(deep)
            self.assertEqual(runtext.find_font_dir(deep), os.path.join(root, "fonts"))

    def test_no_bus(self):
        self.assertNotIn("bus", sys.modules["runtext"].__dict__)

    def test_layout_fits_panel(self):
        # Last minute slot ends inside 32 columns; rows don't overlap.
        self.assertLessEqual(runtext.MIN_XS[-1] + runtext.SLOT_W, 32)
        self.assertGreater(runtext.MIN_XS[0], len(runtext.BADGE[0]))
        self.assertLessEqual(runtext.ROW_TOPS[0] + len(runtext.BADGE), runtext.ROW_TOPS[1])
        self.assertLessEqual(runtext.ROW_TOPS[-1] + len(runtext.BADGE), 16)

    @mock.patch("runtext.subway.route_arrivals",
                side_effect=lambda route: {"F": [NOW + 250, NOW + 730],
                                           "R": [NOW + 670, NOW + 1390]}[route])
    def test_static_screen_counts_down(self, route_arrivals):
        rt = make_display()
        rt.run_once(now=NOW)          # fetch: F 4, 12; R 11, 23
        rt.run_once(now=NOW + 5)      # no fetch, same numbers
        rt.run_once(now=NOW + 70)     # refetch, one minute closer
        self.assertEqual([c.args for c in route_arrivals.call_args_list],
                         [("F",), ("R",)] * 2)
        self.assertEqual(texts(rt), [
            ["F", "4", "12", "R", "11", "23"],
            ["F", "4", "12", "R", "11", "23"],
            ["F", "3", "11", "R", "10", "22"],
        ])

    @mock.patch("runtext.subway.route_arrivals",
                side_effect=lambda route: {"F": [NOW + 130], "R": []}[route])
    def test_draw_positions(self, _):
        rt = make_display()
        rt.run_once(now=NOW)
        self.assertEqual(rt.matrix.frames[0], [
            ("4x6.bdf", 2, 6, "F"),    # letter cut out of the top badge
            ("4x6.bdf", 16, 6, "2"),   # right-aligned in the first slot
            ("4x6.bdf", 23, 6, "--"),  # no F after it yet
            ("4x6.bdf", 2, 14, "R"),
            ("4x6.bdf", 12, 14, "--"),
            ("4x6.bdf", 23, 14, "--"),
        ])
        rt._draw([["12", "5"], ["0", "17"]])
        self.assertEqual([t[1:] for t in rt.matrix.frames[1]], [
            (2, 6, "F"), (12, 6, "12"), (27, 6, "5"),
            (2, 14, "R"), (16, 14, "0"), (23, 14, "17"),
        ])

    def test_badges(self):
        rt = make_display()
        rt._draw([["--", "--"], ["--", "--"]])
        pixels = rt.matrix.pixel_frames[0]
        f_badge = {xy for xy, rgb in pixels.items() if rgb == runtext.F_ORANGE}
        r_badge = {xy for xy, rgb in pixels.items() if rgb == runtext.R_YELLOW}
        self.assertEqual(len(f_badge), 37)
        self.assertEqual({(x, y + 8) for x, y in f_badge}, r_badge)
        self.assertIn((3, 3), f_badge)        # center
        self.assertNotIn((0, 0), f_badge)     # rounded corner
        self.assertTrue(all(x <= 6 and y <= 6 for x, y in f_badge))

    @mock.patch("runtext.subway.route_arrivals", side_effect=OSError("network down"))
    def test_fetch_error_keeps_old_times(self, _):
        rt = make_display()
        with mock.patch("builtins.print"):
            rt.run_once(now=NOW)      # nothing cached yet
            rt.arrivals["R"] = [NOW + 400]
            rt.run_once(now=NOW + 40) # fetch fails again; old time still counts down
        self.assertEqual(texts(rt), [["F", "--", "--", "R", "--", "--"],
                                     ["F", "--", "--", "R", "6", "--"]])

    def test_one_feed_down_other_still_updates(self):
        def route_arrivals(route):
            if route == "F":
                raise OSError("bdfm down")
            return [NOW + 190]

        rt = make_display()
        rt.arrivals["F"] = [NOW + 310]
        with mock.patch("runtext.subway.route_arrivals", side_effect=route_arrivals), \
                mock.patch("builtins.print"):
            rt.run_once(now=NOW)
        self.assertEqual(texts(rt), [["F", "5", "--", "R", "3", "--"]])

if __name__ == "__main__":
    unittest.main()
