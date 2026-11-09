"""Live bus arrivals from the MTA Bus Time SIRI API."""
import os

import requests

MTA_API_BASE = "https://bustime.mta.info/api/siri/stop-monitoring.json"
STOP_ID = "402003"
API_KEY_ENV = "MTA_BUS_API_KEY"


def _api_key():
    key = os.environ.get(API_KEY_ENV)
    if not key:
        raise RuntimeError(
            "Set the %s environment variable to your MTA Bus Time API key "
            "(request one at https://register.developer.obanyc.com/)." % API_KEY_ENV)
    return key


def nyc_current(stop_id=STOP_ID):
    params = {"key": _api_key(), "MonitoringRef": stop_id}
    resp = requests.get(MTA_API_BASE, params=params, timeout=10)
    if resp.status_code == 403:
        raise RuntimeError("MTA Bus Time rejected the API key in %s." % API_KEY_ENV)
    resp.raise_for_status()
    info = resp.json()['Siri']['ServiceDelivery']['StopMonitoringDelivery']
    return [_flatten_dict('', i, {}) for i in info]


def _flatten_dict(root_key, nested_dict, flattened_dict):
    for key, value in nested_dict.items():
        next_key = root_key + "_" + key if root_key != "" else key
        if isinstance(value, dict):
            _flatten_dict(next_key, value, flattened_dict)
        else:
            flattened_dict[next_key] = value
    return flattened_dict


def get_time_strings(current):
    """Return (parsed_visits, ["LINE: distance", ...]) with one string per line."""
    parsed_visits = []
    for thing in current:
        for v in thing.get('MonitoredStopVisit', []):
            flu = v['MonitoredVehicleJourney']
            call = flu.get('MonitoredCall', {})
            distance = (call.get('Extensions', {})
                            .get('Distances', {})
                            .get('PresentableDistance', ''))
            parsed_visits.append([
                distance,
                flu['PublishedLineName'],
                call.get('ExpectedArrivalTime'),
            ])

    lines_to_print = {}
    for distance, line, _ in parsed_visits:
        if line not in lines_to_print:
            lines_to_print[line] = "%s: %s" % (line, distance)

    return parsed_visits, list(lines_to_print.values())


if __name__ == "__main__":
    import time
    while True:
        print(get_time_strings(nyc_current())[1])
        time.sleep(10)
