"""
Database Models for WeatherGPT (database/models.py).

Defines structured schemas for:
1. Farmer (Farmer profiles, agronomic attributes, soil, crop)
2. FarmActivity (Scheduled calendar activities: irrigation, spraying, etc.)
3. ThreatEventLog (Historical audit trail of detected weather threats)
4. AlertLog (Historical record of dispatched or queued farmer notifications)

Supports both SQLAlchemy 2.0 ORM and standard library SQLite mapping.
"""

import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

# ---------------------------------------------------------------------------
# SQLAlchemy 2.0 Models (if SQLAlchemy is installed in the environment)
# ---------------------------------------------------------------------------
try:
    from sqlalchemy import Column, String, Float, Integer, DateTime, Text, ForeignKey, JSON
    from sqlalchemy.orm import declarative_base, relationship
    HAS_SQLALCHEMY = True
    Base = declarative_base()
except ImportError:
    HAS_SQLALCHEMY = False
    Base = object  # Fallback base class


if HAS_SQLALCHEMY:
    class SQLAlchemyFarmer(Base):
        __tablename__ = "farmers"

        farmer_id = Column(String(64), primary_key=True, index=True)
        name = Column(String(128), nullable=False)
        phone = Column(String(32), nullable=True)
        language = Column(String(16), default="en", nullable=False)
        location = Column(String(128), nullable=False, index=True)
        district = Column(String(128), nullable=True)
        state = Column(String(128), nullable=True)
        land_size_acres = Column(Float, nullable=True)
        crop = Column(String(64), nullable=False)
        crop_stage = Column(String(64), nullable=False)
        soil_type = Column(String(64), default="loamy", nullable=False)
        irrigation_method = Column(String(64), default="flood", nullable=False)
        created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
        updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

        activities = relationship("SQLAlchemyFarmActivity", back_populates="farmer", cascade="all, delete-orphan")


    class SQLAlchemyFarmActivity(Base):
        __tablename__ = "farm_activities"

        activity_id = Column(String(64), primary_key=True, index=True)
        farmer_id = Column(String(64), ForeignKey("farmers.farmer_id", ondelete="CASCADE"), nullable=False, index=True)
        activity_type = Column(String(64), nullable=False)
        scheduled_date = Column(String(32), nullable=False)
        status = Column(String(32), default="scheduled", nullable=False)
        calendar_event_id = Column(String(128), nullable=True)
        details = Column(JSON, default=dict)

        farmer = relationship("SQLAlchemyFarmer", back_populates="activities")


    class SQLAlchemyThreatEventLog(Base):
        __tablename__ = "threat_event_logs"

        event_id = Column(String(64), primary_key=True, index=True)
        event_type = Column(String(64), nullable=False)
        severity = Column(String(32), nullable=False)
        probability = Column(Float, nullable=False)
        confidence = Column(String(32), nullable=False)
        confidence_reason = Column(Text, nullable=True)
        location = Column(String(128), nullable=False)
        rainfall_mm = Column(Float, nullable=True)
        wind_speed_kmh = Column(Float, nullable=True)
        temp_c = Column(Float, nullable=True)
        detected_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
        raw_payload = Column(JSON, default=dict)


    class SQLAlchemyAlertLog(Base):
        __tablename__ = "alert_logs"

        dispatch_id = Column(String(64), primary_key=True, index=True)
        threat_event_id = Column(String(64), nullable=True, index=True)
        farmer_id = Column(String(64), nullable=False, index=True)
        farmer_name = Column(String(128), nullable=False)
        channel = Column(String(32), nullable=False)
        language = Column(String(16), default="en", nullable=False)
        urgency = Column(String(32), default="high", nullable=False)
        message = Column(Text, nullable=False)
        status = Column(String(32), default="queued", nullable=False)
        dispatched_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


# ---------------------------------------------------------------------------
# Data Models / Representation Classes (Framework-Agnostic)
# ---------------------------------------------------------------------------

