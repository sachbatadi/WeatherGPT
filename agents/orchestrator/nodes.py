from .state import WeatherState


def run_sentinel(state: WeatherState) -> WeatherState:
    print("\n👁️ Sentinel Agent running...")

    # Temporary mock data.
    # Later this will be replaced by your friend's real Sentinel Agent.
    state["threat_detected"] = True

    state["threat"] = {
        "event_id": "EVT001",
        "event_type": "heavy_rain",
        "severity": "high",
        "probability": 0.85,
        "location": state["location"],
        "time_to_event_minutes": 30,
        "rainfall_mm": 60
    }

    print("⚠️ Threat detected: Heavy Rain")
    print(f"📍 Location: {state['location']}")
    print("🌧️ Expected rainfall: 60 mm")
    print("⏱️ Expected in: 30 minutes")

    return state


def run_strategist(state: WeatherState) -> WeatherState:
    print("\n🧠 Strategist Agent running...")

    # Temporary mock data.
    # Later this will be replaced by your friend's real Strategist Agent.
    state["affected_farmers"] = [
        {
            "id": "F001",
            "crop": "Wheat",
            "crop_stage": "Flowering"
        },
        {
            "id": "F002",
            "crop": "Wheat",
            "crop_stage": "Flowering"
        }
    ]

    state["risk_level"] = "high"

    state["recommended_actions"] = [
        "Stop pesticide spraying",
        "Prepare field drainage",
        "Protect harvested produce"
    ]

    state["alert_required"] = True

    print("👨‍🌾 Affected farmers: 2")
    print("🚨 Risk level: HIGH")
    print("📋 Action plan generated")

    return state