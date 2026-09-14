import sys

# Ensure UTF-8 stdout encoding for Windows console compatibility with emojis
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

from agents.orchestrator.graph import build_graph


def main():
    print("\n===================================")
    print("      🌦️ WEATHERGPT AGENT SYSTEM")
    print("===================================")

    graph = build_graph()

    initial_state = {
        "location": "Jalandhar"
    }

    print("\n📍 Starting location:", initial_state["location"])

    result = graph.invoke(initial_state)

    print("\n===================================")
    print("          FINAL RESULT")
    print("===================================")

    print("\n📍 Location:", result.get("location"))

    threat = result.get("threat", {})

    print(
        f"⚠️ Threat: "
        f"{threat.get('event_type', '').replace('_', ' ').title()} "
        f"(Event ID: {threat.get('event_id')})"
    )

    print(
        f"🌧️ Precipitation: {threat.get('rainfall_mm')} mm | "
        f"Wind: {threat.get('wind_speed_kmh')} km/h"
    )

    print(
        f"🚨 Overall Risk Level: "
        f"{str(result.get('risk_level', '')).upper()}"
    )

    print(
        f"📞 Proactive Alert Required: "
        f"{result.get('alert_required')}"
    )

    print(
        f"🔄 Re-planning Required: "
        f"{result.get('replanning_required')}"
    )

    print("\n👨‍🌾 Affected Farmers Assessed:")

    for f in result.get("affected_farmers", []):
        print(
            f"   - {f.get('name')} "
            f"(ID: {f.get('id')}) | "
            f"Crop: {f.get('crop')} "
            f"({f.get('crop_stage')}) | "
            f"Soil: {f.get('soil_type')} | "
            f"Risk Score: {f.get('risk_score')}/100 "
            f"[{f.get('risk_level').upper()}]"
        )

    print("\n📋 Recommended Action Plan:")

    for act in result.get("recommended_actions", []):
        print(f"   - {act}")

    print("\n===================================")


if __name__ == "__main__":
    main()