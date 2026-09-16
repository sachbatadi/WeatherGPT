"""
Focused Unit Tests for WeatherGPT SQLite Persistence Layer (tests/test_database.py).

All tests:
- Use temporary SQLite database instances (Condition 3: isolated from real database).
- Use temporary test fixtures only (Condition 1: no production overwriting).
- Verify tables, CRUD operations, location queries, plan updates, threat logs, and alert logs.
"""

import os
import copy
import shutil
import tempfile
import unittest
import sqlite3

from database.connection import (
    init_db,
    get_connection,
    log_threat_event,
    log_alert,
    get_threat_event_logs,
    get_alert_logs,
)
from database.models import FarmerModel, FarmActivityModel, ThreatEventLogModel, AlertLogModel
from tools.farmer.farmer_db import FarmerDB


# Temporary test data fixtures (isolated from production)
TEMP_TEST_FARMER_A = {
    "farmer_id": "TEST-F001",
    "name": "Simranjeet Singh",
    "phone": "+91-9999900001",
    "language": "pa",
    "location": "Jalandhar West",
    "district": "Jalandhar",
    "state": "Punjab",
    "land_size_acres": 4.5,
    "crop": "Wheat",
    "crop_stage": "Flowering",
    "soil_type": "Loamy",
    "irrigation_method": "Flood",
    "current_plan": [
        {
            "activity_id": "TEST-ACT-001",
            "activity_type": "irrigation",
            "scheduled_date": "2026-09-20",
            "details": {"target_depth_cm": 5, "duration_hours": 3},
            "status": "scheduled",
            "calendar_event_id": "cal_evt_001"
        },
        {
            "activity_id": "TEST-ACT-002",
            "activity_type": "fertilization",
            "scheduled_date": "2026-09-21",
            "details": {"fertilizer": "Urea", "quantity_kg": 40},
            "status": "scheduled"
        }
    ]
}

TEMP_TEST_FARMER_B = {
    "farmer_id": "TEST-F002",
    "name": "Amanpreet Kaur",
    "phone": "+91-9999900002",
    "language": "hi",
    "location": "Bathinda Central",
    "district": "Bathinda",
    "state": "Punjab",
    "land_size_acres": 7.0,
    "crop": "Cotton",
    "crop_stage": "Vegetative",
    "soil_type": "Sandy",
    "irrigation_method": "Drip",
    "current_plan": [
        {
            "activity_id": "TEST-ACT-003",
            "activity_type": "spraying",
            "scheduled_date": "2026-09-20",
            "details": {"chemical": "Neem Oil"},
            "status": "scheduled"
        }
    ]
}


