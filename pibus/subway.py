"""Live subway arrivals from the MTA GTFS-realtime feeds (no API key needed)."""
import time

import requests

FEED_BASE = "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2F"

# Manhattan-bound stops at 4 Av-9 St, by route: (feed URL, stop ID).
# The F/G platform (F23) and the R platform (R33) have separate stop IDs.
# The "N" suffix is northbound, which for both lines here is Manhattan-bound.
# The G also stops at F23N; arrival_times() filters on route, so it drops out.
STOPS = {
    "F": (FEED_BASE + "gtfs-bdfm", "F23N"),
    "R": (FEED_BASE + "gtfs-nqrw", "R33N"),
}


def fetch_feed(url):
    from google.transit import gtfs_realtime_pb2

    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    feed = gtfs_realtime_pb2.FeedMessage()
    feed.ParseFromString(resp.content)
    return feed


def arrival_times(feed, stop_id, route_id):
    """Sorted POSIX arrival times of route_id trains at stop_id."""
    times = []
    for entity in feed.entity:
        # Unset protobuf fields read as empty defaults, so non-trip-update
        # entities fall out at the route check.
        trip_update = entity.trip_update
        if trip_update.trip.route_id != route_id:
            continue
        for stu in trip_update.stop_time_update:
            if stu.stop_id != stop_id:
                continue
            t = stu.arrival.time or stu.departure.time
            if t:
                times.append(t)
    return sorted(times)


def route_arrivals(route_id):
    """Sorted arrival times of the next Manhattan-bound route_id trains at 4 Av-9 St."""
    url, stop_id = STOPS[route_id]
    return arrival_times(fetch_feed(url), stop_id, route_id)


def minutes_away(times, now=None):
    now = time.time() if now is None else now
    return [max(0, int((t - now) // 60)) for t in times if t > now - 30]


if __name__ == "__main__":
    while True:
        for route in STOPS:
            print("Manhattan-bound %s at 4 Av-9 St:" % route, minutes_away(route_arrivals(route)))
        time.sleep(30)
