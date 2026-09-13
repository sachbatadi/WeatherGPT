"""
Farmer Database Tool (tools/farmer/farmer_db.py).

Provides access to farmer profiles, active farm plans, and field characteristics.
Serves as the data store for Member 3 (Strategist) and Member 6 (Database/API).
"""

from typing import List, Dict, Any, Optional
import copy


# Seed dataset of realistic farming profiles across Punjab & Haryana
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
    In-memory / persistent Farmer Database repository.
    """

    def __init__(self, initial_data: Optional[List[Dict[str, Any]]] = None):
        source = initial_data or INITIAL_FARMERS_DATA
        self._farmers: Dict[str, Dict[str, Any]] = {
            f["farmer_id"]: copy.deepcopy(f) for f in source
        }

    def get_all_farmers(self) -> List[Dict[str, Any]]:
        """Return deep copy of all registered farmers."""
        return [copy.deepcopy(f) for f in self._farmers.values()]

    def get_farmer_by_id(self, farmer_id: str) -> Optional[Dict[str, Any]]:
        """Fetch farmer profile by unique farmer ID."""
        f = self._farmers.get(farmer_id)
        return copy.deepcopy(f) if f else None

    def get_farmers_by_location(self, location: str) -> List[Dict[str, Any]]:
        """
        Fetch all farmers in a given location/district (case-insensitive substring match).
        """
        loc_clean = location.strip().lower()
        matches: List[Dict[str, Any]] = []
        for f in self._farmers.values():
            if (
                loc_clean in f.get("location", "").lower()
                or loc_clean in f.get("district", "").lower()
                or loc_clean in f.get("state", "").lower()
            ):
                matches.append(copy.deepcopy(f))
        return matches

    def update_farmer_plan(self, farmer_id: str, updated_plan: List[Dict[str, Any]]) -> bool:
        """Update the active activity plan for a specific farmer."""
        if farmer_id not in self._farmers:
            return False
        self._farmers[farmer_id]["current_plan"] = copy.deepcopy(updated_plan)
        return True

    def add_farmer(self, farmer_data: Dict[str, Any]) -> str:
        """Register a new farmer profile."""
        f_id = farmer_data.get("farmer_id", f"F{len(self._farmers) + 1:03d}")
        data = copy.deepcopy(farmer_data)
        data["farmer_id"] = f_id
        self._farmers[f_id] = data
        return f_id


# Default singleton instance for easy import
default_farmer_db = FarmerDB()
