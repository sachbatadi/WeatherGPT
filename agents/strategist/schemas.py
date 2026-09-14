"""
Strategist Agent Schemas (Member 3).

Defines the core data models and contracts for:
1. Input: Threat JSON + Farm Profiles & Plans
2. Processing: Agronomic risk evaluations, risk score breakdown
3. Conversational AI: Answering farmer queries ("Why did you change my plan?")
4. Output: Multilingual Voice Scripts (Radio-GPT), Dashboard Cards, and Re-planning Actions.
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
    POTATO = "potato"
    SUGARCANE = "sugarcane"
    SOYBEAN = "soybean"
    PULSES = "pulses"
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
    RED_SOIL = "red_soil"


class IrrigationMethod(str, Enum):
    FLOOD = "flood"
    DRIP = "drip"
    SPRINKLER = "sprinkler"
    FURROW = "furrow"
    RAINFED = "rainfed"


class ActionType(str, Enum):
    POSTPONE_IRRIGATION = "postpone_irrigation"
    RESCHEDULE_SPRAY = "reschedule_spray"
    DELAY_FERTILIZATION = "delay_fertilization"
    EXPEDITE_HARVEST = "expedite_harvest"
    HALT_HARVEST = "halt_harvest"
    DRAINAGE_PREPARATION = "drainage_preparation"
    PROTECTIVE_COVERING = "protective_covering"
    HEAT_STRESS_MITIGATION = "heat_stress_mitigation"
    FROST_PROTECTION = "frost_protection"
    DISEASE_PREVENTATIVE = "disease_preventative"
    NO_ACTION = "no_action"


class UrgencyLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    IMMEDIATE = "immediate"


# ---------------------------------------------------------------------------
# Risk Factor Breakdown
# ---------------------------------------------------------------------------

class RiskBreakdown(BaseModel):
    """Component-level risk breakdown for detailed dashboard telemetry."""
    precipitation_risk: float = Field(0.0, ge=0.0, le=100.0, description="Flooding / waterlogging / pollen wash risk")
    wind_risk: float = Field(0.0, ge=0.0, le=100.0, description="Spray drift / lodging risk")
    thermal_risk: float = Field(0.0, ge=0.0, le=100.0, description="Heatwave or frost risk")
    disease_risk: float = Field(0.0, ge=0.0, le=100.0, description="High humidity fungal / blight risk")


# ---------------------------------------------------------------------------
# Farm Profile & Scheduled Activities
# ---------------------------------------------------------------------------

class FarmActivity(BaseModel):
    """An individual farm task scheduled in the farmer's calendar."""
    activity_id: str = Field(..., description="Unique activity ID (e.g. ACT-001)")
    activity_type: str = Field(
        ...,
        description="Type of activity: irrigation, spraying, harvesting, fertilization, sowing"
    )
    scheduled_date: str = Field(
        ...,
        description="Scheduled date string (e.g. 2026-09-15)"
    )
    details: Dict[str, Any] = Field(
        default_factory=dict,
        description="Activity details such as chemical name, target area, water depth"
    )
    status: str = Field(
        default="scheduled",
        description="Status: scheduled, postponed, completed, cancelled, in_progress"
    )
    calendar_event_id: Optional[str] = Field(
        default=None,
        description="Linked Google Calendar event identifier if synchronized"
    )


class FarmerProfile(BaseModel):
    """
    Farmer Profile & active context stored in Database.
    """
    farmer_id: str = Field(..., description="Unique identifier (e.g. F001)")
    name: str = Field(..., description="Farmer full name")
    phone: Optional[str] = Field(None, description="Contact phone number for SMS/voice alert")
    language: str = Field(default="en", description="Preferred language code: en, hi, pa")
    location: str = Field(..., description="Village / District (e.g. Jalandhar)")
    district: Optional[str] = None
    state: Optional[str] = None
    land_size_acres: Optional[float] = Field(None, description="Land area in acres")

    # Agronomic context
    crop: str = Field(..., description="Primary crop (e.g. Wheat, Rice, Cotton, Tomato)")
    crop_stage: str = Field(..., description="Current growth stage: sowing, vegetative, flowering, grain_filling, maturity, harvesting")
    soil_type: str = Field(default="loamy", description="Soil type: clay, loamy, sandy, silty, black_soil")
    irrigation_method: str = Field(default="flood", description="Method: flood, drip, sprinkler, furrow, rainfed")

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


class LanguageVoiceScripts(BaseModel):
    """Multilingual voice alert scripts for Member 4 (Radio-GPT)."""
    en: str = Field(..., description="English script for TTS / Phone Call")
    hi: str = Field(..., description="Hindi (हिन्दी) script for TTS / Phone Call")
    pa: str = Field(..., description="Punjabi (ਪੰਜਾਬੀ) script for TTS / Phone Call")


class NextObservationTrigger(BaseModel):
    """Instruction for Sentinel Agent when to re-evaluate the field (Agent Loop)."""
    trigger_type: str = Field(..., description="e.g. 'reassess_soil_moisture', 'wind_normalization'")
    reassess_after_hours: int = Field(..., description="Hours to wait before re-checking forecast/soil")
    condition: str = Field(..., description="Condition to verify before reverting or progressing plan")


class FarmerAssessment(BaseModel):
    """Detailed risk assessment and tailored action plan for a single farmer."""
    farmer_id: str
    farmer_name: str
    crop: str
    crop_stage: str
    soil_type: str
    risk_level: SeverityLevel
    risk_score: float = Field(..., ge=0.0, le=100.0, description="Composite risk index between 0 and 100")
    risk_breakdown: RiskBreakdown = Field(default_factory=RiskBreakdown)
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
        description="Default voice script (in farmer's preferred language)"
    )
    multilingual_scripts: LanguageVoiceScripts = Field(
        ...,
        description="Complete multi-lingual scripts (English, Hindi, Punjabi)"
    )
    dashboard_summary: Dict[str, Any] = Field(
        default_factory=dict,
        description="Structured key metrics and badge states for Member 5 (Dashboard)"
    )

    replanning_required: bool = False
    updated_plan: List[FarmActivity] = Field(default_factory=list)
    next_observation: Optional[NextObservationTrigger] = None


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
                "soil_type": a.soil_type,
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


# ---------------------------------------------------------------------------
# Conversational Q&A Schemas ("Why did you change my plan?")
# ---------------------------------------------------------------------------

class FarmerQueryRequest(BaseModel):
    """Incoming question from farmer via chat or voice (Module 10)."""
    farmer_id: str
    query: str = Field(..., description="Question asked by farmer, e.g. 'Why did you postpone my watering?'")
    language: str = Field(default="en", description="User language: en, hi, pa")


class FarmerQueryResponse(BaseModel):
    """Response answering the farmer's question with facts, confidence, and reassurance."""
    farmer_id: str
    query: str
    answer: str = Field(..., description="Direct, compassionate, evidence-based answer")
    evidence: Dict[str, Any] = Field(default_factory=dict, description="Underlying weather and soil facts")
    recommended_next_step: str = Field(..., description="Action farmer should take right now")
