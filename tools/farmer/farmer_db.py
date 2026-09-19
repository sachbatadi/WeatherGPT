"""
Farmer Database Tool (tools/farmer/farmer_db.py).

Provides access to farmer profiles, active farm plans, and field characteristics.
Implements persistent SQLite storage while preserving 100% backward-compatible
interfaces and dictionary schemas for Sentinel, Strategist, and Executor agents.
"""

import json
import copy
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from database.connection import get_connection, init_db, get_db_path, DEFAULT_DB_URL


# Seed dataset of realistic farming profiles across Punjab & Haryana (for testing and manual seeding)
INITIAL_FARMERS_DATA: List[Dict[str, Any]] = [
    {
        "farmer_id": "F001",
        "name": "Gurpreet Singh",
        "phone": "+91-9876543210",
        "language": "pa",
        "location": "Jalandhar",
        "district": "Jalandhar",
        "state": "Punjab",
        "land_size_acres": 5.0,
        "crop": "Wheat",
        "crop_stage": "Flowering",
        "soil_type": "Loamy",
        "irrigation_method": "Flood",
        "current_plan": [
            {
                "activity_id": "ACT-001",
                "activity_type": "irrigation",
                "scheduled_date": "2026-09-15",
                "details": {"duration_hours": 4, "target_depth_cm": 5},
                "status": "scheduled"
            },
            {
                "activity_id": "ACT-002",
                "activity_type": "fertilization",
                "scheduled_date": "2026-09-16",
                "details": {"fertilizer": "Urea top-dressing", "quantity_kg": 50},
                "status": "scheduled"
            }
        ]
    },
    {
        "farmer_id": "F002",
        "name": "Harinder Kaur",
        "phone": "+91-9876543211",
        "language": "hi",
        "location": "Jalandhar",
        "district": "Jalandhar",
        "state": "Punjab",
        "land_size_acres": 3.5,
        "crop": "Wheat",
        "crop_stage": "Flowering",
        "soil_type": "Clay",
        "irrigation_method": "Sprinkler",
        "current_plan": [
            {
                "activity_id": "ACT-003",
                "activity_type": "spraying",
                "scheduled_date": "2026-09-14",
                "details": {"chemical": "Tebuconazole fungicide", "target_pest": "Yellow Rust"},
                "status": "scheduled"
            }
        ]
    },
    {
        "farmer_id": "F003",
        "name": "Baldev Singh",
        "phone": "+91-9876543212",
        "language": "pa",
        "location": "Bathinda",
        "district": "Bathinda",
        "state": "Punjab",
        "land_size_acres": 8.0,
        "crop": "Cotton",
        "crop_stage": "Vegetative",
        "soil_type": "Sandy",
        "irrigation_method": "Drip",
        "current_plan": [
            {
                "activity_id": "ACT-004",
                "activity_type": "spraying",
                "scheduled_date": "2026-09-14",
                "details": {"chemical": "Neem oil organic pesticide", "target_pest": "Whitefly"},
                "status": "scheduled"
            }
        ]
    },
    {
        "farmer_id": "F004",
        "name": "Rajesh Kumar",
        "phone": "+91-9876543213",
        "language": "hi",
        "location": "Amritsar",
        "district": "Amritsar",
        "state": "Punjab",
        "land_size_acres": 2.0,
        "crop": "Tomato",
        "crop_stage": "Flowering",
        "soil_type": "Loamy",
        "irrigation_method": "Drip",
        "current_plan": [
            {
                "activity_id": "ACT-005",
                "activity_type": "harvesting",
                "scheduled_date": "2026-09-16",
                "details": {"harvest_batch": 1},
                "status": "scheduled"
            }
        ]
    },
    {
        "farmer_id": "F005",
        "name": "Sukhwinder Singh",
        "phone": "+91-9876543214",
        "language": "pa",
        "location": "Ludhiana",
        "district": "Ludhiana",
        "state": "Punjab",
        "land_size_acres": 6.0,
        "crop": "Potato",
        "crop_stage": "Vegetative",
        "soil_type": "Silty",
        "irrigation_method": "Furrow",
        "current_plan": [
            {
                "activity_id": "ACT-006",
                "activity_type": "irrigation",
                "scheduled_date": "2026-09-15",
                "details": {"target_depth_cm": 4},
                "status": "scheduled"
            }
        ]
    }
]


