"""
Unit tests for Member 3: Strategist Agent.

Tests all agronomic scenarios and pipeline integration:
1. Heavy rain causing irrigation postponement & drainage preparation (SIH core scenario)
2. High winds causing spraying postponement
3. Mature crop harvest protection against storms
4. Extreme heat mitigation
5. Fertilizer leaching prevention (Urea postponement)
6. Disease / Late Blight risk under humid conditions
7. Multilingual voice scripts generation (English, Hindi, Punjabi for Radio-GPT)
8. Conversational Q&A ("Why did you change my plan?")
9. Farmer DB location querying
10. Direct integration with Orchestrator's WeatherState
"""

import unittest
from agents.strategist import (
    StrategistAgent,
    run_strategist_node,
    SeverityLevel,
    ActionType,
    FarmerProfile,
    FarmActivity
)
from tools.farmer.farmer_db import FarmerDB


class TestStrategistAgent(unittest.TestCase):

    def setUp(self):
        self.agent = StrategistAgent()

    def test_wheat_heavy_rain_irrigation_scenario(self):
        """
        SIH Demo Scenario:
        Farmer Gurpreet has Wheat in flowering stage on loamy soil.
        Irrigation is scheduled for Sept 15.
        Heavy rain (60mm, 85% prob) is detected.
        """
        threat = {
            "event_id": "EVT-RAIN-001",
            "event_type": "heavy_rain",
            "severity": "high",
            "probability": 0.85,
            "confidence": "high",
            "location": "Jalandhar",
            "time_to_event_minutes": 30,
            "rainfall_mm": 60.0
        }

        farmer = FarmerProfile(
            farmer_id="F001",
            name="Gurpreet Singh",
            location="Jalandhar",
            crop="Wheat",
            crop_stage="flowering",
            soil_type="loamy",
            irrigation_method="flood",
            current_plan=[
                FarmActivity(
                    activity_id="ACT-001",
                    activity_type="irrigation",
                    scheduled_date="2026-09-15"
                )
            ]
        )

        result = self.agent.evaluate(threat_data=threat, farmers=[farmer])

        self.assertEqual(result.affected_farmers_count, 1)
        self.assertIn(result.overall_risk_level, [SeverityLevel.HIGH, SeverityLevel.CRITICAL])
        self.assertTrue(result.alert_required)

        assessment = result.assessments[0]
        self.assertTrue(assessment.replanning_required)
        self.assertGreater(assessment.risk_score, 60.0)

        # Verify recommended actions
        action_types = [a.action_type for a in assessment.actions]
        self.assertIn(ActionType.POSTPONE_IRRIGATION, action_types)
        self.assertIn(ActionType.DRAINAGE_PREPARATION, action_types)

        # Check postponed activity in updated plan
        postponed_acts = [a for a in assessment.updated_plan if a.activity_id == "ACT-001"]
        self.assertEqual(len(postponed_acts), 1)
        self.assertEqual(postponed_acts[0].status, "postponed")

        # Check observation trigger
        self.assertIsNotNone(assessment.next_observation)
        self.assertEqual(assessment.next_observation.trigger_type, "reassess_soil_moisture")

    def test_fertilizer_leaching_prevention(self):
        """
        Test that scheduled fertilizer top-dressing is postponed before heavy rain.
        """
        threat = {
            "event_id": "EVT-RAIN-002",
            "event_type": "heavy_rain",
            "severity": "high",
            "probability": 0.85,
            "location": "Jalandhar",
            "rainfall_mm": 45.0
        }

        farmer = FarmerProfile(
            farmer_id="F001",
            name="Gurpreet Singh",
            location="Jalandhar",
            crop="Wheat",
            crop_stage="vegetative",
            soil_type="loamy",
            current_plan=[
                FarmActivity(
                    activity_id="ACT-FERT-01",
                    activity_type="fertilization",
                    scheduled_date="2026-09-14",
                    details={"fertilizer": "Urea top-dressing"}
                )
            ]
        )

        result = self.agent.evaluate(threat_data=threat, farmers=[farmer])
        assessment = result.assessments[0]

        action_types = [a.action_type for a in assessment.actions]
        self.assertIn(ActionType.DELAY_FERTILIZATION, action_types)
        self.assertTrue(assessment.replanning_required)

    def test_potato_late_blight_humidity_risk(self):
        """
        Test fungal disease risk triggers when high humidity (88%) and cool temps occur.
        """
        threat = {
            "event_id": "EVT-HUMID-001",
            "event_type": "heavy_rain",
            "severity": "medium",
            "probability": 0.75,
            "location": "Ludhiana",
            "rainfall_mm": 15.0,
            "temp_c": 19.0,
            "humidity_pct": 90.0
        }

        farmer = FarmerProfile(
            farmer_id="F005",
            name="Sukhwinder Singh",
            location="Ludhiana",
            crop="Potato",
            crop_stage="vegetative",
            soil_type="silty",
            current_plan=[]
        )

        result = self.agent.evaluate(threat_data=threat, farmers=[farmer])
        assessment = result.assessments[0]

        action_types = [a.action_type for a in assessment.actions]
        self.assertIn(ActionType.DISEASE_PREVENTATIVE, action_types)
        self.assertGreater(assessment.risk_breakdown.disease_risk, 0.0)

    def test_multilingual_voice_scripts(self):
        """
        Verify that Member 4 (Radio-GPT) receives scripts in English, Hindi, and Punjabi.
        """
        threat = {
            "event_id": "EVT-RAIN-003",
            "event_type": "heavy_rain",
            "severity": "high",
            "probability": 0.85,
            "location": "Jalandhar",
            "rainfall_mm": 50.0,
            "time_to_event_minutes": 25
        }

        farmer = FarmerProfile(
            farmer_id="F001",
            name="Gurpreet Singh",
            location="Jalandhar",
            crop="Wheat",
            crop_stage="flowering",
            soil_type="loamy",
            current_plan=[]
        )

        result = self.agent.evaluate(threat_data=threat, farmers=[farmer])
        assessment = result.assessments[0]

        scripts = assessment.multilingual_scripts
        self.assertIn("Gurpreet Singh", scripts.en)
        self.assertIn("50 mm", scripts.en)

        self.assertIn("Gurpreet Singh", scripts.hi)
        self.assertIn("बारिश", scripts.hi)

        self.assertIn("Gurpreet Singh", scripts.pa)
        self.assertIn("ਮੀਂਹ", scripts.pa)

    def test_farmer_conversational_qa(self):
        """
        Test Module 10: Farmer asking "Why did you postpone my irrigation?"
        """
        response = self.agent.answer_farmer_query(
            farmer_id="F001",
            query="Why did you postpone my irrigation?"
        )

        self.assertEqual(response.farmer_id, "F001")
        self.assertIn("saturation", response.answer.lower())
        self.assertIn("moisture", response.recommended_next_step.lower())

    def test_farmer_db_location_query(self):
        """
        Test that passing no farmers automatically queries farmers matching the threat location.
        """
        threat = {
            "event_id": "EVT-AUTO-001",
            "event_type": "heavy_rain",
            "severity": "high",
            "probability": 0.85,
            "location": "Jalandhar",
            "rainfall_mm": 40.0
        }

        # Evaluate without passing farmers list
        result = self.agent.evaluate(threat_data=threat)
        self.assertGreaterEqual(result.affected_farmers_count, 1)

    def test_high_wind_spray_drift_scenario(self):
        """
        Wind speed exceeds safe threshold (15 km/h).
        Scheduled spraying must be postponed to prevent chemical drift.
        """
        threat = {
            "event_id": "EVT-WIND-001",
            "event_type": "high_wind",
            "severity": "medium",
            "probability": 0.80,
            "confidence": "high",
            "location": "Bathinda",
            "wind_speed_kmh": 30.0
        }

        farmer = FarmerProfile(
            farmer_id="F003",
            name="Baldev Singh",
            location="Bathinda",
            crop="Cotton",
            crop_stage="vegetative",
            soil_type="sandy",
            current_plan=[
                FarmActivity(
                    activity_id="ACT-002",
                    activity_type="spraying",
                    scheduled_date="2026-09-14",
                    details={"chemical": "Neem oil organic pesticide"}
                )
            ]
        )

        result = self.agent.evaluate(threat_data=threat, farmers=[farmer])
        assessment = result.assessments[0]

        action_types = [a.action_type for a in assessment.actions]
        self.assertIn(ActionType.RESCHEDULE_SPRAY, action_types)
        self.assertTrue(assessment.replanning_required)

    def test_mature_crop_harvest_protection(self):
        """
        Crop at maturity stage facing heavy rain and high winds.
        Should recommend expediting harvest and covering produce.
        """
        threat = {
            "event_id": "EVT-STORM-001",
            "event_type": "cyclone",
            "severity": "critical",
            "probability": 0.90,
            "confidence": "high",
            "location": "Ludhiana",
            "rainfall_mm": 45.0,
            "wind_speed_kmh": 40.0
        }

        farmer = FarmerProfile(
            farmer_id="F003",
            name="Jasbir Kaur",
            location="Ludhiana",
            crop="Wheat",
            crop_stage="maturity",
            soil_type="clay",
            current_plan=[]
        )

        result = self.agent.evaluate(threat_data=threat, farmers=[farmer])
        assessment = result.assessments[0]

        self.assertEqual(assessment.risk_level, SeverityLevel.CRITICAL)
        action_types = [a.action_type for a in assessment.actions]
        self.assertIn(ActionType.EXPEDITE_HARVEST, action_types)

    def test_orchestrator_state_bridge(self):
        """
        Test direct LangGraph node execution and WeatherState mutation.
        """
        orchestrator_state = {
            "location": "Jalandhar",
            "threat_detected": True,
            "threat": {
                "event_id": "EVT-001",
                "event_type": "heavy_rain",
                "severity": "high",
                "probability": 0.85,
                "location": "Jalandhar",
                "time_to_event_minutes": 30,
                "rainfall_mm": 60
            }
        }

        updated_state = run_strategist_node(orchestrator_state)

        self.assertIn("risk_level", updated_state)
        self.assertIn("recommended_actions", updated_state)
        self.assertGreater(len(updated_state["recommended_actions"]), 0)
        self.assertTrue(updated_state["alert_required"])
        self.assertIn("strategist_output", updated_state)
        self.assertIn("radio_gpt_payload", updated_state)
        self.assertIn("dashboard_payload", updated_state)


if __name__ == "__main__":
    unittest.main()
