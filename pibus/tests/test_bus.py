import os
import unittest
from unittest import mock

import bus

# Trimmed real response shape from bustime.mta.info stop-monitoring.json.
SAMPLE = {"Siri": {"ServiceDelivery": {"StopMonitoringDelivery": [{
    "ResponseTimestamp": "2026-11-08T21:04:59.214-05:00",
    "MonitoredStopVisit": [
        {"MonitoredVehicleJourney": {"PublishedLineName": "M102", "MonitoredCall": {
            "ExpectedArrivalTime": "2026-11-08T21:09:46.329-05:00",
            "Extensions": {"Distances": {"PresentableDistance": "0.8 miles away"}}}}},
        {"MonitoredVehicleJourney": {"PublishedLineName": "M101", "MonitoredCall": {
            "Extensions": {"Distances": {"PresentableDistance": "approaching"}}}}},
        {"MonitoredVehicleJourney": {"PublishedLineName": "M102", "MonitoredCall": {
            "Extensions": {"Distances": {"PresentableDistance": "2 stops away"}}}}},
    ],
}]}}}


def fake_response(status=200, payload=SAMPLE):
    resp = mock.Mock(status_code=status)
    resp.json.return_value = payload
    return resp


class BusTest(unittest.TestCase):
    def test_flatten_dict(self):
        self.assertEqual(bus._flatten_dict("", {"a": {"b": 1}, "c": 2}, {}),
                         {"a_b": 1, "c": 2})

    @mock.patch.dict(os.environ, {"MTA_BUS_API_KEY": "k"})
    @mock.patch("bus.requests.get", return_value=fake_response())
    def test_nyc_current_and_strings(self, get):
        visits, strings = bus.get_time_strings(bus.nyc_current())
        self.assertEqual(get.call_args.kwargs["params"],
                         {"key": "k", "MonitoringRef": "402003"})
        self.assertTrue(get.call_args.args[0].startswith("https://"))
        self.assertEqual(len(visits), 3)
        self.assertIsNone(visits[1][2])
        # First visit per line wins.
        self.assertEqual(strings, ["M102: 0.8 miles away", "M101: approaching"])

    @mock.patch.dict(os.environ, {"MTA_BUS_API_KEY": "bad"})
    @mock.patch("bus.requests.get", return_value=fake_response(status=403))
    def test_rejected_key(self, _):
        with self.assertRaisesRegex(RuntimeError, "rejected"):
            bus.nyc_current()

    @mock.patch.dict(os.environ, {}, clear=True)
    def test_missing_key(self):
        with self.assertRaisesRegex(RuntimeError, "MTA_BUS_API_KEY"):
            bus.nyc_current()


if __name__ == "__main__":
    unittest.main()
