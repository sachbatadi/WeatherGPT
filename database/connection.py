"""
SQLite Database Connection & Session Management (database/connection.py).

Provides:
1. SQLite connection and table initialization.
2. Safe URL parsing supporting standard file paths and in-memory test databases.
3. Thread-safe transaction execution.
4. Threat audit logging and alert log persistence functions.
"""

import os
import json
import sqlite3
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

from .models import CREATE_TABLES_SQL, HAS_SQLALCHEMY

# Default SQLite database file (ignored by git via .gitignore)
DEFAULT_DB_FILE = "weathergpt.db"
DEFAULT_DB_URL = f"sqlite:///./{DEFAULT_DB_FILE}"


def parse_db_url(db_url: Optional[str] = None) -> str:
    """
    Extract the clean filesystem path or ':memory:' from a database URL.
    Examples:
      - 'sqlite:///./weathergpt.db' -> './weathergpt.db'
      - 'sqlite:///:memory:'       -> ':memory:'
      - ':memory:'                 -> ':memory:'
      - '/tmp/test.db'             -> '/tmp/test.db'
    """
    if not db_url:
        # Check environment variable, fallback to default
        db_url = os.getenv("DATABASE_URL", DEFAULT_DB_URL)

    url_str = str(db_url).strip()

    if url_str.startswith("sqlite:///"):
        return url_str[len("sqlite:///"):]
    elif url_str.startswith("sqlite://"):
        return url_str[len("sqlite://"):]
    return url_str


def get_db_path(db_url: Optional[str] = None) -> str:
    """Return the resolved database file path or :memory:."""
    return parse_db_url(db_url)


def get_connection(db_url: Optional[str] = None) -> sqlite3.Connection:
    """
    Create a new sqlite3 Connection with Row factory enabled for dictionary access.
    """
    path = get_db_path(db_url)
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    # Enable foreign key constraints in SQLite
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(db_url: Optional[str] = None) -> None:
    """
    Initialize SQLite database tables (farmers, farm_activities, threat_event_logs, alert_logs).
    Safe and idempotent (uses CREATE TABLE IF NOT EXISTS).
    Does NOT overwrite or auto-seed existing data.
    """
    path = get_db_path(db_url)

    # Ensure parent directory exists if using a physical file path
    if path != ":memory:":
        db_path = Path(path)
        if db_path.parent and not db_path.parent.exists():
            db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = get_connection(db_url)
    try:
        conn.executescript(CREATE_TABLES_SQL)
        conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Threat Event & Alert Logging Helpers
# ---------------------------------------------------------------------------

def log_threat_event(threat_data: Dict[str, Any], db_url: Optional[str] = None) -> str:
    """
    Persist a detected ThreatEvent emitted by Sentinel Agent into threat_event_logs.
    """
    init_db(db_url)
    conn = get_connection(db_url)

    event_id = str(threat_data.get("event_id") or f"EVT-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}")
    event_type = str(threat_data.get("event_type", "none"))
    severity = str(threat_data.get("severity", "low"))
    probability = float(threat_data.get("probability", 0.0))
    confidence = str(threat_data.get("confidence", "high"))
    confidence_reason = threat_data.get("confidence_reason")
    location = str(threat_data.get("location", "Unknown"))
    rainfall_mm = threat_data.get("rainfall_mm")
    wind_speed_kmh = threat_data.get("wind_speed_kmh")
    temp_c = threat_data.get("temp_c")
    detected_at = datetime.now(timezone.utc).isoformat()
    raw_json = json.dumps(threat_data)

    query = """
    INSERT OR REPLACE INTO threat_event_logs (
        event_id, event_type, severity, probability, confidence,
        confidence_reason, location, rainfall_mm, wind_speed_kmh,
        temp_c, detected_at, raw_payload
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    try:
        conn.execute(query, (
            event_id, event_type, severity, probability, confidence,
            confidence_reason, location, rainfall_mm, wind_speed_kmh,
            temp_c, detected_at, raw_json
        ))
        conn.commit()
        return event_id
    finally:
        conn.close()


def log_alert(alert_data: Dict[str, Any], db_url: Optional[str] = None) -> str:
    """
    Persist a dispatched or queued alert record emitted by Executor Agent into alert_logs.
    """
    init_db(db_url)
    conn = get_connection(db_url)

    dispatch_id = str(alert_data.get("dispatch_id") or f"DISP-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}")
    threat_event_id = alert_data.get("threat_event_id")
    farmer_id = str(alert_data.get("farmer_id", "UNKNOWN"))
    farmer_name = str(alert_data.get("farmer_name", "Farmer"))
    channel = str(alert_data.get("channel", "sms"))
    language = str(alert_data.get("language", "en"))
    urgency = str(alert_data.get("urgency", "high"))
    message = str(alert_data.get("message", ""))
    status = str(alert_data.get("status", "queued"))
    dispatched_at = alert_data.get("timestamp") or datetime.now(timezone.utc).isoformat()

    query = """
    INSERT OR REPLACE INTO alert_logs (
        dispatch_id, threat_event_id, farmer_id, farmer_name, channel,
        language, urgency, message, status, dispatched_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    try:
        conn.execute(query, (
            dispatch_id, threat_event_id, farmer_id, farmer_name, channel,
            language, urgency, message, status, dispatched_at
        ))
        conn.commit()
        return dispatch_id
    finally:
        conn.close()


def get_threat_event_logs(limit: int = 50, db_url: Optional[str] = None) -> List[Dict[str, Any]]:
    """Fetch recent threat event logs."""
    init_db(db_url)
    conn = get_connection(db_url)
    try:
        cursor = conn.execute(
            "SELECT * FROM threat_event_logs ORDER BY detected_at DESC LIMIT ?",
            (limit,)
        )
        results = []
        for row in cursor.fetchall():
            d = dict(row)
            if d.get("raw_payload"):
                try:
                    d["raw_payload"] = json.loads(d["raw_payload"])
                except Exception:
                    pass
            results.append(d)
        return results
    finally:
        conn.close()


def get_alert_logs(
    farmer_id: Optional[str] = None,
    limit: int = 50,
    db_url: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Fetch recent alert logs, optionally filtered by farmer_id."""
    init_db(db_url)
    conn = get_connection(db_url)
    try:
        if farmer_id:
            cursor = conn.execute(
                "SELECT * FROM alert_logs WHERE farmer_id = ? ORDER BY dispatched_at DESC LIMIT ?",
                (farmer_id, limit)
            )
        else:
            cursor = conn.execute(
                "SELECT * FROM alert_logs ORDER BY dispatched_at DESC LIMIT ?",
                (limit,)
            )
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()
