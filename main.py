import os
import sys
import time

# Ensure UTF-8 stdout encoding for Windows console compatibility with emojis
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

from agents.orchestrator.graph import build_graph


def print_result(result):
    # ============================================================
    # FINAL RESULT
    # ============================================================

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

    # ============================================================
    # FARMERS
    # ============================================================

    print("\n👨‍🌾 Affected Farmers Assessed:")

    for f in result.get("affected_farmers", []):
        print(
            f"   - {f.get('name')} "
            f"(ID: {f.get('id')}) | "
            f"Crop: {f.get('crop')} "
            f"({f.get('crop_stage')}) | "
            f"Soil: {f.get('soil_type')} | "
            f"Risk Score: {f.get('risk_score')}/100 "
            f"[{str(f.get('risk_level', '')).upper()}]"
        )

    # ============================================================
    # STRATEGIST ACTION PLAN
    # ============================================================

    print("\n📋 Recommended Action Plan:")

    for act in result.get("recommended_actions", []):
        print(f"   - {act}")

    # ============================================================
    # EXECUTOR RESULT
    # ============================================================

    executor = result.get("executor_output", {})

    if hasattr(executor, "model_dump"):
        executor = executor.model_dump()

    print("\n===================================")
    print("        ⚙️ EXECUTOR RESULT")
    print("===================================")

    print(
        "\n🔧 Execution Status:",
        str(executor.get("execution_status", "unknown")).upper()
    )

    print(
        "📱 Alerts Dispatched:",
        executor.get("total_alerts_dispatched", 0)
    )

    print(
        "📋 Plans Updated:",
        executor.get("total_plans_updated", 0)
    )

    print(
        "📅 Calendar Operations:",
        executor.get("total_calendar_operations", 0)
    )

    # ============================================================
    # FARM PLAN UPDATES
    # ============================================================

    plan_updates = executor.get("applied_plan_updates", [])

    print("\n📝 Farmer Plan Updates:")

    if plan_updates:
        for update in plan_updates:
            if hasattr(update, "model_dump"):
                update = update.model_dump()

            print(
                f"   - Farmer {update.get('farmer_id')} | "
                f"Activity: {update.get('activity_id')} | "
                f"{update.get('old_status')} → "
                f"{update.get('new_status')}"
            )

            if update.get("rescheduled_to"):
                print(
                    f"     📆 Rescheduled to: "
                    f"{update.get('rescheduled_to')}"
                )
    else:
        print("   - No farmer plans updated.")

    # ============================================================
    # CALENDAR OPERATIONS
    # ============================================================

    calendar_operations = executor.get("calendar_operations", [])

    print("\n📅 Calendar Operations:")

    if calendar_operations:
        for operation in calendar_operations:
            if hasattr(operation, "model_dump"):
                operation = operation.model_dump()

            print(
                f"   - {operation.get('operation')} | "
                f"Farmer: {operation.get('farmer_id')} | "
                f"Activity: {operation.get('activity_id')} | "
                f"Status: {str(operation.get('status', '')).upper()}"
            )

            if operation.get("calendar_event_id"):
                print(
                    f"     🆔 Calendar Event: "
                    f"{operation.get('calendar_event_id')}"
                )

            print(
                f"     💬 {operation.get('message', '')}"
            )
    else:
        print("   - No calendar operations performed.")

    # ============================================================
    # SMS / ALERT DISPATCH
    # ============================================================

    dispatched_alerts = executor.get("dispatched_alerts", [])

    print("\n📱 Alert Dispatch:")

    if dispatched_alerts:
        for alert in dispatched_alerts:
            if hasattr(alert, "model_dump"):
                alert = alert.model_dump()

            print(
                f"   - {str(alert.get('channel', '')).upper()} | "
                f"Farmer: {alert.get('farmer_name')} | "
                f"Status: {str(alert.get('status', '')).upper()}"
            )

            print(
                f"     💬 {alert.get('message', '')}"
            )
    else:
        print("   - No alerts dispatched.")

    # ============================================================
    # DASHBOARD EVENTS
    # ============================================================

    dashboard_events = executor.get("dashboard_events", [])

    print("\n📊 Dashboard Events:")

    if dashboard_events:
        for event in dashboard_events:
            if hasattr(event, "model_dump"):
                event = event.model_dump()

            print(
                f"   - Farmer: {event.get('farmer_name')} | "
                f"Risk: {str(event.get('risk_level', '')).upper()} | "
                f"Execution: {event.get('execution_status')} | "
                f"Calendar: {event.get('calendar_status')}"
            )
    else:
        print("   - No dashboard events created.")

    # ============================================================
    # EXECUTION LOG
    # ============================================================

    execution_log = executor.get("execution_log", [])

    print("\n🧾 Execution Log:")

    if execution_log:
        for log in execution_log:
            print(f"   - {log}")
    else:
        print("   - No execution log entries.")

    # ============================================================

    print("\n===================================")
    print("       WEATHERGPT CYCLE COMPLETE")
    print("===================================")