class FarmActivityModel:
    """Individual farm activity tied to a farmer's calendar."""

    def __init__(
        self,
        activity_id: str,
        activity_type: str,
        scheduled_date: str,
        status: str = "scheduled",
        details: Optional[Dict[str, Any]] = None,
        calendar_event_id: Optional[str] = None,
        farmer_id: Optional[str] = None
    ):
        self.activity_id = activity_id
        self.activity_type = activity_type
        self.scheduled_date = scheduled_date
        self.status = status
        self.details = details or {}
        self.calendar_event_id = calendar_event_id
        self.farmer_id = farmer_id

    def to_dict(self) -> Dict[str, Any]:
        return {
            "activity_id": self.activity_id,
            "activity_type": self.activity_type,
            "scheduled_date": self.scheduled_date,
            "details": dict(self.details),
            "status": self.status,
            "calendar_event_id": self.calendar_event_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any], farmer_id: Optional[str] = None) -> "FarmActivityModel":
        raw_details = data.get("details", {})
        if isinstance(raw_details, str):
            try:
                raw_details = json.loads(raw_details)
            except Exception:
                raw_details = {}
        return cls(
            activity_id=data["activity_id"],
            activity_type=data.get("activity_type", "other"),
            scheduled_date=data.get("scheduled_date", ""),
            status=data.get("status", "scheduled"),
            details=raw_details,
            calendar_event_id=data.get("calendar_event_id"),
            farmer_id=farmer_id or data.get("farmer_id")
        )


class FarmerModel:
    """Farmer Profile domain model holding field and crop characteristics."""

    def __init__(
        self,
        farmer_id: str,
        name: str,
        crop: str,
        crop_stage: str,
        location: str,
        phone: Optional[str] = None,
        language: str = "en",
        district: Optional[str] = None,
        state: Optional[str] = None,
        land_size_acres: Optional[float] = None,
        soil_type: str = "loamy",
        irrigation_method: str = "flood",
        current_plan: Optional[List[Dict[str, Any]]] = None
    ):
        self.farmer_id = farmer_id
        self.name = name
        self.crop = crop
        self.crop_stage = crop_stage
        self.location = location
        self.phone = phone
        self.language = language
        self.district = district or location
        self.state = state
        self.land_size_acres = land_size_acres
        self.soil_type = soil_type
        self.irrigation_method = irrigation_method
        self.current_plan = current_plan or []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "farmer_id": self.farmer_id,
            "name": self.name,
            "phone": self.phone,
            "language": self.language,
            "location": self.location,
            "district": self.district,
            "state": self.state,
            "land_size_acres": self.land_size_acres,
            "crop": self.crop,
            "crop_stage": self.crop_stage,
            "soil_type": self.soil_type,
            "irrigation_method": self.irrigation_method,
            "current_plan": [dict(p) for p in self.current_plan]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FarmerModel":
        plan_raw = data.get("current_plan", [])
        parsed_plan = []
        for p in plan_raw:
            if isinstance(p, dict):
                parsed_plan.append(FarmActivityModel.from_dict(p, farmer_id=data["farmer_id"]).to_dict())
            elif hasattr(p, "to_dict"):
                parsed_plan.append(p.to_dict())
            elif hasattr(p, "model_dump"):
                parsed_plan.append(p.model_dump())

        return cls(
            farmer_id=data["farmer_id"],
            name=data["name"],
            phone=data.get("phone"),
            language=data.get("language", "en"),
            location=data["location"],
            district=data.get("district"),
            state=data.get("state"),
            land_size_acres=data.get("land_size_acres"),
            crop=data["crop"],
            crop_stage=data["crop_stage"],
            soil_type=data.get("soil_type", "loamy"),
            irrigation_method=data.get("irrigation_method", "flood"),
            current_plan=parsed_plan
        )


