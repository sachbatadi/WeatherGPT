"""
Pydantic Request and Response Schemas (backend/schemas.py).

Strict data validation contracts for WeatherGPT REST API endpoints:
- GET /api/health
- GET /api/weather/current
- POST /api/pipeline/run
- GET /api/farmers
- GET /api/farmers/{farmer_id}/dashboard
- GET /api/alerts
"""

from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

try:
    from pydantic import BaseModel, Field, field_validator
    HAS_PYDANTIC = True
except ImportError:
    HAS_PYDANTIC = False
    # Lightweight fallback for pre-pip-installed environments
    class BaseModel:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
        def model_dump(self) -> Dict[str, Any]:
            return {
                k: getattr(self, k) for k in dir(self)
                if not k.startswith("_") and not callable(getattr(self, k))
            }
        def dict(self) -> Dict[str, Any]:
            return self.model_dump()

    def Field(default=None, default_factory=None, **kwargs):
        if default_factory is not None:
            return default_factory()
        return default

    def field_validator(*args, **kwargs):
        def decorator(fn):
            return fn
        return decorator


# ---------------------------------------------------------------------------
# 1. Health Endpoint Schemas
# ---------------------------------------------------------------------------

class HealthResponse(BaseModel):
    """System health and operational mode status."""
    status: str = Field(default="healthy", description="Application health status")
    weather_mode: str = Field(..., description="Active weather ingestion mode: 'mock' or 'live'")
    calendar_provider: str = Field(..., description="Active calendar backend: 'mock' or 'google'")
    default_location: str = Field(..., description="Default geographic center")
    version: str = Field(default="1.0.0", description="WeatherGPT API Version")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="Current server UTC timestamp"
    )


# ---------------------------------------------------------------------------
# 2. Weather Endpoint Schemas
# ---------------------------------------------------------------------------

class CurrentWeatherResponse(BaseModel):
    """Normalized weather telemetry and threat status for a target location."""
    location: str = Field(..., description="Location name")
    source: str = Field(..., description="Data provider or scenario name")
    temperature_c: float = Field(..., description="Current temperature in Celsius")
    humidity_pct: float = Field(..., description="Relative humidity percentage")
    precipitation_mm: float = Field(..., description="Precipitation accumulation in mm")
    wind_speed_kmh: float = Field(..., description="Sustained wind speed in km/h")
    wind_gust_kmh: Optional[float] = Field(None, description="Peak wind gust in km/h")
    threat_detected: bool = Field(..., description="Whether safety threshold was breached")
    threat_type: Optional[str] = Field(None, description="Classified hazard type (e.g. heavy_rain, high_wind)")
    threat_severity: Optional[str] = Field(None, description="Hazard severity level")
    confidence: Optional[str] = Field(None, description="Consensus confidence level")
    confidence_reason: Optional[str] = Field(None, description="Justification for confidence rating")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="Query timestamp"
    )


# ---------------------------------------------------------------------------
# 3. Pipeline Run Schemas
# ---------------------------------------------------------------------------

VALID_MOCK_SCENARIOS = {"heavy_rain", "high_wind", "extreme_heat", "frost"}
VALID_MODES = {"mock", "live"}


class PipelineRunRequest(BaseModel):
    """Input parameters for triggering the end-to-end agentic workflow."""
    location: str = Field(default="Jalandhar", description="Target district or village in Punjab/Haryana")
    mode: Optional[str] = Field(default=None, description="Optional override: 'mock' or 'live'")
    scenario: Optional[str] = Field(
        default=None,
        description="Optional SIH mock scenario: 'heavy_rain', 'high_wind', 'extreme_heat', 'frost'"
    )

    if HAS_PYDANTIC:
        @field_validator("location")
        @classmethod
        def validate_location(cls, v: str) -> str:
            val = v.strip()
            if not val or len(val) < 2:
                raise ValueError("Location must be a non-empty string with at least 2 characters.")
            if len(val) > 100:
                raise ValueError("Location string must not exceed 100 characters.")
            return val

        @field_validator("mode")
        @classmethod
        def validate_mode(cls, v: Optional[str]) -> Optional[str]:
            if v is not None:
                cleaned = v.strip().lower()
                if cleaned not in VALID_MODES:
                    raise ValueError(f"Invalid mode '{v}'. Must be one of: {sorted(VALID_MODES)}")
                return cleaned
            return v

        @field_validator("scenario")
        @classmethod
        def validate_scenario(cls, v: Optional[str]) -> Optional[str]:
            if v is not None:
                cleaned = v.strip().lower()
                if cleaned not in VALID_MOCK_SCENARIOS:
                    raise ValueError(f"Invalid scenario '{v}'. Must be one of: {sorted(VALID_MOCK_SCENARIOS)}")
                return cleaned
            return v