class TestSQLiteDatabaseLayer(unittest.TestCase):
    """Test suite for SQLite persistence layer, FarmerDB repository, and audit logs."""

    def setUp(self):
        """Create a dedicated temporary SQLite database file for each test."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_file = os.path.join(self.temp_dir, "test_weathergpt.db")
        self.db_url = f"sqlite:///{self.db_file}"
        self.farmer_db = FarmerDB(db_url=self.db_url, auto_seed=False)

    def tearDown(self):
        """Clean up the temporary directory and test database file."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_schema_tables_created(self):
        """Verify that all 4 required tables and indices are created in SQLite."""
        conn = get_connection(self.db_url)
        try:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"
            )
            tables = [row[0] for row in cursor.fetchall()]
            self.assertIn("farmers", tables)
            self.assertIn("farm_activities", tables)
            self.assertIn("threat_event_logs", tables)
            self.assertIn("alert_logs", tables)
        finally:
            conn.close()

    def test_add_and_get_farmer_by_id(self):
        """Verify inserting a temporary farmer profile and fetching it back with plan."""
        farmer_id = self.farmer_db.add_farmer(TEMP_TEST_FARMER_A)
        self.assertEqual(farmer_id, "TEST-F001")

        farmer = self.farmer_db.get_farmer_by_id("TEST-F001")
        self.assertIsNotNone(farmer)
        self.assertEqual(farmer["name"], "Simranjeet Singh")
        self.assertEqual(farmer["crop"], "Wheat")
        self.assertEqual(farmer["soil_type"], "Loamy")
        self.assertEqual(len(farmer["current_plan"]), 2)

        # Check nested activity details
        first_act = farmer["current_plan"][0]
        self.assertEqual(first_act["activity_id"], "TEST-ACT-001")
        self.assertEqual(first_act["activity_type"], "irrigation")
        self.assertEqual(first_act["details"]["target_depth_cm"], 5)

    def test_get_farmers_by_location(self):
        """Verify case-insensitive location and district querying."""
        self.farmer_db.add_farmer(TEMP_TEST_FARMER_A)  # Jalandhar
        self.farmer_db.add_farmer(TEMP_TEST_FARMER_B)  # Bathinda

        # Query by district "Jalandhar" (case-insensitive)
        jalandhar_farmers = self.farmer_db.get_farmers_by_location("jalandhar")
        self.assertEqual(len(jalandhar_farmers), 1)
        self.assertEqual(jalandhar_farmers[0]["farmer_id"], "TEST-F001")

        # Query by district "Bathinda" (uppercase)
        bathinda_farmers = self.farmer_db.get_farmers_by_location("BATHINDA")
        self.assertEqual(len(bathinda_farmers), 1)
        self.assertEqual(bathinda_farmers[0]["farmer_id"], "TEST-F002")

        # Query by shared state "Punjab"
        punjab_farmers = self.farmer_db.get_farmers_by_location("Punjab")
        self.assertEqual(len(punjab_farmers), 2)

    def test_update_farmer_plan(self):
        """Verify updating scheduled farm activities (e.g. postponements) in SQLite."""
        self.farmer_db.add_farmer(TEMP_TEST_FARMER_A)

        updated_plan = [
            {
                "activity_id": "TEST-ACT-001",
                "activity_type": "irrigation",
                "scheduled_date": "2026-09-25",
                "details": {"duration_hours": 3, "rescheduled_reason": "60mm heavy rain"},
                "status": "postponed"
            }
        ]

        success = self.farmer_db.update_farmer_plan("TEST-F001", updated_plan)
        self.assertTrue(success)

        # Verify updated plan persists in database
        farmer = self.farmer_db.get_farmer_by_id("TEST-F001")
        self.assertEqual(len(farmer["current_plan"]), 1)
        updated_act = farmer["current_plan"][0]
        self.assertEqual(updated_act["status"], "postponed")
        self.assertEqual(updated_act["scheduled_date"], "2026-09-25")
        self.assertEqual(updated_act["details"]["rescheduled_reason"], "60mm heavy rain")

    def test_update_nonexistent_farmer_plan(self):
        """Verify update_farmer_plan returns False for non-existent farmer ID."""
        success = self.farmer_db.update_farmer_plan("NONEXISTENT", [])
        self.assertFalse(success)

    def test_threat_event_audit_logging(self):
        """Verify writing and reading ThreatEvent audit logs."""
        threat_payload = {
            "event_id": "TEST-EVT-001",
            "event_type": "heavy_rain",
            "severity": "critical",
            "probability": 0.90,
            "confidence": "high",
            "confidence_reason": "3 models in consensus",
            "location": "Jalandhar",
            "rainfall_mm": 55.0,
            "wind_speed_kmh": 28.0,
            "temp_c": 24.5
        }

        event_id = log_threat_event(threat_payload, db_url=self.db_url)
        self.assertEqual(event_id, "TEST-EVT-001")

        logs = get_threat_event_logs(limit=10, db_url=self.db_url)
        self.assertEqual(len(logs), 1)
        entry = logs[0]
        self.assertEqual(entry["event_id"], "TEST-EVT-001")
        self.assertEqual(entry["event_type"], "heavy_rain")
        self.assertEqual(entry["severity"], "critical")
        self.assertEqual(entry["rainfall_mm"], 55.0)

    def test_alert_audit_logging(self):
        """Verify writing and reading Alert audit logs."""
        alert_payload = {
            "dispatch_id": "TEST-DISP-001",
            "threat_event_id": "TEST-EVT-001",
            "farmer_id": "TEST-F001",
            "farmer_name": "Simranjeet Singh",
            "channel": "sms",
            "language": "pa",
            "urgency": "high",
            "message": "Heavy rain alert: postpone irrigation.",
            "status": "dispatched"
        }

        disp_id = log_alert(alert_payload, db_url=self.db_url)
        self.assertEqual(disp_id, "TEST-DISP-001")

        logs = get_alert_logs(farmer_id="TEST-F001", limit=10, db_url=self.db_url)
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0]["dispatch_id"], "TEST-DISP-001")
        self.assertEqual(logs[0]["farmer_name"], "Simranjeet Singh")
        self.assertEqual(logs[0]["channel"], "sms")

    def test_farmers_property_backward_compatibility(self):
        """Verify _farmers dictionary property getter and setter compatibility."""
        self.farmer_db.add_farmer(TEMP_TEST_FARMER_A)

        # Test getter
        dict_view = self.farmer_db._farmers
        self.assertIn("TEST-F001", dict_view)
        self.assertEqual(dict_view["TEST-F001"]["name"], "Simranjeet Singh")

        # Test setter (as used by test_integration.py setUp)
        new_test_data = {"TEST-F002": copy.deepcopy(TEMP_TEST_FARMER_B)}
        self.farmer_db._farmers = new_test_data

        updated_view = self.farmer_db._farmers
        self.assertNotIn("TEST-F001", updated_view)
        self.assertIn("TEST-F002", updated_view)
        self.assertEqual(updated_view["TEST-F002"]["name"], "Amanpreet Kaur")


if __name__ == "__main__":
    unittest.main()
