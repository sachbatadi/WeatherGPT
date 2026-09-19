import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from .schemas import ConversationalQuery, GroundedResponse, IntentType
from agents.orchestrator.nodes import _detect_threat, _mock_weather
from agents.strategist.agent import StrategistAgent
from tools.farmer.farmer_db import default_farmer_db
from tools.weather.weather_api import fetch_weather


class QueryRouter:
    """
    Query Router component.
    Directs queries to appropriate underlying tools, agents, or decision engines.
    Does NOT duplicate agent logic.
    """

    def __init__(self, farmer_db=None, strategist_agent=None):
        self.farmer_db = farmer_db or default_farmer_db
        self.strategist = strategist_agent or StrategistAgent(farmer_db=self.farmer_db)

    def _get_weather(self, location: str) -> Dict[str, Any]:
        """Fetch weather respecting WEATHER_MODE=mock / live."""
        mode = os.getenv("WEATHER_MODE", "mock").strip().lower()
        if mode == "live":
            try:
                return fetch_weather(location)
            except Exception:
                return _mock_weather(location)
        return _mock_weather(location)

    def route(self, query: ConversationalQuery) -> GroundedResponse:
        """Route structured conversational query to target system component."""
        location = query.location or "Jalandhar"
        intent = query.intent

        if intent in [IntentType.WEATHER, IntentType.GENERAL_WEATHER]:
            weather = self._get_weather(location)
            current = weather.get("current", {})
            hourly = weather.get("hourly", {})

            source_name = (
                "Open-Meteo Live API"
                if weather.get("source") == "open-meteo"
                else "WeatherGPT Sensor Network (Mock)"
            )

            text_summary = (
                f"Location: {location}. "
                f"Temperature: {current.get('temperature_c', 'N/A')}°C, "
                f"Humidity: {current.get('humidity_pct', 'N/A')}%, "
                f"Wind Speed: {current.get('wind_speed_kmh', 'N/A')} km/h. "
                f"Forecast 3-hr Precipitation: {sum(hourly.get('precipitation_mm', [])[:3]):.1f} mm."
            )

            return GroundedResponse(
                text=text_summary,
                data_source=source_name,
                agent_used="Weather API",
                raw_data=weather,
            )

        elif intent == IntentType.FORECAST:
            weather = self._get_weather(location)
            current = weather.get("current", {})
            hourly = weather.get("hourly", {})
            times = hourly.get("time", [])

            source_name = (
                "Open-Meteo Live API"
                if weather.get("source") == "open-meteo"
                else "WeatherGPT Sensor Network (Mock)"
            )

            # Check if dataset contains future timestamped data for tomorrow
            has_tomorrow_data = False
            tomorrow_indices = []

            if times:
                now = datetime.now(timezone.utc)
                tomorrow_date = (now + timedelta(days=1)).strftime("%Y-%m-%d")

                for idx, t in enumerate(times):
                    if isinstance(t, str) and (tomorrow_date in t or idx >= 12):
                        tomorrow_indices.append(idx)

                if tomorrow_indices:
                    has_tomorrow_data = True

            raw_copy = dict(weather)
            raw_copy["has_tomorrow_forecast"] = has_tomorrow_data

            if has_tomorrow_data:
                temps = [
                    hourly.get("temperature_c", [])[i]
                    for i in tomorrow_indices
                    if i < len(hourly.get("temperature_c", []))
                ]
                precip = [
                    hourly.get("precipitation_mm", [])[i]
                    for i in tomorrow_indices
                    if i < len(hourly.get("precipitation_mm", []))
                ]
                probs = [
                    hourly.get("precipitation_probability_pct", [])[i]
                    for i in tomorrow_indices
                    if i < len(hourly.get("precipitation_probability_pct", []))
                ]

                max_temp = max(temps) if temps else current.get("temperature_c", "N/A")
                min_temp = min(temps) if temps else current.get("temperature_c", "N/A")
                total_precip = sum(precip) if precip else 0.0
                max_prob = max(probs) if probs else 0.0

                text_summary = (
                    f"Tomorrow's forecast for {location}: Expected temperature between {min_temp}°C and {max_temp}°C. "
                    f"Precipitation probability: {max_prob}%, estimated rainfall: {total_precip:.1f} mm."
                )
            else:
                text_summary = (
                    f"The current SIH mock weather scenario for {location} contains near-term threat monitoring data, "
                    f"but does not include a timestamped forecast specifically for tomorrow. "
                    f"I cannot reliably determine tomorrow's forecast from this dataset."
                )

            return GroundedResponse(
                text=text_summary,
                data_source=source_name,
                agent_used="Weather API",
                raw_data=raw_copy,
            )

        elif intent == IntentType.WARNING:
            weather = self._get_weather(location)
            threat = _detect_threat(weather, location)

            event_type = threat.get("event_type", "none")
            severity = threat.get("severity", "low")

            if event_type != "none":
                summary = (
                    f"SEVERE WEATHER ALERT for {location}: {event_type.replace('_', ' ').upper()} detected! "
                    f"Severity: {severity.upper()}. Expected rainfall: {threat.get('rainfall_mm', 0)} mm, "
                    f"Wind speed: {threat.get('wind_speed_kmh', 0)} km/h in approximately {threat.get('time_to_event_minutes', 60)} minutes."
                )
            else:
                summary = f"No severe weather warnings currently active for {location}."

            return GroundedResponse(
                text=summary,
                data_source="Sentinel Threat Detector",
                agent_used="Sentinel",
                raw_data=threat,
                actions=[f"Monitor {location} weather updates"],
            )

        elif intent == IntentType.AGRICULTURE:
            weather = self._get_weather(location)
            threat = _detect_threat(weather, location)

            eval_result = self.strategist.evaluate(threat_data=threat)
            orch_patch = eval_result.to_orchestrator_state()
            actions = orch_patch.get("recommended_actions", [])

            summary = (
                f"Agricultural assessment for {location} (Overall Risk: {eval_result.overall_risk_level.value.upper()}):\n"
                f"Recommended actions: {', '.join(actions) if actions else 'Normal farming operations.'}"
            )

            if eval_result.assessments:
                first_ass = eval_result.assessments[0]
                summary += f"\nAdvice for {first_ass.crop} ({first_ass.crop_stage}): {first_ass.plain_language_explanation}"

            return GroundedResponse(
                text=summary,
                data_source="Strategist Agricultural Decision Engine",
                agent_used="Strategist",
                raw_data=eval_result.model_dump(),
                actions=actions,
                reasoning=eval_result.assessments[0].plain_language_explanation if eval_result.assessments else None,
            )

        elif intent == IntentType.AGRICULTURE_EXPLANATION:
            farmer_id = query.farmer_id or "F001"
            farmer_obj = self.farmer_db.get_farmer_by_id(farmer_id)

            if not farmer_obj:
                farmers = self.farmer_db.get_farmers_by_location(location)
                if farmers:
                    farmer_obj = farmers[0]
                    farmer_id = farmer_obj.get("farmer_id", "F001")

            if farmer_obj:
                res = self.strategist.answer_farmer_query(farmer_id, query.query)
                return GroundedResponse(
                    text=f"Explanation for Farmer {farmer_obj.get('name', farmer_id)}: {res.answer}\nNext Step: {res.recommended_next_step}",
                    data_source="Strategist Execution Engine",
                    agent_used="Strategist/Executor",
                    raw_data=res.model_dump(),
                    actions=[res.recommended_next_step],
                    reasoning=res.answer,
                )
            else:
                return GroundedResponse(
                    text="Requested execution record or farmer profile is currently unavailable in the database.",
                    data_source="FarmerDB",
                    agent_used="Executor",
                )

        elif intent == IntentType.CLIMATE:
            return GroundedResponse(
                text="Historical climate trend data is not currently connected through the active data source.",
                data_source="Climate System Notice",
                agent_used="System",
            )

        elif intent == IntentType.EMERGENCY:
            weather = self._get_weather(location)
            threat = _detect_threat(weather, location)

            text = (
                f"🚨 EMERGENCY ALERT for {location}: WeatherGPT Emergency Mode active. "
                f"Severe weather threat: {threat.get('event_type', 'severe weather').upper()} ({threat.get('severity', 'high').upper()}). "
                f"Immediate Advice: Suspend all open-field agricultural activities, secure machinery, and stay in safe shelter."
            )
            return GroundedResponse(
                text=text,
                data_source="Emergency Warning Protocol",
                agent_used="Sentinel Emergency",
                raw_data=threat,
                actions=["Suspend field operations", "Seek immediate shelter", "Follow local disaster authority notices"],
            )

        else: # UNKNOWN
            return GroundedResponse(
                text="I am WeatherGPT. Could you please specify your location or ask a specific weather/farming question?",
                data_source="WeatherGPT Assistant",
                agent_used="Conversational Interface",
            )
