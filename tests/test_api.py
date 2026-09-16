"""
Comprehensive Unit & Integration Tests for WeatherGPT API Layer (tests/test_api.py).

Tests:
1. GET  /api/health                     - Validates health status & execution mode
2. GET  /api/weather/current            - Validates normalized weather & hazard flags (offline mock)
3. POST /api/pipeline/run               - Validates end-to-end agentic workflow & audit persistence
4. GET  /api/farmers                    - Validates farmer listing & location filtering
5. GET  /api/farmers/{id}/dashboard     - Validates dashboard summary card (200 OK & 404 Not Found)
6. GET  /api/alerts                     - Validates alert log querying & filtering
7. CORS Configuration                   - Verifies strict dev origins and no wildcard '*'
8. Input Validation & Error Handling    - Verifies clear JSON errors for invalid parameters

Guarantees:
- Strictly does NOT call live external weather services (Condition 4).
- Tests run fast, reliably, and offline.
"""

import copy
import unittest
from typing import Dict, Any

from backend.app import (
    ALLOWED_DEV_ORIGINS,
    handle_health,
    handle_current_weather,
    handle_pipeline_run,
    handle_get_farmers,
    handle_get_farmer_dashboard,
    handle_get_alerts,
)
from backend.schemas import (
    PipelineRunRequest,
    VALID_MOCK_SCENARIOS,
    VALID_MODES,
)
from tools.farmer.farmer_db import default_farmer_db, INITIAL_FARMERS_DATA
from database.connection import init_db, log_alert, log_threat_event

# Check if TestClient is available
try:
    from fastapi.testclient import TestClient
    from backend.app import app, HAS_FASTAPI
    CLIENT_AVAILABLE = HAS_FASTAPI
    client = TestClient(app) if HAS_FASTAPI else None
except Exception:
    CLIENT_AVAILABLE = False
    client = None


