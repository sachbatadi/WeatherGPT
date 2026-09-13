"""
Sentinel Agent Output Schemas (Member 2 Contract).

Defines the structured Threat JSON output emitted by the Sentinel Agent
after observing and verifying weather data from multiple APIs/models.
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class ThreatEvent(BaseModel):
    """
    Threat JSON contract produced by Sentinel Agent (Member 2).
    Passed as input to Strategist Agent (Member 3).
    """
    event_id: str = Field(..., description="Unique event identifier (e.g. EVT-20260913-001)")
    event_type: str = Field(
        ...,
        description="Threat classification: heavy_rain, high_wind, extreme_heat, frost, hail, cyclone, drought"
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