class ThreatEventLogModel:
    """Historical audit record for detected weather threat events."""

    def __init__(
        self,
        event_id: str,
        event_type: str,
        severity: str,
        probability: float,
        confidence: str,
        location: str,
        confidence_reason: Optional[str] = None,
        rainfall_mm: Optional[float] = None,
        wind_speed_kmh: Optional[float] = None,
        temp_c: Optional[float] = None,
        detected_at: Optional[str] = None,
        raw_payload: Optional[Dict[str, Any]] = None
    ):
        self.event_id = event_id
        self.event_type = event_type
        self.severity = severity
        self.probability = probability
        self.confidence = confidence
        self.confidence_reason = confidence_reason
        self.location = location
        self.rainfall_mm = rainfall_mm
        self.wind_speed_kmh = wind_speed_kmh
        self.temp_c = temp_c
        self.detected_at = detected_at or datetime.now(timezone.utc).isoformat()
        self.raw_payload = raw_payload or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "severity": self.severity,
            "probability": self.probability,
            "confidence": self.confidence,
            "confidence_reason": self.confidence_reason,
            "location": self.location,
            "rainfall_mm": self.rainfall_mm,
            "wind_speed_kmh": self.wind_speed_kmh,
            "temp_c": self.temp_c,
            "detected_at": self.detected_at,
            "raw_payload": dict(self.raw_payload)
        }


class AlertLogModel:
    """Historical log record for queued or dispatched farmer alerts."""

    def __init__(
        self,
        dispatch_id: str,
        farmer_id: str,
        farmer_name: str,
        channel: str,
        message: str,
        threat_event_id: Optional[str] = None,
        language: str = "en",
        urgency: str = "high",
        status: str = "queued",
        dispatched_at: Optional[str] = None
    ):
        self.dispatch_id = dispatch_id
        self.threat_event_id = threat_event_id
        self.farmer_id = farmer_id
        self.farmer_name = farmer_name
        self.channel = channel
        self.language = language
        self.urgency = urgency
        self.message = message
        self.status = status
        self.dispatched_at = dispatched_at or datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dispatch_id": self.dispatch_id,
            "threat_event_id": self.threat_event_id,
            "farmer_id": self.farmer_id,
            "farmer_name": self.farmer_name,
            "channel": self.channel,
            "language": self.language,
            "urgency": self.urgency,
            "message": self.message,
            "status": self.status,
            "dispatched_at": self.dispatched_at
        }


# ---------------------------------------------------------------------------
# SQLite DDL Schema Statements
# ---------------------------------------------------------------------------

CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS farmers (
    farmer_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    phone TEXT,
    language TEXT NOT NULL DEFAULT 'en',
    location TEXT NOT NULL,
    district TEXT,
    state TEXT,
    land_size_acres REAL,
    crop TEXT NOT NULL,
    crop_stage TEXT NOT NULL,
    soil_type TEXT NOT NULL DEFAULT 'loamy',
    irrigation_method TEXT NOT NULL DEFAULT 'flood',
    created_at TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS farm_activities (
    activity_id TEXT PRIMARY KEY,
    farmer_id TEXT NOT NULL,
    activity_type TEXT NOT NULL,
    scheduled_date TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'scheduled',
    calendar_event_id TEXT,
    details TEXT,
    FOREIGN KEY(farmer_id) REFERENCES farmers(farmer_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS threat_event_logs (
    event_id TEXT PRIMARY KEY,
    event_type TEXT NOT NULL,
    severity TEXT NOT NULL,
    probability REAL NOT NULL,
    confidence TEXT NOT NULL,
    confidence_reason TEXT,
    location TEXT NOT NULL,
    rainfall_mm REAL,
    wind_speed_kmh REAL,
    temp_c REAL,
    detected_at TEXT,
    raw_payload TEXT
);

CREATE TABLE IF NOT EXISTS alert_logs (
    dispatch_id TEXT PRIMARY KEY,
    threat_event_id TEXT,
    farmer_id TEXT NOT NULL,
    farmer_name TEXT NOT NULL,
    channel TEXT NOT NULL,
    language TEXT NOT NULL DEFAULT 'en',
    urgency TEXT NOT NULL DEFAULT 'high',
    message TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'queued',
    dispatched_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_farmers_location ON farmers(location);
CREATE INDEX IF NOT EXISTS idx_activities_farmer_id ON farm_activities(farmer_id);
CREATE INDEX IF NOT EXISTS idx_threat_logs_location ON threat_event_logs(location);
CREATE INDEX IF NOT EXISTS idx_alert_logs_farmer ON alert_logs(farmer_id);
"""
