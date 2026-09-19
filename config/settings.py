"""
WeatherGPT Centralized Configuration (config/settings.py).

Central source of truth for:
1. Execution modes (Live Open-Meteo vs Mock SIH Disaster Presets)
2. Calendar provider (Mock vs Google Calendar)
3. Agronomic hazard thresholds (Rain, Wind, Heat, Frost)
4. External API endpoints and timeout settings
5. Sensitive credentials loaded from .env
"""

import os
from pathlib import Path
from typing import Optional, List
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Native .env loader (Zero external dependency requirement)
# ---------------------------------------------------------------------------
def _load_env_file() -> None:
    """Load key-value pairs from .env file into os.environ if not already set."""
    env_paths = [
        Path(".env"),
        Path(__file__).resolve().parent.parent / ".env",
    ]
    for path in env_paths:
        if path.is_file():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith("#") or "=" not in line:
                            continue
                        key, val = line.split("=", 1)
                        key = key.strip()
                        val = val.strip().strip("'\"")
                        if key and key not in os.environ:
                            os.environ[key] = val
                break
            except Exception:
                pass


_load_env_file()


# ---------------------------------------------------------------------------
# Settings Schema Definitions
# ---------------------------------------------------------------------------
class SystemExecutionSettings(BaseModel):
    """Core runtime environment and mode toggles."""
    weather_mode: str = Field(
        default_factory=lambda: os.getenv("WEATHER_MODE", "mock").strip().lower(),
        description="Weather source mode: 'mock' (SIH disaster presets) or 'live' (Open-Meteo API)"
    )
    calendar_provider: str = Field(
        default_factory=lambda: os.getenv("CALENDAR_PROVIDER", "mock").strip().lower(),
        description="Calendar backend: 'mock' (in-memory simulator) or 'google' (Google Calendar API)"
    )
    default_location: str = Field(
        default_factory=lambda: os.getenv("DEFAULT_LOCATION", "Jalandhar"),
        description="Default target location name"
    )
    log_level: str = Field(
        default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"),
        description="Logging verbosity level"
    )
    cors_origins: str = Field(
        default_factory=lambda: os.getenv("CORS_ORIGINS", ""),
        description="Comma-separated list of allowed CORS origins for production"
    )
    api_key: Optional[str] = Field(
        default_factory=lambda: os.getenv("API_KEY"),
        description="Optional API key required to access protected farmer and alert endpoints"
    )


class AgronomicHazardThresholds(BaseModel):
    """Meteorological safety limits and agronomic triggers for Sentinel Agent."""
    rain_critical_threshold_mm: float = Field(
        default_factory=lambda: float(os.getenv("RAIN_CRITICAL_MM", 50.0)),
        description="Precipitation causing severe flash flooding and soil inundation"
    )
    rain_high_threshold_mm: float = Field(
        default_factory=lambda: float(os.getenv("RAIN_HIGH_MM", 25.0)),
        description="Precipitation warranting mandatory irrigation cancellation"
    )
    rain_medium_threshold_mm: float = Field(
        default_factory=lambda: float(os.getenv("RAIN_MEDIUM_MM", 12.0)),
        description="Precipitation threshold for weather disturbance monitoring"
    )
    wind_spray_drift_limit_kmh: float = Field(
        default_factory=lambda: float(os.getenv("WIND_SPRAY_LIMIT_KMH", 15.0)),
        description="Maximum safe sustained wind speed for chemical/pesticide spraying"
    )
    wind_gust_high_kmh: float = Field(
        default_factory=lambda: float(os.getenv("WIND_GUST_HIGH_KMH", 40.0)),
        description="Wind gust speed causing lodging or structural damage"
    )
    heat_stress_threshold_c: float = Field(
        default_factory=lambda: float(os.getenv("HEAT_STRESS_C", 38.0)),
        description="Peak temperature triggering crop flower drop and thermal distress"
    )
    heat_critical_temp_c: float = Field(
        default_factory=lambda: float(os.getenv("HEAT_CRITICAL_C", 43.0)),
        description="Extreme heatwave threshold causing rapid desiccation"
    )
    frost_high_temp_c: float = Field(
        default_factory=lambda: float(os.getenv("FROST_HIGH_C", 4.0)),
        description="Low temperature threshold indicating night frost formation"
    )
    frost_critical_temp_c: float = Field(
        default_factory=lambda: float(os.getenv("FROST_CRITICAL_C", 0.5)),
        description="Freezing temperature causing irreversible cellular rupture in crops"
    )


