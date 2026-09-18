"""Provider adapters and transparent weather-source verification.

Only adapters that actually return data are included in the consensus result.
This prevents the application from presenting simulated forecasts as independent
weather sources.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .weather_api import fetch_weather


@dataclass(frozen=True)
class ProviderResult:
    provider: str
    data: Dict[str, Any]


class WeatherProvider(ABC):
    """Minimal provider contract used by the service layer."""

    name: str

    @abstractmethod
    def fetch_current(self, location: str) -> ProviderResult:
        """Fetch and normalize weather data for one location."""


class OpenMeteoProvider(WeatherProvider):
    """No-key Open-Meteo adapter, normalized by ``weather_api.fetch_weather``."""

    name = "open-meteo"

    def fetch_current(self, location: str) -> ProviderResult:
        data = fetch_weather(location=location)
        data["source"] = self.name
        return ProviderResult(provider=self.name, data=data)


class IMDProvider(WeatherProvider):
    """Reserved adapter for an authorized IMD/Mausam integration.

    IMD access and terms differ by product, so this adapter deliberately does
    not fabricate data or scrape an undocumented endpoint.
    """

    name = "imd"

    def fetch_current(self, location: str) -> ProviderResult:
        raise RuntimeError("IMD provider is not configured; add an authorized IMD data integration first.")


class WeatherProviderService:
    """Queries configured providers and computes consensus from returned data."""

    def __init__(self, providers: Optional[List[WeatherProvider]] = None):
        self.providers = providers or [OpenMeteoProvider()]

    def fetch(self, location: str) -> Dict[str, Any]:
        successful: List[ProviderResult] = []
        failures: List[Dict[str, str]] = []
        for provider in self.providers:
            try:
                successful.append(provider.fetch_current(location))
            except Exception as exc:
                failures.append({
                    "provider": provider.name,
                    "reason": str(exc),
                    "error_type": exc.__class__.__name__,
                })

        if not successful:
            val_errors = [f for f in failures if f.get("error_type") == "ValueError"]
            if val_errors and len(val_errors) == len(failures):
                raise ValueError(val_errors[0]["reason"])
            timeout_errors = [
                f for f in failures
                if f.get("error_type") in ("TimeoutError", "ConnectTimeout", "ReadTimeout")
            ]
            if timeout_errors:
                raise TimeoutError(timeout_errors[0]["reason"])
            reasons = "; ".join(f"{f['provider']}: {f['reason']}" for f in failures)
            raise RuntimeError(f"No weather provider returned data. Failures: {reasons}")

        primary = successful[0].data
        readings = []
        for result in successful:
            current = result.data.get("current", {})
            readings.append({
                "provider": result.provider,
                "temperature_c": current.get("temperature_c"),
                "precipitation_mm": current.get("precipitation_mm"),
                "wind_speed_kmh": current.get("wind_speed_kmh"),
            })

        return {
            "weather": primary,
            "verification": {
                "providers_queried": [item.provider for item in successful],
                "provider_count": len(successful),
                "confidence": "high" if len(successful) >= 2 else "single_source",
                "readings": readings,
                "failures": failures,
                "note": (
                    "Confidence is single_source until at least two independent "
                    "providers successfully return data."
                    if len(successful) == 1 else "Independent provider readings were returned."
                ),
            },
        }
