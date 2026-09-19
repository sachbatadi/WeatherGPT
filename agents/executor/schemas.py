"""
Executor Agent Schemas (agents/executor/schemas.py).

Defines the core data models for the execution layer:
- Dispatch channels (SMS, Voice, Radio-GPT, Dashboard, Database, Calendar)
- Task and execution statuses
- Dispatched alert records
- Calendar operations audit receipts
- Farm calendar plan updates
- Dashboard operational events
- Top-level ExecutorOutput receipt
"""

from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class DispatchChannel(str, Enum):
    SMS = "sms"
    VOICE_CALL = "voice_call"
    RADIO_GPT = "radio_gpt"
    DASHBOARD = "dashboard"
    DATABASE = "database"
    CALENDAR = "calendar"


class TaskStatus(str, Enum):
    PENDING = "pending"
    SUCCESS = "success"
    QUEUED = "queued"
    SKIPPED = "skipped"
    FAILED = "failed"


class ExecutionStatus(str, Enum):
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILED = "failed"
    SKIPPED = "skipped"


class DispatchedAlert(BaseModel):
    """Record of an alert notification dispatched or queued for a farmer."""
    dispatch_id: str = Field(..., description="Unique dispatch identifier e.g. DISP-001")
    farmer_id: str
    farmer_name: str
    phone: Optional[str] = None
    channel: DispatchChannel
    language: str = "en"
    urgency: str = "high"
    message: str
    status: TaskStatus = TaskStatus.QUEUED
    timestamp: str
    provider: Optional[str] = None
    provider_message_id: Optional[str] = None
    error_message: Optional[str] = None


class PlanUpdateRecord(BaseModel):
    """Record of a farm calendar activity status change applied to the database."""
    farmer_id: str
    activity_id: str
    activity_type: str
    old_status: str
    new_status: str
    rescheduled_to: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)


class CalendarOperation(BaseModel):
    """Record of a calendar event creation, update, reschedule, or deletion."""
    operation_id: str = Field(..., description="Unique operation identifier e.g. CAL-OP-001")
    farmer_id: str
    activity_id: Optional[str] = None
    operation: str = Field(..., description="Operation: create, update, reschedule, delete, skip")
    calendar_event_id: Optional[str] = None
    status: TaskStatus = TaskStatus.SUCCESS
    message: str
    timestamp: str


class DashboardEvent(BaseModel):
    """Operational event record emitted for Member 5 (Dashboard telemetry)."""
    event_id: str
    threat_event_id: str
    farmer_id: str
    farmer_name: str
    risk_level: str
    action_title: str
    execution_status: str
    calendar_status: str
    timestamp: str
    details: Dict[str, Any] = Field(default_factory=dict)


class ExecutorOutput(BaseModel):
    """
    Top-level execution receipt emitted by the Executor Agent to the Orchestrator.
    Contains complete audit trail of calendar operations, plan updates, and alert dispatches.
    """
    threat_event_id: str
    execution_status: str = Field(
        default=ExecutionStatus.SUCCESS.value,
        description="Overall status: success, partial_success, failed, skipped"
    )
    total_alerts_dispatched: int = 0
    total_plans_updated: int = 0
    total_calendar_operations: int = 0
    dispatched_alerts: List[DispatchedAlert] = Field(default_factory=list)
    applied_plan_updates: List[PlanUpdateRecord] = Field(default_factory=list)
    calendar_operations: List[CalendarOperation] = Field(default_factory=list)
    dashboard_events: List[DashboardEvent] = Field(default_factory=list)
    next_observation_schedule: List[Dict[str, Any]] = Field(default_factory=list)
    execution_log: List[str] = Field(default_factory=list)
