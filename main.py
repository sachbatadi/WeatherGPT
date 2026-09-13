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
    print(f"⚠️ Threat: {threat.get('event_type', '').replace('_', ' ').title()} (Event ID: {threat.get('event_id')})")
    print(f"🌧️ Precipitation: {threat.get('rainfall_mm')} mm | Wind: {threat.get('wind_speed_kmh')} km/h")
    print(f"🚨 Overall Risk Level: {str(result.get('risk_level', '')).upper()}")
    print(f"📞 Proactive Alert Required: {result.get('alert_required')}")
    print(f"🔄 Re-planning Required: {result.get('replanning_required')}")

    print("\n👨‍🌾 Affected Farmers Assessed:")
    for f in result.get("affected_farmers", []):
        print(f"   - {f.get('name')} (ID: {f.get('id')}) | Crop: {f.get('crop')} ({f.get('crop_stage')}) | Soil: {f.get('soil_type')} | Risk Score: {f.get('risk_score')}/100 [{f.get('risk_level').upper()}]")

    print("\n📋 Recommended Action Plan:")
    for act in result.get("recommended_actions", []):
        print(f"   - {act}")

    # Display Radio-GPT Multilingual Scripts if generated
    radio_payload = result.get("radio_gpt_payload", [])
    if radio_payload:
        print("\n📻 Member 4 (Radio-GPT) Voice Broadcast Scripts:")
        for idx, item in enumerate(radio_payload, 1):
            scripts = item.get("multilingual_scripts", {})
            print(f"\n   [Farmer {item.get('farmer_id')}]")
            print(f"   🇬🇧 English: {scripts.get('en')}")
            print(f"   🇮🇳 Hindi:   {scripts.get('hi')}")
            print(f"   🌾 Punjabi: {scripts.get('pa')}")

    print("\n===================================")


if __name__ == "__main__":
    main()