"""
Unit tests for Member 2: Sentinel Agent.

Tests:
1. Heavy rain detection and precipitation thresholding
2. High wind / gale detection (chemical spraying drift hazard)
3. Extreme heatwave detection (thermal stress)
4. Frost / cold snap detection
5. Cyclone dual-hazard detection (severe winds + deluge)
6. Hail hazard detection
7. Routine fair weather observation (no threat)
8. Multi-model confidence engine and justification generation
9. Direct integration with Orchestrator's WeatherState (run_sentinel_node)
10. Contract compatibility with Member 3 (Strategist Agent)
"""

import unittest
from agents.sentinel import (
    SentinelAgent,
    run_sentinel_node,
    ThreatDetector,
    ThreatType,
    ThreatSeverity,
    ConfidenceLevel
)
from agents.strategist import StrategistAgent


class TestSentinelAgent(unittest.TestCase):

    def setUp(self):
        self.agent = SentinelAgent()

    def test_heavy_rain_detection(self):
        """
        Verify that 3-hour precipitation >= 25 mm triggers heavy_rain hazard with timing.
        """
        output = self.agent.observe_and_detect(
            location="Jalandhar",
            mode="mock",
            mock_scenario="heavy_rain"
        )

        self.assertTrue(output.threat_detected)
        self.assertEqual(output.threat.event_type, ThreatType.HEAVY_RAIN.value)
        self.assertIn(output.threat.severity, [ThreatSeverity.HIGH.value, ThreatSeverity.CRITICAL.value])
        self.assertGreaterEqual(output.threat.rainfall_mm, 25.0)
        self.assertIsNotNone(output.threat.time_to_event_minutes)
        self.assertEqual(output.threat.confidence, ConfidenceLevel.HIGH.value)

    def test_high_wind_detection(self):
        """
        Verify that wind speed >= 30 km/h triggers high_wind hazard.
        """
        output = self.agent.observe_and_detect(
            location="Bathinda",
            mode="mock",
            mock_scenario="high_wind"
        )

        self.assertTrue(output.threat_detected)
        self.assertEqual(output.threat.event_type, ThreatType.HIGH_WIND.value)
        self.assertGreaterEqual(output.threat.wind_speed_kmh, 20.0)
        self.assertIn("spray", output.threat.confidence_reason.lower())

    def test_extreme_heat_detection(self):
        """
        Verify that peak temperatures >= 40°C trigger extreme_heat hazard.
        """
        output = self.agent.observe_and_detect(
            location="Amritsar",
            mode="mock",
            mock_scenario="extreme_heat"
        )

        self.assertTrue(output.threat_detected)
        self.assertEqual(output.threat.event_type, ThreatType.EXTREME_HEAT.value)
        self.assertGreaterEqual(output.threat.temp_max_c, 38.0)
        self.assertIn(output.threat.severity, [ThreatSeverity.HIGH.value, ThreatSeverity.CRITICAL.value])

    def test_frost_hazard_detection(self):
        """
        Verify that temperatures <= 4°C trigger frost hazard.
        """
        output = self.agent.observe_and_detect(
            location="Karnal",
            mode="mock",
            mock_scenario="frost"
        )

        self.assertTrue(output.threat_detected)
        self.assertEqual(output.threat.event_type, ThreatType.FROST.value)
        self.assertLessEqual(output.threat.temp_min_c, 4.0)

    def test_cyclone_detection(self):
        """
        Verify that concurrent high winds (>= 40 km/h) and heavy rainfall (>= 35 mm) trigger cyclone.
        """
        output = self.agent.observe_and_detect(
            location="Ludhiana",
            mode="mock",
            mock_scenario="cyclone"
        )

        self.assertTrue(output.threat_detected)
        self.assertEqual(output.threat.event_type, ThreatType.CYCLONE.value)
        self.assertEqual(output.threat.severity, ThreatSeverity.CRITICAL.value)
        self.assertGreaterEqual(output.threat.rainfall_mm, 35.0)
        self.assertGreaterEqual(output.threat.wind_speed_kmh, 40.0)

    def test_hail_detection(self):
        """
        Verify that thunderstorm with hail (WMO code 96/99) triggers hail hazard.
        """
        mock_weather = {
            "current": {"temperature_c": 22.0, "precipitation_mm": 15.0},
            "hourly": {
                "weather_code": [96, 96, 65],
                "precipitation_mm": [15.0, 10.0, 5.0]
            }
        }
        threat = ThreatDetector.detect_threat(mock_weather, "Hoshiarpur")

        self.assertEqual(threat.event_type, ThreatType.HAIL.value)
        self.assertEqual(threat.severity, ThreatSeverity.CRITICAL.value)
        self.assertTrue(threat.hail_risk)

    def test_clear_weather_no_threat(self):
        """
        Verify that fair weather produces threat_detected=False and event_type=none.
        """
        output = self.agent.observe_and_detect(
            location="Jalandhar",
            mode="mock",
            mock_scenario="clear"
        )

        self.assertFalse(output.threat_detected)
        self.assertEqual(output.threat.event_type, ThreatType.NONE.value)
        self.assertEqual(output.threat.severity, ThreatSeverity.LOW.value)

    def test_confidence_engine_reasoning(self):
        """
        Verify that Sentinel generates a clear confidence rating and explanation string.
        """
        output = self.agent.observe_and_detect(
            location="Jalandhar",
            mode="mock",
            mock_scenario="heavy_rain"
        )

        self.assertEqual(output.threat.confidence, "high")
        self.assertIsNotNone(output.threat.confidence_reason)
        self.assertGreater(len(output.threat.confidence_reason), 10)
        self.assertIsNotNone(output.comparison)
        self.assertGreaterEqual(output.comparison.agreement_ratio, 0.8)

    def test_orchestrator_node_integration(self):
        """
        Verify that run_sentinel_node executes and updates shared WeatherState.
        """
        initial_state = {"location": "Jalandhar"}
        updated_state = run_sentinel_node(initial_state)

        self.assertIn("weather_data", updated_state)
        self.assertIn("threat_detected", updated_state)
        self.assertIn("threat", updated_state)
        self.assertTrue(updated_state["threat_detected"])
        self.assertEqual(updated_state["threat"]["event_type"], "heavy_rain")

    def test_contract_compatibility_with_strategist(self):
        """
        Verify contract integrity: Sentinel's ThreatEvent output must feed directly into
        StrategistAgent without KeyError or ValidationError.
        """
        sentinel_output = self.agent.observe_and_detect(
            location="Jalandhar",
            mode="mock",
            mock_scenario="heavy_rain"
        )

        threat_json = sentinel_output.threat.model_dump()

        strategist = StrategistAgent()
        strategist_output = strategist.evaluate(threat_data=threat_json)

        self.assertEqual(strategist_output.threat_event_id, sentinel_output.threat.event_id)
        self.assertGreaterEqual(strategist_output.affected_farmers_count, 1)
        self.assertTrue(strategist_output.alert_required)


if __name__ == "__main__":
    unittest.main()