class FarmerDB:
    """
    Persistent SQLite repository for farmer profiles and farm activities.
    Supports in-memory test databases and local file databases.
    """

    def __init__(
        self,
        db_url: Optional[str] = None,
        initial_data: Optional[List[Dict[str, Any]]] = None,
        auto_seed: Optional[bool] = None
    ):
        self.db_url = db_url or DEFAULT_DB_URL
        self._initialized = False
        if auto_seed is None:
            self.auto_seed = True if (db_url is None or initial_data is not None) else False
        else:
            self.auto_seed = auto_seed

        # When db_url is explicitly provided (e.g. tests), initialize immediately
        if db_url is not None:
            self._ensure_init()

        # In-memory test databases or explicit auto_seed
        if initial_data is not None:
            self._ensure_init()
            self._load_seed_data(initial_data, clear_existing=False)

    def _ensure_init(self) -> None:
        """Lazily ensure tables exist and seed initial farmers if auto_seed is enabled."""
        if not self._initialized:
            init_db(self.db_url)
            self._initialized = True
            if self.auto_seed:
                conn = get_connection(self.db_url)
                try:
                    cur = conn.execute("SELECT COUNT(*) FROM farmers;")
                    if cur.fetchone()[0] == 0:
                        self._load_seed_data(INITIAL_FARMERS_DATA, clear_existing=False)
                finally:
                    conn.close()

    def _get_conn(self):
        """Create and return a database connection, ensuring tables are initialized."""
        self._ensure_init()
        return get_connection(self.db_url)

    def _load_seed_data(self, data: List[Dict[str, Any]], clear_existing: bool = False) -> None:
        """Helper to seed farmer records and their farm activity plans."""
        conn = self._get_conn()
        try:
            if clear_existing:
                conn.execute("DELETE FROM farm_activities;")
                conn.execute("DELETE FROM farmers;")

            now_iso = datetime.now(timezone.utc).isoformat()
            for f in data:
                f_id = f["farmer_id"]
                conn.execute(
                    """
                    INSERT OR REPLACE INTO farmers (
                        farmer_id, name, phone, language, location,
                        district, state, land_size_acres, crop, crop_stage,
                        soil_type, irrigation_method, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        f_id,
                        f.get("name", "Farmer"),
                        f.get("phone"),
                        f.get("language", "en"),
                        f.get("location", "Jalandhar"),
                        f.get("district", f.get("location")),
                        f.get("state", "Punjab"),
                        f.get("land_size_acres"),
                        f.get("crop", "Wheat"),
                        f.get("crop_stage", "Vegetative"),
                        f.get("soil_type", "loamy"),
                        f.get("irrigation_method", "flood"),
                        now_iso,
                        now_iso
                    )
                )

                # Insert associated activities
                for act in f.get("current_plan", []):
                    act_id = act.get("activity_id")
                    if not act_id:
                        continue
                    details_str = json.dumps(act.get("details", {}))
                    conn.execute(
                        """
                        INSERT OR REPLACE INTO farm_activities (
                            activity_id, farmer_id, activity_type,
                            scheduled_date, status, calendar_event_id, details
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            act_id,
                            f_id,
                            act.get("activity_type", "irrigation"),
                            act.get("scheduled_date", now_iso[:10]),
                            act.get("status", "scheduled"),
                            act.get("calendar_event_id"),
                            details_str
                        )
                    )
            conn.commit()
        finally:
            conn.close()

    def _assemble_farmer_dict(self, conn, farmer_row) -> Dict[str, Any]:
        """Convert a database row and its activities into a complete farmer dictionary."""
        farmer = dict(farmer_row)
        farmer_id = farmer["farmer_id"]

        cur = conn.execute(
            "SELECT * FROM farm_activities WHERE farmer_id = ? ORDER BY scheduled_date ASC;",
            (farmer_id,)
        )
        plan = []
        for act_row in cur.fetchall():
            act = dict(act_row)
            raw_details = act.get("details")
            if isinstance(raw_details, str):
                try:
                    act["details"] = json.loads(raw_details)
                except Exception:
                    act["details"] = {}
            elif not raw_details:
                act["details"] = {}
            plan.append(act)

        farmer["current_plan"] = plan
        return farmer

    def get_all_farmers(self) -> List[Dict[str, Any]]:
        """Return deep copy of all registered farmers from SQLite."""
        conn = self._get_conn()
        try:
            cur = conn.execute("SELECT * FROM farmers ORDER BY farmer_id ASC;")
            rows = cur.fetchall()
            return [self._assemble_farmer_dict(conn, r) for r in rows]
        finally:
            conn.close()

    def get_farmer_by_id(self, farmer_id: str) -> Optional[Dict[str, Any]]:
        """Fetch farmer profile by unique farmer ID from SQLite."""
        conn = self._get_conn()
        try:
            cur = conn.execute("SELECT * FROM farmers WHERE farmer_id = ? LIMIT 1;", (farmer_id,))
            row = cur.fetchone()
            if not row:
                return None
            return self._assemble_farmer_dict(conn, row)
        finally:
            conn.close()

    def get_farmers_by_location(self, location: str) -> List[Dict[str, Any]]:
        """
        Fetch all farmers in a given location/district (case-insensitive substring match).
        """
        loc_clean = location.strip().lower()
        param = f"%{loc_clean}%"

        conn = self._get_conn()
        try:
            cur = conn.execute(
                """
                SELECT * FROM farmers
                WHERE LOWER(location) LIKE ?
                   OR LOWER(district) LIKE ?
                   OR LOWER(state) LIKE ?
                ORDER BY farmer_id ASC;
                """,
                (param, param, param)
            )
            rows = cur.fetchall()
            return [self._assemble_farmer_dict(conn, r) for r in rows]
        finally:
            conn.close()

    def update_farmer_plan(self, farmer_id: str, updated_plan: List[Dict[str, Any]]) -> bool:
        """Update the active activity plan for a specific farmer in SQLite."""
        conn = self._get_conn()
        try:
            cur = conn.execute("SELECT 1 FROM farmers WHERE farmer_id = ? LIMIT 1;", (farmer_id,))
            if not cur.fetchone():
                return False

            now_iso = datetime.now(timezone.utc).isoformat()
            # Delete existing activities for this farmer
            conn.execute("DELETE FROM farm_activities WHERE farmer_id = ?;", (farmer_id,))

            # Insert updated activities
            for act in updated_plan:
                act_id = act.get("activity_id")
                if not act_id:
                    continue
                details_str = json.dumps(act.get("details", {}))
                conn.execute(
                    """
                    INSERT INTO farm_activities (
                        activity_id, farmer_id, activity_type,
                        scheduled_date, status, calendar_event_id, details
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        act_id,
                        farmer_id,
                        act.get("activity_type", "irrigation"),
                        act.get("scheduled_date", now_iso[:10]),
                        act.get("status", "scheduled"),
                        act.get("calendar_event_id"),
                        details_str
                    )
                )

            # Mark farmer profile as updated
            conn.execute(
                "UPDATE farmers SET updated_at = ? WHERE farmer_id = ?;",
                (now_iso, farmer_id)
            )
            conn.commit()
            return True
        finally:
            conn.close()

    def add_farmer(self, farmer_data: Dict[str, Any]) -> str:
        """Register a new farmer profile in SQLite."""
        data = copy.deepcopy(farmer_data)
        f_id = data.get("farmer_id")

        conn = self._get_conn()
        try:
            if not f_id:
                cur = conn.execute("SELECT COUNT(*) FROM farmers;")
                count = cur.fetchone()[0]
                f_id = f"F{count + 1:03d}"
                data["farmer_id"] = f_id

            now_iso = datetime.now(timezone.utc).isoformat()
            conn.execute(
                """
                INSERT OR REPLACE INTO farmers (
                    farmer_id, name, phone, language, location,
                    district, state, land_size_acres, crop, crop_stage,
                    soil_type, irrigation_method, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    f_id,
                    data.get("name", "Farmer"),
                    data.get("phone"),
                    data.get("language", "en"),
                    data.get("location", "Jalandhar"),
                    data.get("district", data.get("location")),
                    data.get("state", "Punjab"),
                    data.get("land_size_acres"),
                    data.get("crop", "Wheat"),
                    data.get("crop_stage", "Vegetative"),
                    data.get("soil_type", "loamy"),
                    data.get("irrigation_method", "flood"),
                    now_iso,
                    now_iso
                )
            )

            for act in data.get("current_plan", []):
                act_id = act.get("activity_id")
                if not act_id:
                    continue
                details_str = json.dumps(act.get("details", {}))
                conn.execute(
                    """
                    INSERT OR REPLACE INTO farm_activities (
                        activity_id, farmer_id, activity_type,
                        scheduled_date, status, calendar_event_id, details
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        act_id,
                        f_id,
                        act.get("activity_type", "irrigation"),
                        act.get("scheduled_date", now_iso[:10]),
                        act.get("status", "scheduled"),
                        act.get("calendar_event_id"),
                        details_str
                    )
                )
            conn.commit()
            return f_id
        finally:
            conn.close()

    # -----------------------------------------------------------------------
    # Backward Compatibility Adapter for Existing Tests and Executors
    # -----------------------------------------------------------------------
    @property
    def _farmers(self) -> Dict[str, Dict[str, Any]]:
        """
        Dictionary mapping farmer_id to farmer dict.
        Allows legacy code (e.g. agents/executor/agent.py: _get_db_farmer)
        to read farmers seamlessly.
        """
        all_farmers = self.get_all_farmers()
        return {f["farmer_id"]: copy.deepcopy(f) for f in all_farmers}

    @_farmers.setter
    def _farmers(self, value: Dict[str, Dict[str, Any]]) -> None:
        """
        Setter allowing test suites (e.g. tests/test_integration.py setUp)
        to reset or replace test fixtures dynamically.
        """
        if isinstance(value, dict):
            self._load_seed_data(list(value.values()), clear_existing=True)
        elif isinstance(value, list):
            self._load_seed_data(value, clear_existing=True)


# Default singleton instance (uses configured SQLite database without auto-overwriting)
default_farmer_db = FarmerDB(auto_seed=False)
