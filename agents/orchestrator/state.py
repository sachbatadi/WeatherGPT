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

    # Strategist and downstream payloads
    strategist_output: Dict[str, Any]
    radio_gpt_payload: List[Dict[str, Any]]
    dashboard_payload: List[Dict[str, Any]]
    strategist_assessments: List[Dict[str, Any]]

    # Executor outputs
    execution_summary: Dict[str, Any]
    dispatched_alerts: List[Dict[str, Any]]
    applied_plan_updates: List[Dict[str, Any]]
    calendar_operations: List[Dict[str, Any]]
    executor_output: Dict[str, Any]