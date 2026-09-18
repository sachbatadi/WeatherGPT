import requests
from typing import Dict, Any, Optional


GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

DEFAULT_LOCATION = "Jalandhar"
DEFAULT_LATITUDE = 31.3260
DEFAULT_LONGITUDE = 75.5762


def geocode_location(location: str) -> Dict[str, Any]:
    clean_loc = (location or "").strip()
    if not clean_loc:
        raise ValueError("Location name must not be empty.")

    try:
        response = requests.get(
            GEOCODING_URL,
            params={
                "name": clean_loc,
                "count": 1,
                "language": "en",
                "format": "json",
            },
            timeout=10,
        )
        response.raise_for_status()
    except requests.exceptions.Timeout as exc:
        raise TimeoutError(f"Geocoding service timed out for location '{clean_loc}'.") from exc
    except requests.exceptions.RequestException as exc:
        raise ConnectionError(f"Geocoding network error for '{clean_loc}': {exc}") from exc

    data = response.json()
    results = data.get("results", [])

    if not results:
        raise ValueError(f"Location not found: '{clean_loc}'")

    result = results[0]

    return {
        "name": result.get("name", clean_loc),
        "latitude": float(result["latitude"]),
        "longitude": float(result["longitude"]),
        "country": result.get("country"),
        "admin1": result.get("admin1"),
        "timezone": result.get("timezone", "Asia/Kolkata"),
    }


def fetch_weather(
    location: str = DEFAULT_LOCATION,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
) -> Dict[str, Any]:

    if latitude is None or longitude is None:
        location_info = geocode_location(location)
        latitude = location_info["latitude"]
        longitude = location_info["longitude"]
    else:
        location_info = {
            "name": location,
            "latitude": latitude,
            "longitude": longitude,
            "country": "India",
            "admin1": "Punjab",
            "timezone": "Asia/Kolkata",
        }

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": ",".join([
            "temperature_2m",
            "relative_humidity_2m",
            "precipitation",
            "rain",
            "showers",
            "weather_code",
            "wind_speed_10m",
            "wind_gusts_10m",
        ]),
        "hourly": ",".join([
            "temperature_2m",
            "relative_humidity_2m",
            "precipitation_probability",
            "precipitation",
            "rain",
            "showers",
            "weather_code",
            "wind_speed_10m",
            "wind_gusts_10m",
        ]),
        "forecast_hours": 12,
        "timezone": "auto",
    }

    try:
        response = requests.get(
            FORECAST_URL,
            params=params,
            timeout=15,
        )
        response.raise_for_status()
    except requests.exceptions.Timeout as exc:
        raise TimeoutError(f"Weather forecast service timed out for location '{location}'.") from exc
    except requests.exceptions.RequestException as exc:
        raise ConnectionError(f"Weather forecast request failed for '{location}': {exc}") from exc

    raw = response.json()

    current = raw.get("current", {})
    hourly = raw.get("hourly", {})

    return {
        "source": "open-meteo",
        "location": location_info["name"],
        "coordinates": {
            "latitude": latitude,
            "longitude": longitude,
        },
        "timezone": raw.get(
            "timezone",
            location_info.get("timezone", "Asia/Kolkata"),
        ),
        "current": {
            "time": current.get("time"),
            "temperature_c": current.get("temperature_2m"),
            "humidity_pct": current.get("relative_humidity_2m"),
            "precipitation_mm": current.get("precipitation"),
            "rain_mm": current.get("rain"),
            "showers_mm": current.get("showers"),
            "weather_code": current.get("weather_code"),
            "wind_speed_kmh": current.get("wind_speed_10m"),
            "wind_gust_kmh": current.get("wind_gusts_10m"),
        },
        "hourly": {
            "time": hourly.get("time", []),
            "temperature_c": hourly.get("temperature_2m", []),
            "humidity_pct": hourly.get("relative_humidity_2m", []),
            "precipitation_probability_pct": hourly.get(
                "precipitation_probability",
                [],
            ),
            "precipitation_mm": hourly.get(
                "precipitation",
                [],
            ),
            "rain_mm": hourly.get("rain", []),
            "showers_mm": hourly.get("showers", []),
            "weather_code": hourly.get("weather_code", []),
            "wind_speed_kmh": hourly.get(
                "wind_speed_10m",
                [],
            ),
            "wind_gust_kmh": hourly.get(
                "wind_gusts_10m",
                [],
            ),
        },
    }