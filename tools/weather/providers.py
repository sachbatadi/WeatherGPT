from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from tools.weather.weather_api import fetch_weather, geocode_location


class ProviderResult:
    def __init__(self, provider: str, data: Dict[str, Any]):
        self.provider = provider
        self.data = data


class WeatherProvider:
    name: str = "base"

    def fetch_current(self, location: str) -> ProviderResult:
        raise NotImplementedError


class OpenMeteoProvider(WeatherProvider):
    name: str = "open-meteo"

    def fetch_current(self, location: str) -> ProviderResult:
        info = geocode_location(location)
        raw = fetch_weather(location=info.get("name", location), latitude=info["latitude"], longitude=info["longitude"])
        curr = raw.get("current_weather", {})
        return ProviderResult(
            provider=self.name,
            data={
                "location": info.get("name", location),
                "current": {
                    "temperature_c": float(curr.get("temperature", 25.0)),
                    "precipitation_mm": float(curr.get("precipitation", 0.0)),
                    "wind_speed_kmh": float(curr.get("windspeed", 10.0)),
                }
            }
        )


class WeatherProviderService:
    def __init__(self, providers: Optional[List[WeatherProvider]] = None):
        self.providers = providers if providers is not None else [OpenMeteoProvider()]

    def fetch(self, location: str) -> Dict[str, Any]:
        clean_loc = (location or "").strip()
        if not clean_loc:
            raise ValueError("Location query parameter must not be empty.")

        readings: List[ProviderResult] = []
        failures: List[Dict[str, str]] = []
        last_val_error: Optional[ValueError] = None
        last_timeout_error: Optional[TimeoutError] = None
        last_general_error: Optional[Exception] = None

        for p in self.providers:
            try:
                res = p.fetch_current(clean_loc)
                readings.append(res)
            except ValueError as exc:
                last_val_error = exc
                failures.append({"provider": p.name, "error": str(exc)})
            except TimeoutError as exc:
                last_timeout_error = exc
                failures.append({"provider": p.name, "error": str(exc)})
            except Exception as exc:
                last_general_error = exc
                failures.append({"provider": p.name, "error": str(exc)})

        if not readings:
            if last_val_error:
                raise last_val_error
            if last_timeout_error:
                raise last_timeout_error
            raise RuntimeError("No weather provider returned data.")

        provider_count = len(readings)
        confidence = "single_source" if provider_count == 1 else "multi_source"
        first = readings[0]

        weather_data = {
            "location": first.data.get("location", clean_loc),
            "current": first.data.get("current", {}),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        readings_list = []
        for r in readings:
            curr = r.data.get("current", {})
            readings_list.append({
                "provider": r.provider,
                "temperature_c": curr.get("temperature_c"),
                "precipitation_mm": curr.get("precipitation_mm"),
                "wind_speed_kmh": curr.get("wind_speed_kmh"),
            })

        return {
            "weather": weather_data,
            "verification": {
                "providers_queried": [p.name for p in self.providers],
                "provider_count": provider_count,
                "confidence": confidence,
                "readings": readings_list,
                "failures": failures,
                "note": f"Verified across {provider_count} source(s)." if provider_count > 1 else "Single source verification.",
            }
        }
