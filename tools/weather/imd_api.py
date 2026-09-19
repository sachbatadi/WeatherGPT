import os
from typing import Any, Dict, Optional

import requests
from dotenv import load_dotenv


load_dotenv()


IMD_API_BASE_URL = os.getenv(
    "IMD_API_BASE_URL",
    "https://api.imd.gov.in",
).rstrip("/")

IMD_API_KEY = os.getenv("IMD_API_KEY", "").strip()

DEFAULT_STATION_ID = os.getenv("IMD_STATION_ID", "").strip()

REQUEST_TIMEOUT = 15


def _headers() -> Dict[str, str]:
    """
    Build request headers for IMD API.

    The API key is optional here because the exact authentication
    mechanism depends on the IMD API access granted to the account.
    """

    headers = {
        "Accept": "application/json",
        "User-Agent": "WeatherGPT-SIH/1.0",
    }

    if IMD_API_KEY:
        headers["Authorization"] = f"Bearer {IMD_API_KEY}"

    return headers


def _get(
    endpoint: str,
    params: Optional[Dict[str, Any]] = None,
) -> Any:
    """
    Generic GET request helper for IMD APIs.
    """

    url = f"{IMD_API_BASE_URL}{endpoint}"

    response = requests.get(
        url,
        params=params,
        headers=_headers(),
        timeout=REQUEST_TIMEOUT,
    )

    response.raise_for_status()

    return response.json()


def fetch_current_weather(
    station_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Fetch current weather observations from IMD.

    IMD endpoint:
        /api/v1/current_wx

    Optional station:
        /api/v1/current_wx?id=<StationId>
    """

    station_id = station_id or DEFAULT_STATION_ID

    params = {}

    if station_id:
        params["id"] = station_id

    raw = _get(
        "/api/v1/current_wx",
        params=params,
    )

    return {
        "source": "imd",
        "api": "current_weather",
        "raw": raw,
    }


def fetch_city_forecast(
    station_id: str,
) -> Dict[str, Any]:
    """
    Fetch 7-day city weather forecast from IMD.
    """

    raw = _get(
        "/api/v1/cityforecast",
        params={"id": station_id},
    )

    return {
        "source": "imd",
        "api": "city_forecast",
        "station_id": station_id,
        "raw": raw,
    }


def fetch_city_forecast_location(
    station_id: str,
) -> Dict[str, Any]:
    """
    Fetch 7-day city forecast including latitude
    and longitude information.
    """

    raw = _get(
        "/api/v1/cityforecastloc",
        params={"id": station_id},
    )

    return {
        "source": "imd",
        "api": "city_forecast_location",
        "station_id": station_id,
        "raw": raw,
    }


def fetch_district_nowcast(
    district_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Fetch district-wise nowcast information.

    IMD provides categories for:
    - Heavy rain
    - Thunderstorms
    - Lightning
    - Strong winds
    - Hail
    - Dust storms
    """

    params = {}

    if district_id:
        params["id"] = district_id

    raw = _get(
        "/api/v1/districtnowcast",
        params=params,
    )

    return {
        "source": "imd",
        "api": "district_nowcast",
        "district_id": district_id,
        "raw": raw,
    }


def fetch_district_warning(
    district_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Fetch district-wise weather warnings.

    IMD warning codes include:
    1  - No warning
    2  - Heavy rain
    4  - Thunderstorm & lightning
    5  - Hailstorm
    8  - Strong surface winds
    9  - Heat wave
    12 - Cold wave
    16 - Very heavy rain
    17 - Extremely heavy rain
    """

    params = {}

    if district_id:
        params["id"] = district_id

    raw = _get(
        "/api/v1/districtwarning",
        params=params,
    )

    return {
        "source": "imd",
        "api": "district_warning",
        "district_id": district_id,
        "raw": raw,
    }


def fetch_district_rainfall(
    district_id: str,
) -> Dict[str, Any]:
    """
    Fetch district rainfall information from IMD.
    """

    raw = _get(
        "/api/v1/districtrainfall",
        params={"id": district_id},
    )

    return {
        "source": "imd",
        "api": "district_rainfall",
        "district_id": district_id,
        "raw": raw,
    }


def fetch_aws_data(
    station_code: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Fetch AWS/ARG observation data from IMD.

    Example:
        /api/v1/aws_data?id=NDL
    """

    params = {}

    if station_code:
        params["id"] = station_code

    raw = _get(
        "/api/v1/aws_data",
        params=params,
    )

    return {
        "source": "imd",
        "api": "aws_data",
        "station_code": station_code,
        "raw": raw,
    }


def fetch_imd_weather_bundle(
    station_id: Optional[str] = None,
    district_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Collect the main IMD weather intelligence sources
    required by WeatherGPT.

    This function is intentionally separated from Sentinel.
    Sentinel can decide later which sources to use.
    """

    bundle: Dict[str, Any] = {
        "source": "imd",
        "current_weather": None,
        "forecast": None,
        "nowcast": None,
        "warnings": None,
    }

    bundle["current_weather"] = fetch_current_weather(
        station_id=station_id,
    )

    if station_id:
        bundle["forecast"] = fetch_city_forecast(
            station_id=station_id,
        )

    if district_id:
        bundle["nowcast"] = fetch_district_nowcast(
            district_id=district_id,
        )

        bundle["warnings"] = fetch_district_warning(
            district_id=district_id,
        )

    return bundle


if __name__ == "__main__":
    print("WeatherGPT IMD API Adapter")
    print("=" * 40)
    print(f"Base URL: {IMD_API_BASE_URL}")

    if not IMD_API_KEY:
        print("IMD API key: not configured")
    else:
        print("IMD API key: configured")

    if not DEFAULT_STATION_ID:
        print("IMD station ID: not configured")
    else:
        print(f"IMD station ID: {DEFAULT_STATION_ID}")