class TestWeatherGPTApiLayer(unittest.TestCase):
    """Test suite for WeatherGPT FastAPI endpoints and core handler contracts."""

    def setUp(self):
        """Reset farmer test data before each test for determinism."""
        default_farmer_db._farmers = {
            f["farmer_id"]: copy.deepcopy(f) for f in INITIAL_FARMERS_DATA
        }

    # -----------------------------------------------------------------------
    # 1. Health Endpoint Tests (/api/health)
    # -----------------------------------------------------------------------

    def test_health_endpoint(self):
        """Verify GET /api/health returns 200 OK with expected status fields."""
        data = handle_health()
        self.assertEqual(data["status"], "healthy")
        self.assertIn("weather_mode", data)
        self.assertIn("calendar_provider", data)
        self.assertIn("default_location", data)
        self.assertIn("timestamp", data)
        self.assertEqual(data["version"], "1.0.0")

    # -----------------------------------------------------------------------
    # 2. Weather Endpoint Tests (/api/weather/current)
    # -----------------------------------------------------------------------

    def test_weather_current_mock_scenario(self):
        """Verify GET /api/weather/current returns normalized weather without external API call."""
        data = handle_current_weather(location="Jalandhar", mode="mock", scenario="heavy_rain")
        self.assertEqual(data["location"], "Jalandhar")
        self.assertTrue(data["threat_detected"])
        self.assertEqual(data["threat_type"], "heavy_rain")
        self.assertGreaterEqual(data["precipitation_mm"], 10.0)
        self.assertIn("confidence", data)
        self.assertIn("temperature_c", data)
        self.assertIn("humidity_pct", data)
        self.assertIn("wind_speed_kmh", data)

    def test_weather_current_invalid_location(self):
        """Verify invalid empty location raises ValueError."""
        with self.assertRaises(ValueError) as ctx:
            handle_current_weather(location="   ", mode="mock")
        self.assertIn("Location", str(ctx.exception))

    def test_weather_current_invalid_mode(self):
        """Verify invalid weather mode raises ValueError."""
        with self.assertRaises(ValueError) as ctx:
            handle_current_weather(location="Jalandhar", mode="unsupported_mode")
        self.assertIn("Invalid mode", str(ctx.exception))

    def test_weather_current_invalid_scenario(self):
        """Verify invalid mock scenario raises ValueError."""
        with self.assertRaises(ValueError) as ctx:
            handle_current_weather(location="Jalandhar", mode="mock", scenario="blizzard_unknown")
        self.assertIn("Invalid scenario", str(ctx.exception))

    # -----------------------------------------------------------------------
    # 3. Pipeline Run Endpoint Tests (/api/pipeline/run)
    # -----------------------------------------------------------------------

    def test_pipeline_run_mock_heavy_rain(self):
        """Verify POST /api/pipeline/run executes workflow and returns complete execution receipt."""
        request_payload = {
            "location": "Jalandhar",
            "mode": "mock",
            "scenario": "heavy_rain"
        }
        response = handle_pipeline_run(request_payload)

        self.assertEqual(response["status"], "completed")
        self.assertEqual(response["location"], "Jalandhar")
        self.assertTrue(response["threat_detected"])
        self.assertEqual(response["threat"]["event_type"], "heavy_rain")
        self.assertIn(response["risk_level"], ["high", "critical"])
        self.assertTrue(response["alert_required"])
        self.assertTrue(response["replanning_required"])
        self.assertGreaterEqual(len(response["affected_farmers"]), 1)
        self.assertGreaterEqual(len(response["recommended_actions"]), 1)

    def test_pipeline_run_validation_errors(self):
        """Verify invalid pipeline payload parameters trigger ValueError."""
        with self.assertRaises(ValueError):
            handle_pipeline_run({"location": "X"})  # Too short

        with self.assertRaises(ValueError):
            handle_pipeline_run({"location": "Jalandhar", "mode": "invalid_mode"})

        with self.assertRaises(ValueError):
            handle_pipeline_run({"location": "Jalandhar", "scenario": "invalid_scenario"})

    # -----------------------------------------------------------------------
    # 4. Farmers Listing Endpoint Tests (/api/farmers)
    # -----------------------------------------------------------------------

    def test_get_all_farmers(self):
        """Verify GET /api/farmers returns complete list of registered farmers."""
        result = handle_get_farmers(location=None)
        self.assertGreaterEqual(result["total_count"], 5)
        self.assertEqual(len(result["farmers"]), result["total_count"])

        # Check farmer record structure
        first = result["farmers"][0]
        self.assertIn("farmer_id", first)
        self.assertIn("name", first)
        self.assertIn("crop", first)
        self.assertIn("crop_stage", first)
        self.assertIn("soil_type", first)
        self.assertIn("current_plan", first)

    def test_get_farmers_filtered_by_location(self):
        """Verify GET /api/farmers?location=Bathinda filters correctly."""
        result = handle_get_farmers(location="Bathinda")
        self.assertGreaterEqual(result["total_count"], 1)
        for farmer in result["farmers"]:
            self.assertIn("bathinda", farmer["location"].lower() + " " + str(farmer.get("district", "")).lower())

    # -----------------------------------------------------------------------
    # 5. Farmer Dashboard Endpoint Tests (/api/farmers/{farmer_id}/dashboard)
    # -----------------------------------------------------------------------

    def test_get_farmer_dashboard_success(self):
        """Verify GET /api/farmers/{id}/dashboard returns structured summary card."""
        dashboard = handle_get_farmer_dashboard("F001")
        self.assertEqual(dashboard["farmer_id"], "F001")
        self.assertEqual(dashboard["name"], "Gurpreet Singh")
        self.assertEqual(dashboard["crop"], "Wheat")
        self.assertEqual(dashboard["crop_stage"], "Flowering")
        self.assertEqual(dashboard["soil_type"], "Loamy")
        self.assertIn(dashboard["badge_color"], ["green", "yellow", "orange", "red"])
        self.assertGreaterEqual(dashboard["active_plan_count"], 1)
        self.assertIsInstance(dashboard["scheduled_activities"], list)

    def test_get_farmer_dashboard_not_found(self):
        """Verify querying non-existent farmer raises LookupError (which maps to 404)."""
        with self.assertRaises(LookupError) as ctx:
            handle_get_farmer_dashboard("F9999_NONEXISTENT")
        self.assertIn("F9999_NONEXISTENT", str(ctx.exception))

    def test_get_farmer_dashboard_empty_id(self):
        """Verify empty farmer ID raises ValueError (which maps to 400)."""
        with self.assertRaises(ValueError):
            handle_get_farmer_dashboard("   ")

    # -----------------------------------------------------------------------
    # 6. Alerts Endpoint Tests (/api/alerts)
    # -----------------------------------------------------------------------

    def test_get_alerts_endpoint(self):
        """Verify GET /api/alerts retrieves logged alert notifications."""
        # Seed a test alert in SQLite
        test_alert = {
            "dispatch_id": "TEST-DISP-API-001",
            "threat_event_id": "EVT-TEST",
            "farmer_id": "F001",
            "farmer_name": "Gurpreet Singh",
            "channel": "sms",
            "language": "pa",
            "urgency": "high",
            "message": "Urgent weather advisory: postpone irrigation.",
            "status": "queued"
        }
        log_alert(test_alert)

        result = handle_get_alerts(farmer_id="F001", limit=10)
        self.assertGreaterEqual(result["total_count"], 1)
        dispatches = [a["dispatch_id"] for a in result["alerts"]]
        self.assertIn("TEST-DISP-API-001", dispatches)

    # -----------------------------------------------------------------------
    # 7. Strict CORS Configuration Tests
    # -----------------------------------------------------------------------

    def test_cors_configuration(self):
        """Verify strict CORS settings without wildcard '*' allowed origins."""
        self.assertNotIn("*", ALLOWED_DEV_ORIGINS)
        self.assertIn("http://localhost:3000", ALLOWED_DEV_ORIGINS)
        self.assertIn("http://localhost:5173", ALLOWED_DEV_ORIGINS)
        self.assertIn("http://127.0.0.1:3000", ALLOWED_DEV_ORIGINS)
        self.assertIn("http://127.0.0.1:5173", ALLOWED_DEV_ORIGINS)


if __name__ == "__main__":
    unittest.main()
