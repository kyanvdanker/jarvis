import requests

NS_API_KEY = "d60326b6bcd44d31b52ddf83b02b5daf"

def check_train_delay(from_station, to_station, planned_time):
    url = "https://gateway.apiportal.ns.nl/reisinformatie-api/api/v2/departures"
    headers = {"Ocp-Apim-Subscription-Key": NS_API_KEY}
    params = {"station": from_station}

    r = requests.get(url, headers=headers, params=params)
    data = r.json()

    for dep in data["payload"]["departures"]:
        if dep["direction"].lower() == to_station.lower():
            planned = dep["plannedDateTime"]
            actual = dep["actualDateTime"]
            delay = dep["delayInSeconds"]

            return {
                "planned": planned,
                "actual": actual,
                "delay": delay
            }

    return None
