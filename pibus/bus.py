import requests

MTA_API_KEY="7a186bb8-a8f5-4fad-a8b7-6ec4dcd79505"
MTA_API_BASE = "http://bustime.mta.info/api/siri/stop-monitoring.json"
#This is useful for the live MTA Data
params = {"key": MTA_API_KEY, }
STOP_ID="402003"
params["MonitoringRef"] = STOP_ID
def nyc_current():
    resp = requests.get(MTA_API_BASE, params=params).json()
    info = resp['Siri']['ServiceDelivery']['StopMonitoringDelivery']
    return [_flatten_dict('', i, {}) for i in info]

def _flatten_dict(root_key, nested_dict, flattened_dict):
    for key, value in nested_dict.iteritems():
        next_key = root_key + "_" + key if root_key != "" else key
        if isinstance(value, dict):
            _flatten_dict(next_key, value, flattened_dict)
        else:
            flattened_dict[next_key] = value
    return flattened_dict


def get_time_strings(current):
    for thing in current:
        visits = thing['MonitoredStopVisit']
        parsed_visits = []
        for v in visits:
            flu = v['MonitoredVehicleJourney']
	    parsed_visits.append([
              flu['MonitoredCall']['Extensions']['Distances']['PresentableDistance'],
	      flu['PublishedLineName'],
flu['MonitoredCall']['ExpectedArrivalTime'] if 'ExpectedArrivalTime' in flu['MonitoredCall'] else None])
    print "==================="
    print "==================="
    print parsed_visits
    print "==================="
    lines_to_print = {}
    for v in parsed_visits:
      if v[1] not in lines_to_print:
        lines_to_print[v[1]] = ": ".join(v[1::-1])

    return parsed_visits, lines_to_print.values()

if __name__ == "__main__":
    import time
    while True:
        info = None
        if info is None:
	    info = nyc_current()
        print get_time_strings(info)
	time.sleep(10)
