"""
Strategist Agent Schemas (Member 3).

Defines the core data models and contracts for:
1. Input: Threat JSON + Farm Profiles & Plans
2. Processing: Agronomic risk evaluations
3. Output: Risk + Action payloads for Orchestrator, Radio-GPT, Dashboard & Database.
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class SeverityLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ConfidenceLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class CropType(str, Enum):
    WHEAT = "wheat"
    RICE = "rice"
    COTTON = "cotton"
    TOMATO = "tomato"
    MUSTARD = "mustard"
    MAIZE = "maize"
    SUGARCANE = "sugarcane"
    POTATO = "potato"
    OTHER = "other"


class CropStage(str, Enum):
    SOWING = "sowing"
    VEGETATIVE = "vegetative"
    FLOWERING = "flowering"
    GRAIN_FILLING = "grain_filling"
    MATURITY = "maturity"
    HARVESTING = "harvesting"


class SoilType(str, Enum):
    CLAY = "clay"
    LOAMY = "loamy"
    SANDY = "sandy"
    SILTY = "silty"
    BLACK_SOIL = "black_soil"


class IrrigationMethod(str, Enum):
    FLOOD = "flood"
    DRIP = "drip"
    SPRINKLER = "sprinkler"
    RAINFED = "rainfed"


class ActionType(str, Enum):
    POSTPONE_IRRIGATION = "postpone_irrigation"
    RESCHEDULE_SPRAY = "reschedule_spray"
    EXPEDITE_HARVEST = "expedite_harvest"
    HALT_HARVEST = "halt_harvest"
    DRAINAGE_PREPARATION = "drainage_preparation"
    PROTECTIVE_COVERING = "protective_covering"
    HEAT_STRESS_MITIGATION = "heat_stress_mitigation"
    FROST_PROTECTION = "frost_protection"
    NO_ACTION = "no_action"


class UrgencyLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    IMMEDIATE = "immediate"


# ---------------------------------------------------------------------------
# Farm Profile & Scheduled Activities
# ---------------------------------------------------------------------------

class FarmActivity(BaseModel):
    """An individual farm task scheduled in the farmer's plan."""
    activity_id: str = Field(..., description="Unique activity ID (e.g. ACT-001)")
    activity_type: str = Field(
        ...,
        description="Type of activity: irrigation, spraying, harvesting, fertilization, sowing"
    )
    scheduled_date: str = Field(
        ...,
        description="Scheduled date string (e.g. 2026-09-15 or relative 'tomorrow')"
    )
    details: Dict[str, Any] = Field(
        default_factory=dict,
        description="Details such as water volume, chemical type, target area"
    )
    status: str = Field(
        default="scheduled",
        description="Status: scheduled, postponed, completed, cancelled, in_progress"
    )


class FarmerProfile(BaseModel):
    """
    Farmer Profile & active context maintained by Database/Orchestrator.
    """
    farmer_id: str = Field(..., description="Unique identifier for the farmer (e.g. F001)")
    name: str = Field(..., description="Farmer full name")
    phone: Optional[str] = Field(None, description="Contact phone number for SMS/voice alert")
    language: str = Field(default="en", description="Preferred language code: en, hi, pa, etc.")
    location: str = Field(..., description="Village / District name (e.g. Jalandhar)")
    land_size_acres: Optional[float] = Field(None, description="Land area in acres")

    # Agronomic context
    crop: str = Field(..., description="Primary crop (e.g. Wheat, Rice, Cotton)")
    crop_stage: str = Field(..., description="Current growth stage: sowing, vegetative, flowering, grain_filling, maturity, harvesting")
    soil_type: str = Field(default="loamy", description="Soil type: clay, loamy, sandy, silty, black_soil")
    irrigation_method: str = Field(default="flood", description="Irrigation method: flood, drip, sprinkler, rainfed")

    # Active farm plan
    current_plan: List[FarmActivity] = Field(
        default_factory=list,
        description="List of currently scheduled farm activities"
    )


# ---------------------------------------------------------------------------
# Output Models: Actions, Assessments & Payloads
# ---------------------------------------------------------------------------

class ActionItem(BaseModel):
    """A concrete, practical action recommended for the farmer."""
    action_type: ActionType
    title: str = Field(..., description="Concise action heading (e.g. 'Postpone Scheduled Irrigation')")
    description: str = Field(..., description="Specific, practical step for the farmer to take")
    urgency: UrgencyLevel = Field(default=UrgencyLevel.MEDIUM)
    target_date: Optional[str] = Field(None, description="Original planned date")
    rescheduled_date: Optional[str] = Field(None, description="Suggested new date or window")
    affected_activity_id: Optional[str] = Field(None, description="ID of affected FarmActivity")


class FarmerAssessment(BaseModel):
    """Detailed risk assessment and tailored action plan for a single farmer."""
    farmer_id: str
    farmer_name: str
    crop: str
    crop_stage: str
    risk_level: SeverityLevel
    risk_score: float = Field(..., ge=0.0, le=100.0, description="Risk index between 0 and 100")
    risk_factors: List[str] = Field(default_factory=list, description="List of detected vulnerability factors")
    actions: List[ActionItem] = Field(default_factory=list)

    # Conversational & Plain-Language Explanation ("Why did you change my plan?")
    plain_language_explanation: str = Field(
        ...,
        description="Clear, non-technical explanation citing evidence and confidence"
    )

    # Subsystem-specific payloads
    radio_gpt_script: str = Field(
        ...,
        description="Tailored voice script for Member 4 (Radio-GPT) telephony call"
    )
    dashboard_summary: Dict[str, Any] = Field(
        default_factory=dict,
        description="Structured key metrics and badge states for Member 5 (Dashboard)"
    )

    replanning_required: bool = False
    updated_plan: List[FarmActivity] = Field(default_factory=list)


class StrategistOutput(BaseModel):
    """
    Top-level output emitted by Strategist Agent (Member 3) to the Orchestrator.
    Feeds downstream into Radio-GPT (Member 4), Dashboard (Member 5), and Database (Member 6).
    """
    threat_event_id: str
    overall_risk_level: SeverityLevel
    affected_farmers_count: int
    assessments: List[FarmerAssessment]
    alert_required: bool

    # Helper for seamless Orchestrator integration
    def to_orchestrator_state(self) -> Dict[str, Any]:
        """Convert assessment into Orchestrator's WeatherState patch dictionary."""
        recommended_actions: List[str] = []
        affected_farmers_list: List[Dict[str, Any]] = []
        any_replanning = False

        for a in self.assessments:
            affected_farmers_list.append({
                "id": a.farmer_id,
                "name": a.farmer_name,
                "crop": a.crop,
                "crop_stage": a.crop_stage,
                "risk_level": a.risk_level.value,
                "risk_score": a.risk_score
            })
            for act in a.actions:
                if act.title not in recommended_actions:
                    recommended_actions.append(act.title)
            if a.replanning_required:
                any_replanning = True

        return {
            "risk_level": self.overall_risk_level.value,
            "recommended_actions": recommended_actions,
            "affected_farmers": affected_farmers_list,
            "alert_required": self.alert_required,
            "replanning_required": any_replanning,
            "strategist_assessments": [a.model_dump() for a in self.assessments]
        }
