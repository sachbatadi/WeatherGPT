import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List

from .state import WeatherState
from agents.strategist import run_strategist_node
from tools.weather.weather_api import fetch_weather


def _safe_print(text: str) -> None:
    """Safe print helper that prevents Windows console encoding crashes."""
    try:
        print(text)
    except (UnicodeEncodeError, UnicodeError):
        enc = getattr(sys.stdout, "encoding", None) or "utf-8"
        print(text.encode(enc, errors="replace").decode(enc))


def _generate_event_id() -> str:
    """
    Generate a unique threat event ID.
    """
    now = datetime.now(timezone.utc)

    return f"EVT-{now.strftime('%Y%m%d')}-{now.strftime('%H%M%S')}"


def _mock_weather(location: str) -> Dict[str, Any]:
    """
    Deterministic SIH demonstration scenario.

    This preserves the original heavy-rain scenario so the team
    can demonstrate Strategist + Executor even when live weather
    does not contain a threat.
    """

    return {
        "source": "mock",

        "location": location,

        "coordinates": {
            "latitude": 31.3260,
            "longitude": 75.5762,
        },

        "current": {
            "time": datetime.now(timezone.utc).isoformat(),
            "temperature_c": 26.0,
            "humidity_pct": 88.0,
            "precipitation_mm": 0.0,
            "rain_mm": 0.0,
            "showers_mm": 0.0,
            "weather_code": 65,
            "wind_speed_kmh": 22.0,
            "wind_gust_kmh": 32.0,
        },

        "hourly": {
            "time": [],
            "temperature_c": [26.0],
            "humidity_pct": [88.0],
            "precipitation_probability_pct": [85.0],
            "precipitation_mm": [60.0],
            "rain_mm": [60.0],
            "showers_mm": [0.0],
            "weather_code": [65],
            "wind_speed_kmh": [22.0],
            "wind_gust_kmh": [32.0],
        },
    }


