"""Offline tests for provider, grounded chat, and monitoring services."""

import unittest

from backend.app import handle_chat
from services.chat import build_grounded_reply, detect_intent
from services.monitoring import run_monitoring_cycle
from tools.weather.providers import ProviderResult, WeatherProvider, WeatherProviderService


class FakeProvider(WeatherProvider):
    name = "fake-provider"

    def fetch_current(self, location):
        return ProviderResult(
            provider=self.name,
            data={
                "location": location,
                "current": {"temperature_c": 31.0, "precipitation_mm": 2.0, "wind_speed_kmh": 9.0},
            },
        )


class TestRemainingPhases(unittest.TestCase):
    def test_provider_service_marks_single_source_honestly(self):
        result = WeatherProviderService([FakeProvider()]).fetch("Jalandhar")
        self.assertEqual(result["verification"]["provider_count"], 1)
        self.assertEqual(result["verification"]["confidence"], "single_source")
        self.assertEqual(result["weather"]["location"], "Jalandhar")

    def test_chat_is_grounded_and_does_not_use_llm(self):
        weather = {
            "location": "Jalandhar",
            "temperature_c": 26.5,
            "precipitation_mm": 18.0,
            "wind_speed_kmh": 22.0,
            "threat_type": "heavy_rain",
            "threat_severity": "high",
        }
        result = build_grounded_reply("Can I spray pesticides today?", weather)
        self.assertEqual(detect_intent("Can I spray pesticides today?"), "spraying_safety")
        self.assertFalse(result["llm_used"])
        self.assertIn("Postpone spraying", result["reply"])
        self.assertIn("26.5°C", result["reply"])

    def test_chat_handler_uses_mock_structured_weather(self):
        result = handle_chat({
            "message": "Should I irrigate today?",
            "location": "Jalandhar",
            "mode": "mock",
            "scenario": "heavy_rain",
        })
        self.assertFalse(result["llm_used"])
        self.assertEqual(result["intent"], "irrigation")
        self.assertIn("Postpone irrigation", result["reply"])

    def test_monitoring_cycle_uses_runner_results(self):
        farmers = [
            {"farmer_id": "F001", "location": "Jalandhar"},
            {"farmer_id": "F002", "location": "Bathinda"},
        ]

        def fake_runner(payload):
            return {"threat_detected": payload["location"] == "Jalandhar", "risk_level": "high"}

        result = run_monitoring_cycle(farmers, fake_runner)
        self.assertEqual(result["farmers_checked"], 2)
        self.assertEqual(result["threats_detected"], 1)

    def test_pipeline_honors_requested_mock_scenario(self):
        from backend.app import handle_pipeline_run

        result = handle_pipeline_run({
            "location": "Bathinda",
            "mode": "mock",
            "scenario": "high_wind",
        })
        self.assertEqual(result["threat"]["event_type"], "high_wind")

    def test_provider_service_propagates_invalid_location_value_error(self):
        class InvalidLocationProvider(WeatherProvider):
            name = "failing-provider"
            def fetch_current(self, location):
                raise ValueError(f"Location not found: '{location}'")

        service = WeatherProviderService([InvalidLocationProvider()])
        with self.assertRaises(ValueError) as ctx:
            service.fetch("UnknownPlace123")
        self.assertIn("Location not found", str(ctx.exception))

    def test_provider_service_propagates_timeout_error(self):
        class TimeoutProvider(WeatherProvider):
            name = "timeout-provider"
            def fetch_current(self, location):
                raise TimeoutError("Connection to weather API timed out.")

        service = WeatherProviderService([TimeoutProvider()])
        with self.assertRaises(TimeoutError) as ctx:
            service.fetch("Jalandhar")
        self.assertIn("timed out", str(ctx.exception))

    def test_provider_service_handles_general_failure(self):
        class OutageProvider(WeatherProvider):
            name = "outage-provider"
            def fetch_current(self, location):
                raise ConnectionError("503 Service Unavailable")

        service = WeatherProviderService([OutageProvider()])
        with self.assertRaises(RuntimeError) as ctx:
            service.fetch("Jalandhar")
        self.assertIn("No weather provider returned data", str(ctx.exception))

    def test_grounded_reply_with_farmer_profile_and_why_replan(self):
        weather = {
            "location": "Jalandhar",
            "temperature_c": 24.0,
            "precipitation_mm": 55.0,
            "threat_type": "heavy_rain",
            "threat_severity": "critical",
        }
        farmer = {
            "farmer_id": "F001",
            "name": "Gurpreet Singh",
            "crop": "Wheat",
            "crop_stage": "Flowering",
            "soil_type": "Loamy",
        }
        res = build_grounded_reply(
            message="Why did you postpone my irrigation?",
            weather=weather,
            farmer=farmer,
            language="en"
        )
        self.assertEqual(res["intent"], "why_replan")
        self.assertIn("Wheat", res["reply"])
        self.assertIn("heavy_rain", res["reply"])
        self.assertIn("Gurpreet Singh", res["grounding"]["facts_used"][4])

    def test_grounded_reply_multilingual(self):
        weather = {
            "location": "Jalandhar",
            "threat_type": "heavy_rain",
            "precipitation_mm": 30.0,
        }
        hi_res = build_grounded_reply("Irrigation", weather, language="hi")
        self.assertIn("सिंचाई तुरंत रोक दें", hi_res["reply"])

        pa_res = build_grounded_reply("Irrigation", weather, language="pa")
        self.assertIn("ਪਾਣੀ ਲਾਉਣਾ ਤੁਰੰਤ ਰੋਕ ਦਿਓ", pa_res["reply"])


if __name__ == "__main__":
    unittest.main()
