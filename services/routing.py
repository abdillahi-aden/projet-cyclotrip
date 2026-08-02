import json
import math
import os

import requests
from shapely.errors import GEOSException
from shapely.geometry import LineString


class RouteError(Exception):
    pass


def same_location(start, end, precision=6):
    if not start or not end:
        return False
    return (
        round(float(start["lon"]), precision) == round(float(end["lon"]), precision)
        and round(float(start["lat"]), precision) == round(float(end["lat"]), precision)
    )


def get_route(start, end):
    api_key = os.getenv("ORS_API_KEY")
    if not api_key:
        raise RouteError("La clé API OpenRouteService n'est pas configurée.")

    payload = {
        "coordinates": [
            [float(start["lon"]), float(start["lat"])],
            [float(end["lon"]), float(end["lat"])],
        ],
        "elevation": True,
    }
    headers = {"Authorization": api_key, "Content-Type": "application/json"}
    url = "https://api.openrouteservice.org/v2/directions/cycling-regular/geojson"

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=20)
        response.raise_for_status()
        data = response.json()
    except requests.Timeout as exc:
        raise RouteError("Le service de calcul d'itinéraire met trop de temps à répondre.") from exc
    except requests.RequestException as exc:
        raise RouteError("Le service OpenRouteService est temporairement indisponible.") from exc
    except ValueError as exc:
        raise RouteError("La réponse OpenRouteService est illisible.") from exc

    features = data.get("features") or []
    if not features:
        raise RouteError("Aucun itinéraire cyclable n'a été trouvé entre ces deux adresses.")

    feature = features[0]
    coordinates = feature.get("geometry", {}).get("coordinates") or []
    if len(coordinates) < 2:
        raise RouteError("Aucun tracé exploitable n'a été renvoyé pour cet itinéraire.")

    try:
        route = LineString([(coord[0], coord[1]) for coord in coordinates])
    except (GEOSException, TypeError, ValueError) as exc:
        raise RouteError("Le tracé renvoyé n'a pas pu être exploité.") from exc

    properties = feature.get("properties", {})
    summary = properties.get("summary", {})
    elevation = _compute_elevation(coordinates)
    distance_m = summary.get("distance")
    duration_s = summary.get("duration")
    return {
        "line": route,
        "coordinates": coordinates,
        "distance_km": (distance_m / 1000) if distance_m else _approx_distance_km(route),
        "duration_min": (duration_s / 60) if duration_s else 0,
        "ascent_m": properties.get("ascent", elevation["ascent_m"]) or 0,
        "descent_m": properties.get("descent", elevation["descent_m"]) or 0,
        "geojson": feature,
    }


def split_route(route_line, daily_distance_km):
    if not route_line or route_line.is_empty:
        return []

    total_length = route_line.length
    total_km = _approx_distance_km(route_line)
    days = max(1, int(math.ceil(total_km / max(daily_distance_km, 1))))
    segments = []
    for index in range(days):
        start_fraction = index / days
        end_fraction = (index + 1) / days
        start = route_line.interpolate(start_fraction * total_length)
        end = route_line.interpolate(end_fraction * total_length)
        segment = LineString([start, end])
        segments.append(
            {
                "day": index + 1,
                "start": start,
                "end": end,
                "distance_km": total_km / days,
                "line": segment,
            }
        )
    return segments


def difficulty(distance_km, ascent_m):
    ascent_m = ascent_m or 0
    if distance_km < 25 and ascent_m < 250:
        return "Facile"
    if distance_km < 60 and ascent_m < 800:
        return "Intermédiaire"
    return "Sportif"


def route_geojson(feature):
    return json.dumps(feature, ensure_ascii=False, indent=2)


def route_gpx(route):
    points = "\n".join(
        f'      <trkpt lat="{lat:.7f}" lon="{lon:.7f}"></trkpt>'
        for lon, lat in route["line"].coords
    )
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="CycloTrip" xmlns="http://www.topografix.com/GPX/1/1">
  <trk>
    <name>CycloTrip itinerary</name>
    <trkseg>
{points}
    </trkseg>
  </trk>
</gpx>
"""


def _compute_elevation(coordinates):
    ascent = 0
    descent = 0
    elevations = [coord[2] for coord in coordinates if len(coord) >= 3 and coord[2] is not None]
    for previous, current in zip(elevations, elevations[1:]):
        diff = current - previous
        if diff > 0:
            ascent += diff
        else:
            descent += abs(diff)
    return {"ascent_m": round(ascent, 1), "descent_m": round(descent, 1)}


def _approx_distance_km(line):
    return line.length * 111
