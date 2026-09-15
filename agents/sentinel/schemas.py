"""
Sentinel Agent Output Schemas (Member 2 Contract).

Defines the structured Threat JSON output emitted by the Sentinel Agent
after observing, normalizing, and verifying weather data from multiple models/APIs.
"""

from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class ThreatType(str, Enum):
    HEAVY_RAIN = "heavy_rain"
    HIGH_WIND = "high_wind"
    EXTREME_HEAT = "extreme_heat"
    FROST = "frost"
    HAIL = "hail"
    CYCLONE = "cyclone"
    DROUGHT = "drought"
    NONE = "none"


class ThreatSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ConfidenceLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ModelForecastData(BaseModel):
    """Normalized snapshot from an individual forecast source/model."""
    model_name: str = Field(..., description="Name of weather model (e.g. ecmwf, gfs, icon, open-meteo)")
    precipitation_mm: float = Field(0.0, description="Predicted 3h precipitation accumulation in mm")
    precipitation_probability_pct: float = Field(0.0, description="Probability of rain in %")
    max_wind_kmh: float = Field(0.0, description="Predicted maximum wind speed in km/h")
    peak_gust_kmh: float = Field(0.0, description="Predicted peak gust in km/h")
    max_temp_c: float = Field(25.0, description="Forecast peak temperature in °C")
    min_temp_c: float = Field(15.0, description="Forecast minimum temperature in °C")
    threat_flag: bool = Field(False, description="Whether this individual model breached safety thresholds")


class MultiModelComparison(BaseModel):
    """Synthesis of multi-source verification and model consensus."""
    models_evaluated: List[str] = Field(default_factory=list)
    agreement_ratio: float = Field(1.0, ge=0.0, le=1.0, description="Fraction of models in consensus")
    rain_range_mm: Dict[str, float] = Field(default_factory=dict, description="min/max spread among models")
    wind_range_kmh: Dict[str, float] = Field(default_factory=dict)
    timing_agreement: bool = Field(True, description="Whether models agree on arrival hour")
    summary: str = Field(..., description="Human-readable summary of model convergence or divergence")


class ThreatEvent(BaseModel):
    """
    Threat JSON contract produced by Sentinel Agent (Member 2).
    Passed as input to Strategist Agent (Member 3).
    """
    event_id: str = Field(..., description="Unique event identifier (e.g. EVT-20260915-001)")
    event_type: str = Field(
        ...,
        description="Threat classification: heavy_rain, high_wind, extreme_heat, frost, hail, cyclone, drought, none"
    )
    severity: str = Field(
        ...,
        description="Severity level: low, medium, high, critical"
    )
    probability: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Forecast probability (0.0 to 1.0, e.g. 0.85 = 85%)"
    )
    confidence: str = Field(
        default="high",
        description="Forecast confidence based on multi-source agreement: low, medium, high"
    )
    confidence_reason: Optional[str] = Field(
        None,
        description="Explanation for confidence (e.g. '3 of 4 forecast models agree on timing and intensity')"
    )
    location: str = Field(..., description="Target location name (e.g. Jalandhar, Punjab)")
    coordinates: Optional[Dict[str, float]] = Field(
        None,
        description="Latitude and Longitude of the affected region"
    )
    time_to_event_minutes: Optional[int] = Field(
        None,
        description="Estimated minutes until weather event begins"
    )
    duration_hours: Optional[float] = Field(
        None,
        description="Expected duration of the weather event in hours"
    )

    # Specific weather parameters
    rainfall_mm: Optional[float] = Field(None, description="Expected precipitation accumulation in mm")
    wind_speed_kmh: Optional[float] = Field(None, description="Expected sustained wind speed in km/h")
    wind_gust_kmh: Optional[float] = Field(None, description="Expected peak wind gust in km/h")
    temp_c: Optional[float] = Field(None, description="Forecast temperature in Celsius")
    temp_max_c: Optional[float] = Field(None, description="Maximum forecast temperature in Celsius")
    temp_min_c: Optional[float] = Field(None, description="Minimum forecast temperature in Celsius")
    humidity_pct: Optional[float] = Field(None, description="Relative humidity percentage")
    hail_risk: Optional[bool] = Field(False, description="Whether hail is anticipated")

    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional raw metadata or source model comparison data"
    )


class SentinelOutput(BaseModel):
    """Complete output produced by Sentinel Agent."""
    threat_detected: bool
    threat: ThreatEvent
    weather_data: Dict[str, Any] = Field(default_factory=dict)
    comparison: Optional[MultiModelComparison] = None
