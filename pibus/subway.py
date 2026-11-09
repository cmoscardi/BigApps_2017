"""Live subway arrivals from the MTA GTFS-realtime feeds (no API key needed)."""
import time

import requests

# B, D, F, M feed.
FEED_URL = "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-bdfm"
# 4 Av-9 St (F/G). The "N" suffix is northbound, which for the F is Manhattan-bound.
STOP_ID = "F23N"
# The G also stops at F23N, so filter on route.
ROUTE_IDS = ("F",)


def fetch_feed(url=FEED_URL):
    from google.transit import gtfs_realtime_pb2

    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    feed = gtfs_realtime_pb2.FeedMessage()
    feed.ParseFromString(resp.content)
    return feed


def arrival_times(feed, stop_id=STOP_ID, route_ids=ROUTE_IDS):
    """Sorted POSIX arrival times at stop_id for the given routes."""
    times = []
    for entity in feed.entity:
        # Unset protobuf fields read as empty defaults, so non-trip-update
        # entities fall out at the route check.
        trip_update = entity.trip_update
        if trip_update.trip.route_id not in route_ids:
            continue
        for stu in trip_update.stop_time_update:
            if stu.stop_id != stop_id:
                continue
            t = stu.arrival.time or stu.departure.time
            if t:
                times.append(t)
    return sorted(times)


def minutes_away(times, now=None):
    now = time.time() if now is None else now
    return [max(0, int((t - now) // 60)) for t in times if t > now - 30]


def next_trains(now=None):
    """Minutes until the next Manhattan-bound F trains at 4 Av-9 St."""
    return minutes_away(arrival_times(fetch_feed()), now=now)


if __name__ == "__main__":
    while True:
        print("Manhattan-bound F at 4 Av-9 St:", next_trains())
        time.sleep(30)