class WeatherApiSettings(BaseModel):
    """External API endpoints and request parameters."""
    geocoding_url: str = "https://geocoding-api.open-meteo.com/v1/search"
    forecast_url: str = "https://api.open-meteo.com/v1/forecast"
    api_timeout_seconds: int = 15
    supported_models: List[str] = ["ECMWF-IFS", "GFS-Global", "ICON-EU"]


class SMSSettings(BaseModel):
    """SMS notification runtime configuration."""
    sms_enabled: bool = Field(
        default_factory=lambda: os.getenv("SMS_ENABLED", "false").strip().lower() in ("true", "1", "yes"),
        description="Global kill-switch for sending real SMS messages"
    )
    sms_provider: str = Field(
        default_factory=lambda: os.getenv("SMS_PROVIDER", "mock").strip().lower(),
        description="Active SMS provider: 'mock' or 'vonage'"
    )
    sms_sender_id: Optional[str] = Field(
        default_factory=lambda: os.getenv("SMS_SENDER_ID")
    )
    vonage_signature_method: str = Field(
        default_factory=lambda: os.getenv("VONAGE_SIGNATURE_METHOD", "sha256").strip().lower(),
        description="Signature algorithm for Vonage webhooks: sha256, sha512, md5, or sha1"
    )


class IntegrationCredentials(BaseModel):
    """Credentials for external services loaded securely from environment."""
    google_application_credentials: Optional[str] = Field(
        default_factory=lambda: os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    )
    google_calendar_id: str = Field(
        default_factory=lambda: os.getenv("GOOGLE_CALENDAR_ID", "primary")
    )
    database_url: Optional[str] = Field(
        default_factory=lambda: os.getenv("DATABASE_URL")
    )
    gemini_api_key: Optional[str] = Field(
        default_factory=lambda: os.getenv("GEMINI_API_KEY")
    )
    vonage_api_key: Optional[str] = Field(
        default_factory=lambda: os.getenv("VONAGE_API_KEY")
    )
    vonage_api_secret: Optional[str] = Field(
        default_factory=lambda: os.getenv("VONAGE_API_SECRET")
    )
    vonage_signature_secret: Optional[str] = Field(
        default_factory=lambda: os.getenv("VONAGE_SIGNATURE_SECRET")
    )


class Settings(BaseModel):
    """Consolidated WeatherGPT Settings Container."""
    system: SystemExecutionSettings = Field(default_factory=SystemExecutionSettings)
    thresholds: AgronomicHazardThresholds = Field(default_factory=AgronomicHazardThresholds)
    api: WeatherApiSettings = Field(default_factory=WeatherApiSettings)
    sms: SMSSettings = Field(default_factory=SMSSettings)
    credentials: IntegrationCredentials = Field(default_factory=IntegrationCredentials)

    @property
    def is_live_weather(self) -> bool:
        """Check if system is set to live weather querying."""
        return self.system.weather_mode == "live"

    @property
    def is_live_calendar(self) -> bool:
        """Check if system is set to live Google Calendar API."""
        return self.system.calendar_provider == "google"

    @property
    def is_sms_enabled(self) -> bool:
        """Check if outbound SMS notifications are enabled."""
        return self.sms.sms_enabled


# Singleton configuration instance for project-wide import
settings = Settings()
