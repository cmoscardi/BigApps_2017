import sys
import types
import unittest
from types import SimpleNamespace as NS
from unittest import mock

import subway

NOW = 1_800_000_000


def stu(stop_id, arrival=0, departure=0):
    return NS(stop_id=stop_id, arrival=NS(time=arrival), departure=NS(time=departure))


def trip(route_id, *updates):
    return NS(trip_update=NS(trip=NS(route_id=route_id), stop_time_update=list(updates)))


# Mirrors protobuf: unset fields read as empty/zero defaults.
FEED = NS(entity=[
    trip("F", stu("F22N", NOW + 60), stu("F23N", NOW + 660)),      # 11 min
    trip("F", stu("F23N", departure=NOW + 200)),                   # departure-only: 3 min
    trip("G", stu("F23N", NOW + 120)),                             # wrong route
    trip("F", stu("F23S", NOW + 30)),                              # Coney Island-bound
    trip("F", stu("F23N", NOW - 600)),                             # already gone
    trip(""),                                                      # alert / vehicle entity
])


class SubwayTest(unittest.TestCase):
    def test_stops(self):
        self.assertEqual(subway.STOPS["F"][1], "F23N")
        self.assertEqual(subway.STOPS["R"][1], "R33N")
        self.assertTrue(subway.STOPS["F"][0].endswith("nyct%2Fgtfs-bdfm"))
        self.assertTrue(subway.STOPS["R"][0].endswith("nyct%2Fgtfs-nqrw"))

    def test_arrival_times_filters_route_and_direction(self):
        self.assertEqual(subway.arrival_times(FEED, "F23N", "F"), [NOW - 600, NOW + 200, NOW + 660])

    def test_arrival_times_r(self):
        feed = NS(entity=[
            trip("R", stu("R33N", NOW + 300)),
            trip("N", stu("R33N", NOW + 100)),   # wrong route (doesn't stop here, but filter anyway)
            trip("R", stu("R33S", NOW + 50)),    # Bay Ridge-bound
            trip("F", stu("F23N", NOW + 120)),
        ])
        self.assertEqual(subway.arrival_times(feed, "R33N", "R"), [NOW + 300])

    def test_route_arrivals_uses_line_feed_and_stop(self):
        with mock.patch("subway.fetch_feed", return_value=FEED) as fetch:
            self.assertEqual(subway.route_arrivals("F"), [NOW - 600, NOW + 200, NOW + 660])
        fetch.assert_called_once_with(subway.STOPS["F"][0])

    def test_minutes_away(self):
        times = subway.arrival_times(FEED, "F23N", "F")
        self.assertEqual(subway.minutes_away(times, now=NOW), [3, 11])
        self.assertEqual(subway.minutes_away([NOW - 10], now=NOW), [0])

    def test_fetch_feed_parses_protobuf(self):
        parsed = []

        class FeedMessage(object):
            def ParseFromString(self, data):
                parsed.append(data)

        pb2 = types.ModuleType("gtfs_realtime_pb2")
        pb2.FeedMessage = FeedMessage
        transit = types.ModuleType("google.transit")
        transit.gtfs_realtime_pb2 = pb2
        fake_mods = {"google": types.ModuleType("google"), "google.transit": transit,
                     "google.transit.gtfs_realtime_pb2": pb2}
        resp = mock.Mock(content=b"pb-bytes")
        with mock.patch.dict(sys.modules, fake_mods), \
                mock.patch("subway.requests.get", return_value=resp) as get:
            subway.fetch_feed(subway.STOPS["F"][0])
        self.assertEqual(get.call_args.args[0], subway.STOPS["F"][0])
        self.assertNotIn("headers", get.call_args.kwargs)  # no API key needed
        self.assertEqual(parsed, [b"pb-bytes"])


if __name__ == "__main__":
    unittest.main()