def _detect_threat(
    weather: Dict[str, Any],
    location: str,
) -> Dict[str, Any]:
    """
    Convert raw weather data into the Sentinel ThreatEvent contract.

    Detection rules are intentionally simple and explainable.
    They can later be replaced by the team's more advanced
    multi-model Sentinel detector.
    """

    current = weather.get("current", {})
    hourly = weather.get("hourly", {})

    precipitation = hourly.get("precipitation_mm", [])
    rain = hourly.get("rain_mm", [])
    precipitation_probability = hourly.get(
        "precipitation_probability_pct",
        [],
    )

    wind_speeds = hourly.get("wind_speed_kmh", [])
    wind_gusts = hourly.get("wind_gust_kmh", [])

    temperatures = hourly.get("temperature_c", [])

    # Normalize missing data.
    precipitation = [
        float(value or 0)
        for value in precipitation
    ]

    rain = [
        float(value or 0)
        for value in rain
    ]

    precipitation_probability = [
        float(value or 0)
        for value in precipitation_probability
    ]

    wind_speeds = [
        float(value or 0)
        for value in wind_speeds
    ]

    wind_gusts = [
        float(value or 0)
        for value in wind_gusts
    ]

    temperatures = [
        float(value or 0)
        for value in temperatures
    ]

    # ---------------------------------------------------------
    # Heavy rain detection
    # ---------------------------------------------------------

    # Look at the next 3 forecast hours.
    next_three_rain = sum(precipitation[:3])

    max_rain_probability = max(
        precipitation_probability[:3],
        default=0.0,
    )

    heavy_rain_detected = (
        next_three_rain >= 25.0
        and max_rain_probability >= 50.0
    )

    # ---------------------------------------------------------
    # High wind detection
    # ---------------------------------------------------------

    max_wind = max(
        wind_speeds[:3],
        default=float(current.get("wind_speed_kmh") or 0),
    )

    max_gust = max(
        wind_gusts[:3],
        default=float(current.get("wind_gust_kmh") or 0),
    )

    high_wind_detected = (
        max_wind >= 40.0
        or max_gust >= 60.0
    )

    # ---------------------------------------------------------
    # Extreme heat detection
    # ---------------------------------------------------------

    max_temperature = max(
        temperatures[:6],
        default=float(current.get("temperature_c") or 0),
    )

    extreme_heat_detected = max_temperature >= 40.0

    # ---------------------------------------------------------
    # Select threat
    # ---------------------------------------------------------

    if heavy_rain_detected:

        probability = max_rain_probability / 100.0

        if next_three_rain >= 50:
            severity = "critical"
        elif next_three_rain >= 35:
            severity = "high"
        else:
            severity = "medium"

        event_type = "heavy_rain"

        rainfall_mm = round(next_three_rain, 1)

        # Find approximately when significant rainfall begins.
        time_to_event_minutes = 60

        for index, value in enumerate(precipitation[:3]):
            if value >= 5:
                time_to_event_minutes = max(
                    15,
                    index * 60,
                )
                break

        return {
            "event_id": _generate_event_id(),
            "event_type": event_type,
            "severity": severity,
            "probability": round(probability, 2),
            "confidence": "high" if probability >= 0.70 else "medium",
            "confidence_reason": (
                "Forecast indicates significant precipitation "
                "with elevated precipitation probability."
            ),
            "location": location,
            "coordinates": weather.get("coordinates"),
            "time_to_event_minutes": time_to_event_minutes,
            "duration_hours": 3.0,
            "rainfall_mm": rainfall_mm,
            "wind_speed_kmh": round(max_wind, 1),
            "wind_gust_kmh": round(max_gust, 1),
            "temp_c": current.get("temperature_c"),
            "temp_max_c": max_temperature,
            "temp_min_c": min(temperatures, default=None),
            "humidity_pct": current.get("humidity_pct"),
            "hail_risk": False,
            "metadata": {
                "source": weather.get("source"),
                "detection_method": "rule_based",
                "three_hour_precipitation_mm": rainfall_mm,
                "max_precipitation_probability_pct": max_rain_probability,
            },
        }

    if high_wind_detected:

        probability = 0.75

        severity = (
            "critical"
            if max_gust >= 80
            else "high"
        )

        return {
            "event_id": _generate_event_id(),
            "event_type": "high_wind",
            "severity": severity,
            "probability": probability,
            "confidence": "high",
            "confidence_reason": (
                "Forecast wind speed or gusts exceed the "
                "configured safety threshold."
            ),
            "location": location,
            "coordinates": weather.get("coordinates"),
            "time_to_event_minutes": 60,
            "duration_hours": 2.0,
            "rainfall_mm": round(next_three_rain, 1),
            "wind_speed_kmh": round(max_wind, 1),
            "wind_gust_kmh": round(max_gust, 1),
            "temp_c": current.get("temperature_c"),
            "temp_max_c": max_temperature,
            "temp_min_c": min(temperatures, default=None),
            "humidity_pct": current.get("humidity_pct"),
            "hail_risk": False,
            "metadata": {
                "source": weather.get("source"),
                "detection_method": "rule_based",
            },
        }

    if extreme_heat_detected:

        probability = 0.80

        return {
            "event_id": _generate_event_id(),
            "event_type": "extreme_heat",
            "severity": "high",
            "probability": probability,
            "confidence": "high",
            "confidence_reason": (
                "Forecast maximum temperature exceeds "
                "the configured extreme-heat threshold."
            ),
            "location": location,
            "coordinates": weather.get("coordinates"),
            "time_to_event_minutes": 60,
            "duration_hours": 6.0,
            "rainfall_mm": round(next_three_rain, 1),
            "wind_speed_kmh": round(max_wind, 1),
            "wind_gust_kmh": round(max_gust, 1),
            "temp_c": current.get("temperature_c"),
            "temp_max_c": max_temperature,
            "temp_min_c": min(temperatures, default=None),
            "humidity_pct": current.get("humidity_pct"),
            "hail_risk": False,
            "metadata": {
                "source": weather.get("source"),
                "detection_method": "rule_based",
            },
        }

    # ---------------------------------------------------------
    # No threat
    # ---------------------------------------------------------

    return {
        "event_id": _generate_event_id(),
        "event_type": "none",
        "severity": "low",
        "probability": 0.0,
        "confidence": "high",
        "confidence_reason": (
            "No configured severe-weather threshold "
            "was exceeded."
        ),
        "location": location,
        "coordinates": weather.get("coordinates"),
        "time_to_event_minutes": None,
        "duration_hours": None,
        "rainfall_mm": round(next_three_rain, 1),
        "wind_speed_kmh": round(max_wind, 1),
        "wind_gust_kmh": round(max_gust, 1),
        "temp_c": current.get("temperature_c"),
        "temp_max_c": max_temperature,
        "temp_min_c": min(temperatures, default=None),
        "humidity_pct": current.get("humidity_pct"),
        "hail_risk": False,
        "metadata": {
            "source": weather.get("source"),
            "detection_method": "rule_based",
        },
    }