class PipelineRunResponse(BaseModel):
    """Execution receipt returned after Sentinel -> Strategist -> Executor pipeline execution."""
    status: str = Field(default="completed", description="Execution status: 'completed' or 'monitored'")
    location: str = Field(..., description="Target location")
    threat_detected: bool = Field(..., description="True if severe weather threat was confirmed")
    threat: Optional[Dict[str, Any]] = Field(None, description="Sentinel ThreatEvent payload")
    risk_level: Optional[str] = Field(None, description="Composite agronomic risk rating")
    alert_required: bool = Field(default=False, description="Whether proactive farmer alerts were triggered")
    replanning_required: bool = Field(default=False, description="Whether calendar tasks were rescheduled")
    affected_farmers: List[Dict[str, Any]] = Field(default_factory=list, description="Farmers assessed with risk scores")
    recommended_actions: List[str] = Field(default_factory=list, description="Action items generated by Strategist")
    execution_summary: Optional[Dict[str, Any]] = Field(None, description="Executor dispatch summary receipt")
    audit_event_id: Optional[str] = Field(None, description="Persistent ThreatEvent audit ID logged in SQLite")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="Pipeline execution completion timestamp"
    )


# ---------------------------------------------------------------------------
# 4. Farmer Schemas
# ---------------------------------------------------------------------------

class FarmActivitySchema(BaseModel):
    """Calendar task scheduled for a farmer."""
    activity_id: str
    activity_type: str
    scheduled_date: str
    status: str = "scheduled"
    calendar_event_id: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)


class FarmerProfileResponse(BaseModel):
    """Complete farmer profile with active farm plan."""
    farmer_id: str
    name: str
    phone: Optional[str] = None
    language: str = "en"
    location: str
    district: Optional[str] = None
    state: Optional[str] = None
    land_size_acres: Optional[float] = None
    crop: str
    crop_stage: str
    soil_type: str
    irrigation_method: str
    current_plan: List[Dict[str, Any]] = Field(default_factory=list)


class FarmerListResponse(BaseModel):
    """List response for /api/farmers endpoint."""
    total_count: int
    farmers: List[FarmerProfileResponse]


class FarmerDashboardResponse(BaseModel):
    """Structured dashboard summary card for a specific farmer profile."""
    farmer_id: str
    name: str
    phone: Optional[str] = None
    language: str
    location: str
    crop: str
    crop_stage: str
    soil_type: str
    irrigation_method: str
    risk_level: str = Field(default="low", description="low, medium, high, critical")
    badge_color: str = Field(default="green", description="Color code: green, yellow, orange, red")
    active_plan_count: int
    scheduled_activities: List[Dict[str, Any]] = Field(default_factory=list)
    recent_alerts: List[Dict[str, Any]] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# 5. Alert Schemas
# ---------------------------------------------------------------------------

class AlertLogRecord(BaseModel):
    """Record of a dispatched or queued alert."""
    dispatch_id: str
    threat_event_id: Optional[str] = None
    farmer_id: str
    farmer_name: str
    channel: str
    language: str
    urgency: str
    message: str
    status: str
    dispatched_at: str


class AlertListResponse(BaseModel):
    """List response for /api/alerts endpoint."""
    total_count: int
    alerts: List[AlertLogRecord]


# ---------------------------------------------------------------------------
# 6. Error Response Schema
# ---------------------------------------------------------------------------

class ErrorResponse(BaseModel):
    """Standardized error format returned on validation or resource failure."""
    error: str = Field(..., description="Short error title")
    detail: str = Field(..., description="Human-readable explanation of failure")
    status_code: int = Field(..., description="HTTP status code")
