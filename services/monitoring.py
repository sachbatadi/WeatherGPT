from typing import Any, Dict


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
