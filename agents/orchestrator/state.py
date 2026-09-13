from typing import TypedDict, List, Dict, Any


class WeatherState(TypedDict, total=False):
    location: str

    weather_data: Dict[str, Any]

    threat_detected: bool
    threat: Dict[str, Any]

    affected_farmers: List[Dict[str, Any]]

    risk_level: str
    recommended_actions: List[str]

    alert_required: bool
    alert_status: str

    replanning_required: bool