def run_sentinel(state: WeatherState) -> WeatherState:
    """
    Sentinel Agent.

    WEATHER_MODE=live:
        Fetch live weather from Open-Meteo.

    WEATHER_MODE=mock:
        Use deterministic SIH disaster scenario.
    """

    _safe_print("\n👁️ Sentinel Agent running...")

    location = state.get("location", "Jalandhar")

    weather_mode = os.getenv(
        "WEATHER_MODE",
        "mock",
    ).strip().lower()

    # ---------------------------------------------------------
    # Get weather
    # ---------------------------------------------------------

    if weather_mode == "live":

        _safe_print("🌐 Weather source: Open-Meteo LIVE API")

        try:
            weather = fetch_weather(location)

        except Exception as exc:

            _safe_print(
                f"⚠️ Live weather API failed: {exc}"
            )

            _safe_print(
                "🔄 Falling back to mock Sentinel scenario..."
            )

            weather = _mock_weather(location)

    else:

        _safe_print(
            "🧪 Weather source: MOCK SIH DEMO"
        )

        weather = _mock_weather(location)

    # Save raw weather in shared state.
    state["weather_data"] = weather

    # ---------------------------------------------------------
    # Detect threat
    # ---------------------------------------------------------

    threat = _detect_threat(
        weather,
        location,
    )

    state["threat"] = threat

    threat_detected = (
        threat["event_type"] != "none"
    )

    state["threat_detected"] = threat_detected

    # ---------------------------------------------------------
    # Console output
    # ---------------------------------------------------------

    if threat_detected:

        event_name = (
            threat["event_type"]
            .replace("_", " ")
            .title()
        )

        _safe_print(
            f"⚠️ Threat detected: {event_name}"
        )

        _safe_print(
            f"📍 Location: {location}"
        )

        if threat.get("rainfall_mm") is not None:
            _safe_print(
                f"🌧️ Expected rainfall: "
                f"{threat['rainfall_mm']} mm"
            )

        if threat.get("wind_speed_kmh") is not None:
            _safe_print(
                f"💨 Wind speed: "
                f"{threat['wind_speed_kmh']} km/h"
            )

        if threat.get("time_to_event_minutes") is not None:
            _safe_print(
                f"⏱️ Expected in: "
                f"{threat['time_to_event_minutes']} minutes"
            )

        _safe_print(
            "\n🚨 Threat detected → Sending to Strategist"
        )

    else:

        _safe_print(
            "✅ No severe weather threat detected."
        )

        _safe_print(
            "📡 Sentinel will continue monitoring."
        )

    return state


def run_strategist(state: WeatherState) -> WeatherState:
    """
    Executes the real Strategist Agent (Agricultural Decision Engine).
    Queries FarmerDB, evaluates agronomic risk, reschedules conflicting activities,
    and generates multilingual voice scripts and dashboard telemetry.
    """

    _safe_print(
        "\n🧠 Strategist Agent running "
        "(Real Decision Engine)..."
    )

    return run_strategist_node(state)