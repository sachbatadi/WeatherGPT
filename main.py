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
    print("⚠️ Threat:", result.get("threat"))
    print("🚨 Risk Level:", result.get("risk_level"))
    print("👨‍🌾 Affected Farmers:", result.get("affected_farmers"))
    print("📋 Recommended Actions:", result.get("recommended_actions"))
    print("📞 Alert Required:", result.get("alert_required"))

    print("\n===================================")


if __name__ == "__main__":
    main()