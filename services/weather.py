import os

import requests


def get_weather(lat, lon):
    api_key = os.getenv("WEATHER_API_KEY")
    if not api_key:
        return None

    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {"lat": lat, "lon": lon, "appid": api_key, "units": "metric", "lang": "fr"}
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except (requests.RequestException, ValueError):
        return None


def format_weather(data):
    if not data:
        return "Météo indisponible"
    temp = data.get("main", {}).get("temp")
    conditions = (data.get("weather") or [{}])[0].get("description", "conditions non précisées")
    wind = data.get("wind", {}).get("speed")
    parts = []
    if temp is not None:
        parts.append(f"{temp:.0f} °C")
    parts.append(conditions)
    if wind is not None:
        parts.append(f"vent {wind * 3.6:.0f} km/h")
    return " - ".join(parts)