def get_threat_signature(result):
    """
    Creates a stable identifier for the current threat.

    The Sentinel event_id changes on every monitoring cycle,
    so we do not use event_id for duplicate protection.
    """

    threat = result.get("threat", {})

    event_type = threat.get("event_type", "none")
    location = result.get("location", "")
    severity = threat.get("severity", "")

    return (
        str(location).lower().strip(),
        str(event_type).lower().strip(),
        str(severity).lower().strip(),
    )


def run_monitoring_cycle(graph, location, last_threat_signature):
    """
    Executes one complete WeatherGPT monitoring cycle.

    Returns:
        Updated threat signature.
    """

    print("\n\n===================================")
    print("      🌦️ WEATHERGPT MONITOR")
    print("===================================")

    print("\n📍 Monitoring location:", location)

    result = graph.invoke(
        {
            "location": location
        }
    )

    threat = result.get("threat", {})
    threat_detected = result.get("threat_detected", False)

    current_signature = get_threat_signature(result)

    # ============================================================
    # NO THREAT
    # ============================================================

    if not threat_detected:
        print("\n✅ No severe weather threat detected.")
        print("📡 Sentinel will continue monitoring.")

        # Reset the previous threat so that if the same type of
        # threat occurs again later, an alert can be sent again.
        return None

    # ============================================================
    # NEW THREAT
    # ============================================================

    if current_signature != last_threat_signature:
        print("\n🚨 NEW WEATHER THREAT DETECTED")
        print("📨 Alert execution is allowed for this threat.")

        print_result(result)

        return current_signature

    # ============================================================
    # EXISTING THREAT
    # ============================================================

    print("\n⚠️ Existing threat is still active.")
    print("🛑 Duplicate alert suppressed.")
    print("📡 Sentinel will continue monitoring.")

    print(
        f"   Threat: "
        f"{threat.get('event_type', '').replace('_', ' ').title()}"
    )

    print(
        f"   Severity: "
        f"{str(threat.get('severity', '')).upper()}"
    )

    print(
        f"   Location: {result.get('location')}"
    )

    return last_threat_signature


def main():
    print("\n===================================")
    print("      🌦️ WEATHERGPT AGENT SYSTEM")
    print("===================================")

    # ============================================================
    # CONFIGURATION
    # ============================================================

    location = os.getenv("WEATHER_LOCATION", "Jalandhar")

    # Default: check every 60 seconds.
    # Can be changed without modifying code:
    #
    # export MONITOR_INTERVAL_SECONDS="30"
    #
    monitor_interval = int(
        os.getenv("MONITOR_INTERVAL_SECONDS", "60")
    )

    weather_mode = os.getenv(
        "WEATHER_MODE",
        "mock"
    ).lower()

    print("\n📍 Starting location:", location)
    print("🌐 Weather mode:", weather_mode.upper())
    print("⏱️ Monitoring interval:", monitor_interval, "seconds")

    print("\n🔧 Building WeatherGPT agent graph...")

    graph = build_graph()

    print("✅ Agent graph ready.")

    # Stores the last active threat.
    #
    # This prevents the same active threat from generating
    # duplicate SMS alerts on every monitoring cycle.
    last_threat_signature = None

    print("\n===================================")
    print("      📡 CONTINUOUS MONITORING")
    print("===================================")

    print("\n👁️ Sentinel will continuously monitor live weather.")
    print("📱 Real SMS alerts will be dispatched when a NEW")
    print("   qualifying threat is detected.")
    print("\n🛑 Press Ctrl+C to stop monitoring.")

    try:
        while True:

            last_threat_signature = run_monitoring_cycle(
                graph=graph,
                location=location,
                last_threat_signature=last_threat_signature,
            )

            print(
                f"\n⏳ Next weather check in "
                f"{monitor_interval} seconds..."
            )

            time.sleep(monitor_interval)

    except KeyboardInterrupt:
        print("\n\n===================================")
        print("       🛑 MONITORING STOPPED")
        print("===================================")
        print("\nWeatherGPT monitoring stopped safely.")
        print("No further SMS alerts will be dispatched.")


if __name__ == "__main__":
    main()