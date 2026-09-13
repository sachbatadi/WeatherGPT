"""
Strategist Agent (Member 3).

Core agricultural decision-making, re-planning, and conversational engine.
1. Consumes Threat JSON from Sentinel Agent (Member 2).
2. Connects to Farmer Database (tools/farmer/farmer_db.py).
3. Evaluates crop vulnerability and farm activities via RiskEngine.
4. Dynamically re-plans farm schedules (irrigation, spraying, fertilization, harvest).
5. Generates multilingual voice scripts for Member 4 (Radio-GPT) in English, Hindi, and Punjabi.
6. Generates dashboard cards for Member 5 (Dashboard).
7. Answers farmer questions conversational AI ("Why did you change my plan?").
8. Plugs directly into LangGraph Orchestrator as a drop-in node.
"""

from typing import Dict, Any, List, Union, Optional
from .schemas import (
    SeverityLevel,
    FarmerProfile,
    FarmActivity,
    FarmerAssessment,
    StrategistOutput,
    LanguageVoiceScripts,
    FarmerQueryResponse
)
from .risk_engine import RiskEngine
from tools.farmer.farmer_db import default_farmer_db


class StrategistAgent:
    """
    Agricultural Strategy & Decision Orchestration Agent.
    """

    def __init__(self, farmer_db=None):
        self.farmer_db = farmer_db or default_farmer_db

    def evaluate(
        self,
        threat_data: Dict[str, Any],
        farmers: Optional[List[Union[Dict[str, Any], FarmerProfile]]] = None
    ) -> StrategistOutput:
        """
        Evaluate a threat event against affected farmers and generate an actionable strategy.
        If no farmers are provided, queries the farmer database by location.
        """
        event_id = threat_data.get("event_id", "EVT-UNKNOWN")
        location = threat_data.get("location", "Jalandhar")

        # Parse farmers or query from DB
        farmer_profiles: List[FarmerProfile] = []

        if farmers is not None and len(farmers) > 0:
            raw_farmers = farmers
        else:
            # Query from Farmer DB by location, fallback to all farmers if no location match
            matched = self.farmer_db.get_farmers_by_location(location)
            raw_farmers = matched if matched else self.farmer_db.get_all_farmers()

        for item in raw_farmers:
            if isinstance(item, FarmerProfile):
                farmer_profiles.append(item)
            elif isinstance(item, dict):
                plan_raw = item.get("current_plan", [])
                plan_models = [
                    p if isinstance(p, FarmActivity) else FarmActivity(**p)
                    for p in plan_raw
                ]
                item_copy = dict(item)
                item_copy["current_plan"] = plan_models
                farmer_profiles.append(FarmerProfile(**item_copy))

        assessments: List[FarmerAssessment] = []
        overall_severity_rank = {"low": 1, "medium": 2, "high": 3, "critical": 4}
        highest_rank = 1

        for farmer in farmer_profiles:
            assessment = self._assess_farmer(threat_data, farmer)
            assessments.append(assessment)

            # Persist updated plan in database if changed
            if assessment.replanning_required:
                self.farmer_db.update_farmer_plan(
                    farmer.farmer_id,
                    [p.model_dump() for p in assessment.updated_plan]
                )

            rank = overall_severity_rank.get(assessment.risk_level.value, 1)
            if rank > highest_rank:
                highest_rank = rank

        rank_to_severity = {
            1: SeverityLevel.LOW,
            2: SeverityLevel.MEDIUM,
            3: SeverityLevel.HIGH,
            4: SeverityLevel.CRITICAL
        }
        overall_risk = rank_to_severity[highest_rank]
        alert_required = overall_risk in (SeverityLevel.HIGH, SeverityLevel.CRITICAL)

        return StrategistOutput(
            threat_event_id=event_id,
            overall_risk_level=overall_risk,
            affected_farmers_count=len(assessments),
            assessments=assessments,
            alert_required=alert_required
        )

    def _assess_farmer(self, threat: Dict[str, Any], farmer: FarmerProfile) -> FarmerAssessment:
        """Evaluate single farmer, formulate multilingual explanations and subsystem payloads."""
        (
            risk_level,
            risk_score,
            breakdown,
            risk_factors,
            actions,
            replanning_required,
            updated_plan,
            obs_trigger
        ) = RiskEngine.evaluate_farmer_risk(threat, farmer)

        explanation = self._build_explanation(threat, farmer, risk_level, risk_factors, actions)
        multilingual_scripts = self._build_multilingual_scripts(threat, farmer, actions)

        # Pick default script based on preferred language
        lang = (farmer.language or "en").lower()
        if lang == "hi":
            default_script = multilingual_scripts.hi
        elif lang == "pa":
            default_script = multilingual_scripts.pa
        else:
            default_script = multilingual_scripts.en

        dashboard_summary = {
            "farmer_id": farmer.farmer_id,
            "farmer_name": farmer.name,
            "crop": farmer.crop,
            "crop_stage": farmer.crop_stage,
            "soil_type": farmer.soil_type,
            "risk_level": risk_level.value,
            "risk_score": risk_score,
            "risk_breakdown": breakdown.model_dump(),
            "badge_color": self._get_badge_color(risk_level),
            "primary_action": actions[0].title if actions else "None",
            "action_count": len(actions),
            "replanning_required": replanning_required,
            "next_review_hours": obs_trigger.reassess_after_hours if obs_trigger else 12
        }

        return FarmerAssessment(
            farmer_id=farmer.farmer_id,
            farmer_name=farmer.name,
            crop=farmer.crop,
            crop_stage=farmer.crop_stage,
            soil_type=farmer.soil_type,
            risk_level=risk_level,
            risk_score=risk_score,
            risk_breakdown=breakdown,
            risk_factors=risk_factors,
            actions=actions,
            plain_language_explanation=explanation,
            radio_gpt_script=default_script,
            multilingual_scripts=multilingual_scripts,
            dashboard_summary=dashboard_summary,
            replanning_required=replanning_required,
            updated_plan=updated_plan,
            next_observation=obs_trigger
        )

    def _build_explanation(
        self,
        threat: Dict[str, Any],
        farmer: FarmerProfile,
        risk_level: SeverityLevel,
        factors: List[str],
        actions: List[Any]
    ) -> str:
        """
        Generate clear, evidence-based reasoning ("Why did you change my plan?").
        """
        event_type = threat.get("event_type", "weather disturbance").replace("_", " ").title()
        rainfall = threat.get("rainfall_mm")
        wind = threat.get("wind_speed_kmh")
        prob = int(float(threat.get("probability", 0.8)) * 100)
        conf = threat.get("confidence", "high").upper()

        reasons: List[str] = []
        if rainfall:
            reasons.append(f"{rainfall:.1f} mm rainfall predicted with {prob}% probability ({conf} confidence)")
        if wind:
            reasons.append(f"high winds of {wind:.1f} km/h expected")

        metric_str = ", and ".join(reasons) if reasons else f"{prob}% forecast probability"
        action_titles = [a.title for a in actions]
        action_str = "; ".join(action_titles)

        explanation = (
            f"WeatherGPT detected a {risk_level.value.upper()} risk from incoming {event_type} in {farmer.location} "
            f"({metric_str}). For your {farmer.crop} ({farmer.crop_stage} stage) on {farmer.soil_type} soil: "
            f"{' '.join(factors)} "
            f"Recommended Strategy: {action_str}."
        )
        return explanation

    def _build_multilingual_scripts(
        self,
        threat: Dict[str, Any],
        farmer: FarmerProfile,
        actions: List[Any]
    ) -> LanguageVoiceScripts:
        """
        Format localized, polite, punchy voice scripts for Radio-GPT (Member 4 telephony / voice alert).
        Supports English (en), Hindi (hi), and Punjabi (pa).
        """
        rainfall = threat.get("rainfall_mm")
        wind = threat.get("wind_speed_kmh")
        time_to_event = threat.get("time_to_event_minutes", 30)
        primary_action = actions[0].title if actions else "Check your field conditions"
        secondary_action = actions[1].title if len(actions) > 1 else None

        # 1. English Script
        en_script = (
            f"Attention {farmer.name} ji from {farmer.location}. "
            f"This is an important WeatherGPT advisory for your {farmer.crop} crop. "
        )
        if rainfall and rainfall >= 10:
            en_script += f"Heavy rainfall of {rainfall:.0f} mm is expected within {time_to_event} minutes. "
        elif wind and wind >= 20:
            en_script += f"Strong winds of {wind:.0f} km/h are expected within {time_to_event} minutes. "
        else:
            en_script += f"Weather changes are forecasted within {time_to_event} minutes. "

        en_script += f"Primary action: {primary_action}. "
        if secondary_action:
            en_script += f"Also: {secondary_action}. "
        en_script += "Please stay safe and check the WeatherGPT dashboard for updated schedules."

        # 2. Hindi Script (हिन्दी)
        hi_script = (
            f"नमस्ते {farmer.name} जी, {farmer.location} से। "
            f"यह आपकी {farmer.crop} की फसल के लिए वेदरजीपीटी (WeatherGPT) का महत्वपूर्ण अलर्ट है। "
        )
        if rainfall and rainfall >= 10:
            hi_script += f"अगले {time_to_event} मिनटों में लगभग {rainfall:.0f} मिलीमीटर भारी बारिश की संभावना है। "
            hi_script += "कृपया अपनी निर्धारित सिंचाई रोक दें और खेतों की नालियां खोल दें। "
        elif wind and wind >= 20:
            hi_script += f"अगले {time_to_event} मिनटों में {wind:.0f} किलोमीटर प्रति घंटे की तेज हवा चलने की संभावना है। "
            hi_script += "कृपया कीटनाशक का छिड़काव तुरंत टालें। "
        else:
            hi_script += f"मौसम में बदलाव की संभावना है। कृपया अपने खेत की स्थिति जांचें। "

        hi_script += "सुरक्षित रहें और अपडेटेड प्लान के लिए वेदरजीपीटी डैशबोर्ड देखें।"

        # 3. Punjabi Script (ਪੰਜਾਬੀ)
        pa_script = (
            f"ਸਤਿ ਸ੍ਰੀ ਅਕਾਲ {farmer.name} ਜੀ, {farmer.location} ਤੋਂ। "
            f"ਇਹ ਤੁਹਾਡੀ {farmer.crop} ਦੀ ਫ਼ਸਲ ਲਈ ਵੈਦਰ-ਜੀਪੀਟੀ (WeatherGPT) ਵੱਲੋਂ ਜ਼ਰੂਰੀ ਸੂਚਨਾ ਹੈ। "
        )
        if rainfall and rainfall >= 10:
            pa_script += f"ਅਗਲੇ {time_to_event} ਮਿੰਟਾਂ ਵਿੱਚ ਲਗਭਗ {rainfall:.0f} ਮਿਲੀਮੀਟਰ ਭਾਰੀ ਮੀਂਹ ਪੈਣ ਦਾ ਅਨੁਮਾਨ ਹੈ। "
            pa_script += "ਕਿਰਪਾ ਕਰਕੇ ਪਾਣੀ ਲਾਉਣਾ ਮੁਲਤਵੀ ਕਰੋ ਅਤੇ ਖੇਤ ਦੇ ਨਿਕਾਸ ਦਾ ਪ੍ਰਬੰਧ ਕਰੋ। "
        elif wind and wind >= 20:
            pa_script += f"ਅਗਲੇ {time_to_event} ਮਿੰਟਾਂ ਵਿੱਚ {wind:.0f} ਕਿਲੋਮੀਟਰ ਪ੍ਰਤੀ ਘੰਟੇ ਦੀ ਤੇਜ਼ ਹਵਾ ਚੱਲਣ ਦਾ ਖ਼ਤਰਾ ਹੈ। "
            pa_script += "ਕਿਰਪਾ ਕਰਕੇ ਸਪਰੇਅ ਦਾ ਕੰਮ ਤੁਰੰਤ ਰੋਕ ਦਿਓ। "
        else:
            pa_script += "ਮੌਸਮ ਵਿੱਚ ਬਦਲਾਅ ਦੀ ਸੰਭਾਵਨਾ ਹੈ। ਖੇਤ ਦੀ ਦੇਖ-ਰੇਖ ਕਰੋ ਜੀ।"

        pa_script += "ਸੁਰੱਖਿਅਤ ਰਹੋ ਅਤੇ ਅੱਪਡੇਟ ਕੀਤੇ ਪਲਾਨ ਲਈ ਵੈਦਰ-ਜੀਪੀਟੀ ਡੈਸ਼ਬੋਰਡ ਦੇਖੋ।"

        return LanguageVoiceScripts(en=en_script, hi=hi_script, pa=pa_script)

    def answer_farmer_query(
        self,
        farmer_id: str,
        query: str,
        language: str = "en"
    ) -> FarmerQueryResponse:
        """
        Conversational reasoning engine (Module 10).
        Answers farmer queries like:
        - "Why did you postpone my irrigation?"
        - "When can I irrigate next?"
        - "Can I spray today?"
        """
        farmer_data = self.farmer_db.get_farmer_by_id(farmer_id)
        if not farmer_data:
            return FarmerQueryResponse(
                farmer_id=farmer_id,
                query=query,
                answer="Farmer profile not found in database.",
                recommended_next_step="Register your farm profile with WeatherGPT."
            )

        farmer = FarmerProfile(**farmer_data)
        query_lower = query.lower()

        # Check topic
        if any(w in query_lower for w in ["irrigation", "water", "irrigate", "sinchai", "paani"]):
            answer = (
                f"Namaste {farmer.name} ji. We adjusted your irrigation schedule because substantial rainfall "
                f"was verified across multiple forecast sources. Your {farmer.soil_type} soil will reach full saturation "
                f"from the incoming rain. Irrigating right before rainfall would cause waterlogging, waste pumping electricity, "
                f"and harm your {farmer.crop} root system."
            )
            next_step = f"Wait for the rain to cease. Re-check your field moisture in {RiskEngine.calculate_drying_days(40, farmer.soil_type)} days."
            evidence = {"crop": farmer.crop, "soil_type": farmer.soil_type, "action": "postpone_irrigation"}

        elif any(w in query_lower for w in ["spray", "pesticide", "fungicide", "keetnashak", "spray"]):
            answer = (
                f"We postponed spraying activities because high wind speeds (>15 km/h) or rainfall cause spray droplets "
                f"to drift into neighboring fields and wash off the crop canopy before absorption."
            )
            next_step = "Wait until wind drops below 15 km/h and foliage is completely dry before applying chemicals."
            evidence = {"wind_threshold_kmh": 15.0, "action": "reschedule_spray"}

        else:
            answer = (
                f"WeatherGPT continuously monitors multi-model weather forecasts for {farmer.location} and dynamically "
                f"optimizes farm tasks to protect your {farmer.crop} ({farmer.crop_stage} stage) and maximize yield."
            )
            next_step = "Consult the WeatherGPT dashboard for real-time task updates."
            evidence = {"crop": farmer.crop, "location": farmer.location}

        return FarmerQueryResponse(
            farmer_id=farmer_id,
            query=query,
            answer=answer,
            evidence=evidence,
            recommended_next_step=next_step
        )

    @staticmethod
    def _get_badge_color(severity: SeverityLevel) -> str:
        mapping = {
            SeverityLevel.LOW: "green",
            SeverityLevel.MEDIUM: "yellow",
            SeverityLevel.HIGH: "orange",
            SeverityLevel.CRITICAL: "red"
        }
        return mapping.get(severity, "blue")

    def process_orchestrator_state(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Bridge method for LangGraph Orchestrator node.
        Directly mutates and enriches the shared WeatherState.
        """
        threat = state.get("threat", {})
        farmers = state.get("affected_farmers", None)

        output = self.evaluate(threat_data=threat, farmers=farmers)

        # Merge strategist results into state
        state_patch = output.to_orchestrator_state()
        for k, v in state_patch.items():
            state[k] = v

        # Add detailed payloads for downstream nodes
        state["strategist_output"] = output.model_dump()
        state["radio_gpt_payload"] = [
            {
                "farmer_id": a.farmer_id,
                "phone": getattr(a, "phone", None),
                "script": a.radio_gpt_script,
                "multilingual_scripts": a.multilingual_scripts.model_dump()
            }
            for a in output.assessments
        ]
        state["dashboard_payload"] = [a.dashboard_summary for a in output.assessments]

        return state


def run_strategist_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Drop-in node function for LangGraph Orchestrator:
    `graph.add_node("strategist", run_strategist_node)`
    """
    try:
        print("\n[STRATEGIST] Strategist Agent running (Agricultural Decision Engine)...")
    except Exception:
        pass

    strategist = StrategistAgent()
    updated_state = strategist.process_orchestrator_state(state)

    try:
        print(f"[*] Evaluated farmers: {len(updated_state.get('affected_farmers', []))}")
        print(f"[*] Assessed Risk Level: {updated_state.get('risk_level', '').upper()}")
        print("[*] Generated Action Plan:")
        for act in updated_state.get("recommended_actions", []):
            print(f"   - {act}")
        print(f"[*] Replanning required: {updated_state.get('replanning_required', False)}")
        print(f"[*] Proactive alert required: {updated_state.get('alert_required', False)}")
    except Exception:
        pass

    return updated_state


def _safe_print(text: str) -> None:
    """Safe print helper that prevents Windows cp1252 charmap encoding crashes."""
    try:
        print(text)
    except (UnicodeEncodeError, UnicodeError):
        import sys
        enc = sys.stdout.encoding or "utf-8"
        print(text.encode(enc, errors="replace").decode(enc))


if __name__ == "__main__":
    import sys
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    # Demonstration CLI execution
    _safe_print("==================================================")
    _safe_print("   WeatherGPT - Strategist Agent Interactive Demo")
    _safe_print("==================================================")

    agent = StrategistAgent()

    # Scenario: Heavy rain threat in Jalandhar
    threat_event = {
        "event_id": "EVT-SIH-001",
        "event_type": "heavy_rain",
        "severity": "high",
        "probability": 0.85,
        "confidence": "high",
        "location": "Jalandhar",
        "time_to_event_minutes": 30,
        "rainfall_mm": 60.0,
        "wind_speed_kmh": 22.0
    }

    result = agent.evaluate(threat_data=threat_event)
    _safe_print(f"\nLocation: {threat_event['location']}")
    _safe_print(f"Threat: {threat_event['event_type']} ({threat_event['rainfall_mm']} mm)")
    _safe_print(f"Overall Risk: {result.overall_risk_level.value.upper()}")
    _safe_print(f"Alert Required: {result.alert_required}")
    _safe_print(f"Farmers Evaluated: {result.affected_farmers_count}")

    for idx, asm in enumerate(result.assessments, 1):
        _safe_print(f"\n--- Farmer {idx}: {asm.farmer_name} ({asm.crop} - {asm.crop_stage}) ---")
        _safe_print(f"Risk Score: {asm.risk_score} / 100 ({asm.risk_level.value.upper()})")
        _safe_print("Actions:")
        for act in asm.actions:
            _safe_print(f"  * [{act.urgency.value.upper()}] {act.title}: {act.description[:75]}...")
        _safe_print(f"Replanning required: {asm.replanning_required}")
        _safe_print("\nRadio-GPT Voice Script (English):")
        _safe_print(f"  \"{asm.multilingual_scripts.en}\"")
        _safe_print("\nRadio-GPT Voice Script (Hindi):")
        _safe_print(f"  \"{asm.multilingual_scripts.hi}\"")
        _safe_print("\nRadio-GPT Voice Script (Punjabi):")
        _safe_print(f"  \"{asm.multilingual_scripts.pa}\"")

    # Conversational Q&A test
    _safe_print("\n==================================================")
    _safe_print("   Farmer Conversational Q&A Simulation")
    _safe_print("==================================================")
    query = "Why did you postpone my irrigation on September 15?"
    _safe_print(f"Farmer asked: \"{query}\"")
    response = agent.answer_farmer_query("F001", query)
    _safe_print(f"Strategist Agent: \"{response.answer}\"")
    _safe_print(f"Next step: \"{response.recommended_next_step}\"")
    _safe_print("==================================================")
