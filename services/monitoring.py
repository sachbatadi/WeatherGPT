from datetime import datetime, timezone
from typing import Any, Dict, List, Callable, Optional


def get_system_health() -> Dict[str, Any]:
    """Return health metrics and status for WeatherGPT system backend services."""
    return {
        "status": "healthy",
        "system": "WeatherGPT Hybrid Engine",
        "subsystems": {
            "sentinel": "active",
            "strategist": "active",
            "executor": "active",
            "conversational": "active",
            "farmer_db": "active",
            "weather_api": "active",
        },
    }


def run_monitoring_cycle(
    farmers: List[Dict[str, Any]],
    runner_fn: Callable[[Dict[str, Any]], Dict[str, Any]],
    mode: str = "mock",
) -> Dict[str, Any]:
    """
    Run an end-to-end monitoring audit cycle across all registered farmers.
    Executes pipeline runner per location and tallies detected threats.
    """
    threats_detected = 0
    results: List[Dict[str, Any]] = []

    location_map: Dict[str, List[Dict[str, Any]]] = {}
    for f in farmers:
        loc = f.get("location") or f.get("district") or "Jalandhar"
        location_map.setdefault(loc, []).append(f)

    for loc, loc_farmers in location_map.items():
        payload = {
            "location": loc,
            "mode": mode,
        }
        res = runner_fn(payload)
        results.append(res)
        if res.get("threat_detected"):
            threats_detected += len(loc_farmers)

    return {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "mode": mode,
        "farmers_checked": len(farmers),
        "threats_detected": threats_detected,
        "results": results,
    }
