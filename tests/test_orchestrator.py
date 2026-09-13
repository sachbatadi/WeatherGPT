"""
Unit and Integration Tests for Orchestrator Agent (LangGraph Workflow).
"""

import unittest
from agents.orchestrator.graph import build_graph
from agents.orchestrator.router import threat_router
from agents.orchestrator.nodes import run_sentinel, run_strategist


class TestOrchestratorIntegration(unittest.TestCase):

    def test_threat_router_decision(self):
        """Test router directs to Strategist when threat detected, and monitor when safe."""
        state_with_threat = {"threat_detected": True}
        self.assertEqual(threat_router(state_with_threat), "strategist")

        state_without_threat = {"threat_detected": False}
        self.assertEqual(threat_router(state_without_threat), "monitor")

    def test_run_sentinel_mock(self):
        """Test sentinel node populates threat and location."""
        state = {"location": "Jalandhar"}
        updated = run_sentinel(state)
        self.assertTrue(updated.get("threat_detected"))
        self.assertEqual(updated.get("threat", {}).get("location"), "Jalandhar")
        self.assertIn("rainfall_mm", updated.get("threat", {}))

    def test_run_strategist_with_real_agent(self):
        """Test strategist node correctly processes threat and loads farmers from FarmerDB."""
        state = {
            "location": "Jalandhar",
            "threat_detected": True,
            "threat": {
                "event_id": "EVT-TEST-001",
                "event_type": "heavy_rain",
                "severity": "high",
                "probability": 0.85,
                "location": "Jalandhar",
                "rainfall_mm": 60.0,
                "wind_speed_kmh": 20.0
            }
        }
        updated = run_strategist(state)
        self.assertIn("risk_level", updated)
        self.assertIn(updated["risk_level"], ["high", "critical"])
        self.assertTrue(len(updated.get("affected_farmers", [])) > 0)
        self.assertTrue(len(updated.get("recommended_actions", [])) > 0)
        self.assertTrue(updated.get("alert_required"))
        self.assertIn("radio_gpt_payload", updated)
        self.assertIn("dashboard_payload", updated)

    def test_end_to_end_orchestrator_graph(self):
        """Test the compiled LangGraph execution from START through Sentinel and Strategist to END."""
        graph = build_graph()
        initial_state = {"location": "Jalandhar"}

        result = graph.invoke(initial_state)

        self.assertEqual(result.get("location"), "Jalandhar")
        self.assertTrue(result.get("threat_detected"))
        self.assertIsNotNone(result.get("threat"))
        self.assertIn(result.get("risk_level"), ["high", "critical"])
        self.assertTrue(result.get("alert_required"))

        # Verify Jalandhar farmers evaluated
        farmers = result.get("affected_farmers", [])
        self.assertGreaterEqual(len(farmers), 1)
        farmer_names = [f["name"] for f in farmers]
        self.assertIn("Gurpreet Singh", farmer_names)

        # Verify multilingual voice scripts generated for Radio-GPT
        radio_payload = result.get("radio_gpt_payload", [])
        self.assertGreaterEqual(len(radio_payload), 1)
        first_scripts = radio_payload[0].get("multilingual_scripts", {})
        self.assertIn("en", first_scripts)
        self.assertIn("hi", first_scripts)
        self.assertIn("pa", first_scripts)


if __name__ == "__main__":
    unittest.main()
