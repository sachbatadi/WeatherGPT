"""
Strategist Agent (Member 3).

Core agricultural decision-making and planning agent.
1. Consumes Threat JSON from Sentinel Agent (Member 2).
2. Evaluates crop vulnerability and farm activities via RiskEngine.
3. Dynamically updates farm plans (e.g. postponing irrigation, rescheduling spraying).
4. Generates plain-language reasoning, Radio-GPT scripts (Member 4), and Dashboard payloads (Member 5).
5. Plugs seamlessly into the LangGraph Orchestrator.
"""

from typing import Dict, Any, List, Union, Optional
from .schemas import (
    SeverityLevel,
    FarmerProfile,
    FarmActivity,
    FarmerAssessment,
    StrategistOutput
)
from .risk_engine import RiskEngine


# Default demo farmers (used when DB is not yet populated or for mock runs)
DEFAULT_DEMO_FARMERS: List[Dict[str, Any]] = [
    {
        "farmer_id": "F001",
        "name": "Gurpreet Singh",
        "phone": "+91-9876543210",
        "language": "pa",
        "location": "Jalandhar",
        "land_size_acres": 5.0,
        "crop": "Wheat",
        "crop_stage": "Flowering",
        "soil_type": "Loamy",
        "irrigation_method": "Flood",
        "current_plan": [
            {
                "activity_id": "ACT-001",
                "activity_type": "irrigation",
                "scheduled_date": "2026-09-15",
                "details": {"duration_hours": 4},
                "status": "scheduled"
            }
        ]
    },
    {
        "farmer_id": "F002",
        "name": "Harinder Kaur",
        "phone": "+91-9876543211",
        "language": "hi",
        "location": "Jalandhar",
        "land_size_acres": 3.5,
        "crop": "Wheat",
        "crop_stage": "Flowering",
        "soil_type": "Clay",
        "irrigation_method": "Sprinkler",
        "current_plan": [
            {
                "activity_id": "ACT-002",
                "activity_type": "spraying",
                "scheduled_date": "2026-09-14",
                "details": {"chemical": "Fungicide spray"},
                "status": "scheduled"
            }
        ]
    }
]


class StrategistAgent:
    """
    Decision and Strategy Orchestration Agent.
    """

    def __init__(self, default_farmers: Optional[List[Dict[str, Any]]] = None):
        self.default_farmers = default_farmers or DEFAULT_DEMO_FARMERS

    def evaluate(
        self,
        threat_data: Dict[str, Any],
        farmers: Optional[List[Union[Dict[str, Any], FarmerProfile]]] = None
    ) -> StrategistOutput:
        """
        Evaluate a threat event against affected farmers and generate an actionable strategy.
        """
        event_id = threat_data.get("event_id", "EVT-UNKNOWN")

        # Parse farmers
        farmer_profiles: List[FarmerProfile] = []
        raw_farmers = farmers if (farmers is not None and len(farmers) > 0) else self.default_farmers

        for item in raw_farmers:
            if isinstance(item, FarmerProfile):
                farmer_profiles.append(item)
            elif isinstance(item, dict):
                # Ensure current_plan items are properly formed
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
            rank = overall_severity_rank.get(assessment.risk_level.value, 1)
            if rank > highest_rank:
                highest_rank = rank

        # Determine overall risk
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
        """Evaluate single farmer, formulate explanations and subsystem payloads."""
        (
            risk_level,
            risk_score,
            risk_factors,
            actions,
            replanning_required,
            updated_plan
        ) = RiskEngine.evaluate_farmer_risk(threat, farmer)

        # Build plain language explanation
        explanation = self._build_explanation(threat, farmer, risk_level, risk_factors, actions)

        # Build Radio-GPT telephony voice script
        radio_script = self._build_radio_script(threat, farmer, actions)

        # Build Dashboard visualization payload
        dashboard_summary = {
            "farmer_id": farmer.farmer_id,
            "farmer_name": farmer.name,
            "crop": farmer.crop,
            "crop_stage": farmer.crop_stage,
            "soil_type": farmer.soil_type,
            "risk_level": risk_level.value,
            "risk_score": risk_score,
            "badge_color": self._get_badge_color(risk_level),
            "primary_action": actions[0].title if actions else "None",
            "action_count": len(actions),
            "replanning_required": replanning_required
        }

        return FarmerAssessment(
            farmer_id=farmer.farmer_id,
            farmer_name=farmer.name,
            crop=farmer.crop,
            crop_stage=farmer.crop_stage,
            risk_level=risk_level,
            risk_score=risk_score,
            risk_factors=risk_factors,
            actions=actions,
            plain_language_explanation=explanation,
            radio_gpt_script=radio_script,
            dashboard_summary=dashboard_summary,
            replanning_required=replanning_required,
            updated_plan=updated_plan
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
            reasons.append(f"{rainfall} mm rainfall predicted with {prob}% confidence ({conf})")
        if wind:
            reasons.append(f"high winds of {wind} km/h expected")

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

    def _build_radio_script(
        self,
        threat: Dict[str, Any],
        farmer: FarmerProfile,
        actions: List[Any]
    ) -> str:
        """
        Format a natural, spoken voice script for Radio-GPT (Member 4 telephony / voice alert).
        """
        rainfall = threat.get("rainfall_mm")
        time_to_event = threat.get("time_to_event_minutes", 30)
        primary_action = actions[0].title if actions else "Check your field conditions"

        script = (
            f"Attention {farmer.name} ji from {farmer.location}. "
            f"This is an urgent WeatherGPT update for your {farmer.crop} crop. "
        )

        if rainfall:
            script += f"Heavy rainfall of {rainfall} millimeters is expected in {time_to_event} minutes. "
        else:
            script += f"Adverse weather conditions are expected within {time_to_event} minutes. "

        script += f"Action required: {primary_action}. "

        if len(actions) > 1:
            script += f"Also: {actions[1].title}. "

        script += "Please stay safe and consult the WeatherGPT dashboard for updated schedules."
        return script

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
                "script": a.radio_gpt_script
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
