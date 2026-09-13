import sys
from .state import WeatherState
from agents.strategist import run_strategist_node


def _safe_print(text: str) -> None:
    """Safe print helper that prevents Windows console encoding crashes."""
    try:
        print(text)
    except (UnicodeEncodeError, UnicodeError):
        enc = getattr(sys.stdout, "encoding", None) or "utf-8"
        print(text.encode(enc, errors="replace").decode(enc))


def run_sentinel(state: WeatherState) -> WeatherState:
    _safe_print("\n👁️ Sentinel Agent running...")

    # Sentinel threat detection
    # (To be replaced with Sentinel live API detector in Member 2 integration)
    state["threat_detected"] = True

    location = state.get("location", "Jalandhar")
    state["threat"] = {
        "event_id": "EVT-20260913-001",
        "event_type": "heavy_rain",
        "severity": "high",
        "probability": 0.85,
        "confidence": "high",
        "location": location,
        "time_to_event_minutes": 30,
        "duration_hours": 3.0,
        "rainfall_mm": 60.0,
        "wind_speed_kmh": 22.0,
        "temp_c": 26.0,
        "humidity_pct": 88.0
    }

    _safe_print("⚠️ Threat detected: Heavy Rain")
    _safe_print(f"📍 Location: {location}")
    _safe_print("🌧️ Expected rainfall: 60.0 mm")
    _safe_print("⏱️ Expected in: 30 minutes")

    return state


def run_strategist(state: WeatherState) -> WeatherState:
    """
    Executes the real Strategist Agent (Agricultural Decision Engine).
    Queries FarmerDB, evaluates agronomic risk, reschedules conflicting activities,
    and generates multilingual voice scripts and dashboard telemetry.
    """
    _safe_print("\n🧠 Strategist Agent running (Real Decision Engine)...")
    return run_strategist_node(state)