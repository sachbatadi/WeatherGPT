"""Unit tests for centralized configuration (config/settings.py)."""
import os
import pytest
from config.settings import Settings, SystemExecutionSettings, AgronomicHazardThresholds

def test_default_settings():
    s = Settings()
    assert s.system.weather_mode in ["mock", "live"]
    assert s.thresholds.rain_critical_threshold_mm == 50.0
    assert s.thresholds.rain_high_threshold_mm == 25.0
    assert s.thresholds.wind_spray_drift_limit_kmh == 15.0
    assert s.thresholds.heat_stress_threshold_c == 38.0
    assert s.thresholds.frost_high_temp_c == 4.0
    assert s.api.geocoding_url.startswith("https://")
    assert s.api.forecast_url.startswith("https://")
    assert s.is_live_weather is (s.system.weather_mode == "live")
    assert s.is_live_calendar is (s.system.calendar_provider == "google")

def test_settings_mode_properties():
    s = Settings(
        system=SystemExecutionSettings(weather_mode="live", calendar_provider="google")
    )
    assert s.is_live_weather is True
    assert s.is_live_calendar is True

def test_env_override_simulation(monkeypatch):
    monkeypatch.setenv("WEATHER_MODE", "live")
    monkeypatch.setenv("CALENDAR_PROVIDER", "google")
    monkeypatch.setenv("RAIN_HIGH_MM", "30.0")
    monkeypatch.setenv("DEFAULT_LOCATION", "Amritsar")

    fresh = Settings()
    assert fresh.system.weather_mode == "live"
    assert fresh.system.calendar_provider == "google"
    assert fresh.system.default_location == "Amritsar"
    assert fresh.thresholds.rain_high_threshold_mm == 30.0
    assert fresh.is_live_weather is True
    assert fresh.is_live_calendar is True
