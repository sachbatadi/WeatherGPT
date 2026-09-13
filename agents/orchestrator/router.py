from .state import WeatherState


def threat_router(state: WeatherState) -> str:
    """
    Decide what the Orchestrator should do after Sentinel runs.
    """

    if state.get("threat_detected", False):
        print("\n🚨 Threat detected → Sending to Strategist")
        return "strategist"

    print("\n✅ No significant threat → Continue monitoring")
    return "monitor"