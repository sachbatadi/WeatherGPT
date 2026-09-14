"""
Integration Tests for WeatherGPT Agent Workflow:
Sentinel → Orchestrator → Strategist → FarmerDB.

Scenarios covered:
1. No Threat (Sentinel detects no threat → Orchestrator routes to monitor/END, Strategist does not run)
2. Heavy Rain (High rainfall → Strategist reschedules irrigation/fertilization, drainage alerts)
3. Extreme Heat (High temperatures → Thermal stress mitigation actions, no rain assumptions)
4. Multi-Hazard (Heavy rain + high winds + high humidity → Combined risk breakdown and multi-factor actions)
"""

import copy
import unittest
from unittest.mock import patch

from agents.orchestrator.graph import build_graph
from agents.orchestrator.state import WeatherState
from agents.orchestrator.nodes import run_strategist
from tools.farmer.farmer_db import default_farmer_db, INITIAL_FARMERS_DATA


class TestAgentSystemIntegration(unittest.TestCase):
    """
    End-to-end integration tests for the compiled LangGraph workflow.
    """

    def setUp(self):
        """Reset the shared in-memory FarmerDB to ensure test isolation and determinism."""
        default_farmer_db._farmers = {
            f["farmer_id"]: copy.deepcopy(f) for f in INITIAL_FARMERS_DATA
        }

    def test_no_threat_stops_before_strategist(self):
        """
        Scenario 1: NO THREAT
        When Sentinel detects no significant threat, Orchestrator must route to
        monitor/END, Strategist must NOT execute, and no proactive alert should be issued.
        """
        def mock_no_threat_sentinel(state: WeatherState) -> WeatherState:
            state["threat_detected"] = False
            state["weather_data"] = {
                "status": "clear",
                "temperature_c": 24.0,
                "rainfall_mm": 0.0,
                "wind_speed_kmh": 6.0
            }
            return state

        with patch("agents.orchestrator.graph.run_sentinel", side_effect=mock_no_threat_sentinel), \
             patch("agents.orchestrator.graph.run_strategist", wraps=run_strategist) as mock_strategist:

            graph = build_graph()
            initial_state: WeatherState = {"location": "Jalandhar"}
            result = graph.invoke(initial_state)

            # Assert Sentinel output
            self.assertFalse(result.get("threat_detected", True))

            # Assert Strategist did NOT execute
            mock_strategist.assert_not_called()

            # Assert no alerts or replanning occurred
            self.assertFalse(result.get("alert_required", False))
            self.assertNotIn("strategist_output", result)
            self.assertNotIn("recommended_actions", result)
            self.assertNotIn("affected_farmers", result)

    def test_heavy_rain_flows_to_strategist(self):
        """
        Scenario 2: HEAVY RAIN
        When Sentinel detects a heavy rain threat, Orchestrator routes to Strategist,
        which evaluates affected farmers, generates risk scores, postpones conflicting
        irrigation/fertilization, and outputs action plans.
        """
        def mock_heavy_rain_sentinel(state: WeatherState) -> WeatherState:
            state["threat_detected"] = True
            state["threat"] = {
                "event_id": "EVT-RAIN-TEST-001",
                "event_type": "heavy_rain",
                "severity": "high",
                "probability": 0.85,
                "confidence": "high",
                "location": state.get("location", "Jalandhar"),
                "time_to_event_minutes": 30,
                "duration_hours": 3.0,
                "rainfall_mm": 60.0,
                "wind_speed_kmh": 22.0,
                "temp_c": 26.0,
                "humidity_pct": 88.0
            }
            return state

        with patch("agents.orchestrator.graph.run_sentinel", side_effect=mock_heavy_rain_sentinel):
            graph = build_graph()
            initial_state: WeatherState = {"location": "Jalandhar"}
            result = graph.invoke(initial_state)

            # 1. Threat detection & routing verified
            self.assertTrue(result.get("threat_detected"))
            self.assertEqual(result.get("location"), "Jalandhar")

            # 2. Risk assessment produced
            self.assertIn(result.get("risk_level"), ["high", "critical"])
            self.assertTrue(result.get("alert_required"))
            self.assertTrue(result.get("replanning_required"))

            # 3. Affected farmers evaluated via FarmerDB
            affected = result.get("affected_farmers", [])
            self.assertGreaterEqual(len(affected), 2)
            farmer_ids = [f["id"] for f in affected]
            self.assertIn("F001", farmer_ids)
            self.assertIn("F002", farmer_ids)

            # 4. Recommended actions address heavy rain hazards
            actions = result.get("recommended_actions", [])
            self.assertGreater(len(actions), 0)
            self.assertTrue(any("irrigation" in act.lower() for act in actions))
            self.assertTrue(any("drainage" in act.lower() for act in actions))

            # 5. Output payloads exist
            self.assertIn("strategist_output", result)
            self.assertIn("radio_gpt_payload", result)
            self.assertIn("dashboard_payload", result)

            # Verify Radio-GPT payload format without executing Radio-GPT
            radio_payload = result["radio_gpt_payload"]
            self.assertIsInstance(radio_payload, list)
            self.assertGreaterEqual(len(radio_payload), 1)
            self.assertIn("multilingual_scripts", radio_payload[0])

    def test_extreme_heat_flows_to_strategist(self):
        """
        Scenario 3: EXTREME HEAT
        When Sentinel detects an extreme heat event (44°C), Strategist evaluates thermal
        stress on flowering crops and produces heat-specific mitigations (irrigation/mulch)
        without assuming rainfall.
        """
        def mock_heat_sentinel(state: WeatherState) -> WeatherState:
            state["threat_detected"] = True
            state["threat"] = {
                "event_id": "EVT-HEAT-TEST-002",
                "event_type": "extreme_heat",
                "severity": "high",
                "probability": 0.90,
                "confidence": "high",
                "location": state.get("location", "Jalandhar"),
                "time_to_event_minutes": 120,
                "duration_hours": 6.0,
                "rainfall_mm": 0.0,
                "temp_c": 42.0,
                "temp_max_c": 44.0,
                "wind_speed_kmh": 8.0,
                "humidity_pct": 25.0
            }
            return state

        with patch("agents.orchestrator.graph.run_sentinel", side_effect=mock_heat_sentinel):
            graph = build_graph()
            initial_state: WeatherState = {"location": "Jalandhar"}
            result = graph.invoke(initial_state)

            # Threat detected and routed
            self.assertTrue(result.get("threat_detected"))
            self.assertIn(result.get("risk_level"), ["high", "critical"])
            self.assertTrue(result.get("alert_required"))

            # Heat stress mitigations generated
            actions = result.get("recommended_actions", [])
            self.assertGreater(len(actions), 0)
            self.assertTrue(
                any("mulch" in act.lower() or "heat" in act.lower() or "evening irrigation" in act.lower() for act in actions),
                f"Expected heat stress mitigations, but got: {actions}"
            )

            # Verify no rainfall-specific advice was mistakenly generated
            self.assertFalse(
                any("drainage" in act.lower() for act in actions),
                "Drainage preparation should NOT be recommended for extreme heat with zero rain."
            )

    def test_multi_hazard_risk_assessment(self):
        """
        Scenario 4: MULTI-HAZARD
        When Sentinel detects combined severe weather (heavy rainfall 75mm + strong winds
        45km/h + high humidity 92%), Strategist evaluates all hazard dimensions simultaneously,
        produces a composite risk breakdown, and generates holistic mitigation actions.
        """
        def mock_multi_hazard_sentinel(state: WeatherState) -> WeatherState:
            state["threat_detected"] = True
            state["threat"] = {
                "event_id": "EVT-MULTI-TEST-003",
                "event_type": "cyclone",
                "severity": "critical",
                "probability": 0.95,
                "confidence": "high",
                "location": state.get("location", "Jalandhar"),
                "time_to_event_minutes": 20,
                "duration_hours": 5.0,
                "rainfall_mm": 75.0,
                "wind_speed_kmh": 45.0,
                "temp_c": 22.0,
                "humidity_pct": 92.0,
                "hail_risk": False
            }
            return state

        with patch("agents.orchestrator.graph.run_sentinel", side_effect=mock_multi_hazard_sentinel):
            graph = build_graph()
            initial_state: WeatherState = {"location": "Jalandhar"}
            result = graph.invoke(initial_state)

            # Workflow execution succeeds without crashing
            self.assertTrue(result.get("threat_detected"))
            self.assertEqual(result.get("risk_level"), "critical")
            self.assertTrue(result.get("alert_required"))
            self.assertTrue(result.get("replanning_required"))

            # Assessments reflect multiple hazard categories
            assessments = result.get("strategist_assessments", [])
            self.assertGreater(len(assessments), 0)

            first_assessment = assessments[0]
            breakdown = first_assessment.get("risk_breakdown", {})
            self.assertGreater(breakdown.get("precipitation_risk", 0.0), 50.0)
            self.assertGreater(breakdown.get("wind_risk", 0.0), 50.0)
            self.assertGreater(breakdown.get("disease_risk", 0.0), 0.0)

            # Verify actions address both water and wind hazards
            actions = result.get("recommended_actions", [])
            has_wind_action = any("wind" in act.lower() or "spray" in act.lower() for act in actions)
            has_water_action = any("drainage" in act.lower() or "irrigation" in act.lower() for act in actions)
            self.assertTrue(has_wind_action, f"Expected wind/spray action in: {actions}")
            self.assertTrue(has_water_action, f"Expected water/drainage action in: {actions}")


if __name__ == "__main__":
    unittest.main()
