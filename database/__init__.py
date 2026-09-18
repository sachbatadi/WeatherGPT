"""
WeatherGPT Database Package (database/).

Provides SQLite connection management, ORM models, and repository interfaces
for farmer profiles, farm schedules, threat audit logs, and alert logs.
"""

from .models import (
    FarmerModel,
    FarmActivityModel,
    ThreatEventLogModel,
    AlertLogModel,
)
from .connection import (
    init_db,
    get_db_path,
    get_connection,
    log_threat_event,
    log_alert,
    get_threat_event_logs,
    get_alert_logs,
    get_alert_log_by_provider_message_id,
    update_alert_status_by_provider_id,
    check_db_health,
)

__all__ = [
    "FarmerModel",
    "FarmActivityModel",
    "ThreatEventLogModel",
    "AlertLogModel",
    "init_db",
    "get_db_path",
    "get_connection",
    "log_threat_event",
    "log_alert",
    "get_threat_event_logs",
    "get_alert_logs",
    "get_alert_log_by_provider_message_id",
    "update_alert_status_by_provider_id",
    "check_db_health",
]
