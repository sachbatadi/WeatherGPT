"""
WeatherGPT Executor Agent.

The Executor is the action layer between the Strategist and downstream
systems such as FarmerDB, alerts, Radio-GPT, dashboard, and Calendar.

It consumes structured Strategist ActionItems and performs controlled,
auditable execution without using an LLM for arbitrary operations.
"""

from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from .schemas import (
    ExecutorOutput,
    ExecutionStatus,
    TaskStatus,
    PlanUpdateRecord,
    CalendarOperation,
)

from .dispatcher import AlertDispatcher

from agents.strategist.schemas import ActionType
from tools.farmer.farmer_db import default_farmer_db
from tools.calendar import default_calendar_provider


# ============================================================
# Helpers
# ============================================================

def _now() -> str:
    """Return a UTC ISO timestamp."""
    return datetime.now(timezone.utc).isoformat()


def _enum_value(value: Any) -> str:
    """Safely convert Enum/string values to their string value."""
    if hasattr(value, "value"):
        return str(value.value)
    return str(value)


def _get_farmer_id(farmer: Dict[str, Any]) -> Optional[str]:
    """Support both lightweight state farmer format and DB format."""
    return farmer.get("farmer_id") or farmer.get("id")


def _get_farmer_name(
    farmer: Dict[str, Any],
    db_farmer: Optional[Dict[str, Any]] = None,
) -> str:
    """Resolve farmer name from state first, then DB."""
    return (
        farmer.get("name")
        or (db_farmer or {}).get("name")
        or "Farmer"
    )


def _get_db_farmer(farmer_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve a farmer from the existing in-memory FarmerDB.

    The current FarmerDB uses an internal _farmers mapping. This helper
    intentionally keeps the lookup isolated from the rest of the Executor.
    """
    farmers = getattr(default_farmer_db, "_farmers", {})
    return farmers.get(farmer_id)


def _get_actions(assessment: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Return structured ActionItems from a FarmerAssessment."""
    actions = assessment.get("actions", [])

    if actions is None:
        return []

    return [
        action.model_dump() if hasattr(action, "model_dump") else action
        for action in actions
    ]


def _find_activity(
    db_farmer: Dict[str, Any],
    activity_id: Optional[str],
) -> Optional[Dict[str, Any]]:
    """Find an activity in a farmer's current_plan."""
    if not activity_id:
        return None

    current_plan = db_farmer.get("current_plan", [])

    for activity in current_plan:
        if isinstance(activity, dict):
            if activity.get("activity_id") == activity_id:
                return activity

        elif getattr(activity, "activity_id", None) == activity_id:
            return activity

    return None


def _set_activity_field(
    activity: Any,
    field_name: str,
    value: Any,
) -> None:
    """Set a field on either a dict activity or a model-like activity."""
    if isinstance(activity, dict):
        activity[field_name] = value
    else:
        try:
            setattr(activity, field_name, value)
        except Exception:
            pass


def _get_activity_field(
    activity: Any,
    field_name: str,
    default: Any = None,
) -> Any:
    """Read a field from either a dict or model-like activity."""
    if isinstance(activity, dict):
        return activity.get(field_name, default)

    return getattr(activity, field_name, default)


def _is_relative_schedule(value: Any) -> bool:
    """
    Detect schedule values that are conditions or relative instructions
    rather than concrete calendar dates.
    """
    if value is None:
        return False

    value = str(value).strip()

    if not value:
        return False

    relative_markers = (
        "+",
        "after",
        "when ",
        "once ",
        "until ",
        "below ",
        "above ",
        "ceases",
        "subsides",
        "moist",
        "suitable",
    )

    lowered = value.lower()

    return (
        lowered.startswith(relative_markers)
        or "after" in lowered
        or "when" in lowered
        or "below" in lowered
        or "ceases" in lowered
        or "subsides" in lowered
    )


def _calendar_operation_id(
    farmer_id: str,
    activity_id: Optional[str],
) -> str:
    """Create a deterministic mock-friendly operation ID."""
    activity_part = activity_id or "general"
    return (
        f"cal_op_{farmer_id}_{activity_part}"
        .replace(" ", "_")
    )


# ============================================================
# Action Validation
# ============================================================

def _validate_action(action: Dict[str, Any]) -> Optional[str]:
    """
    Validate that an ActionItem contains a recognized ActionType.

    Returns None when valid, otherwise an error message.
    """
    action_type = action.get("action_type")

    if not action_type:
        return "ActionItem has no action_type."

    action_value = _enum_value(action_type)

    valid_actions = {
        _enum_value(member)
        for member in ActionType
    }

    if action_value not in valid_actions:
        return f"Unsupported ActionType: {action_value}"

    return None


# ============================================================
# Farm Plan Execution
# ============================================================

def _execute_plan_action(
    threat_id: str,
    farmer: Dict[str, Any],
    action: Dict[str, Any],
    execution_log: List[str],
) -> Optional[PlanUpdateRecord]:
    """
    Execute a structured farm-plan ActionItem against FarmerDB.

    Returns a PlanUpdateRecord when an activity was actually changed.
    Returns None when the action does not modify an existing activity.
    """
    farmer_id = _get_farmer_id(farmer)

    if not farmer_id:
        execution_log.append(
            "SKIPPED: Action has no farmer_id."
        )
        return None

    db_farmer = _get_db_farmer(farmer_id)

    if db_farmer is None:
        execution_log.append(
            f"FAILED: Farmer {farmer_id} was not found in FarmerDB."
        )
        return None

    action_type = _enum_value(action.get("action_type"))
    activity_id = action.get("affected_activity_id")

    # Actions that do not necessarily modify an existing activity.
    calendar_only_actions = {
        "drainage_preparation",
        "protective_covering",
        "heat_stress_mitigation",
        "frost_protection",
        "disease_preventative",
        "no_action",
    }

    if action_type in calendar_only_actions and not activity_id:
        execution_log.append(
            f"QUEUED: {action_type} for farmer {farmer_id}; "
            "no existing activity required."
        )
        return None

    if not activity_id:
        execution_log.append(
            f"SKIPPED: {action_type} for farmer {farmer_id} "
            "has no affected_activity_id."
        )
        return None

    activity = _find_activity(
        db_farmer,
        activity_id,
    )

    if activity is None:
        execution_log.append(
            f"FAILED: Activity {activity_id} for farmer "
            f"{farmer_id} was not found."
        )
        return None

    old_status = str(
        _get_activity_field(
            activity,
            "status",
            "scheduled",
        )
    )

    old_date = _get_activity_field(
        activity,
        "scheduled_date",
    )

    new_status = old_status
    new_date = action.get("rescheduled_date")

    # --------------------------------------------------------
    # Controlled action mapping
    # --------------------------------------------------------

    status_mapping = {
        "postpone_irrigation": "postponed",
        "reschedule_spray": "rescheduled",
        "delay_fertilization": "postponed",
        "expedite_harvest": "expedited",
        "halt_harvest": "halted",
    }

    if action_type in status_mapping:
        new_status = status_mapping[action_type]

    elif action_type in {
        "drainage_preparation",
        "protective_covering",
        "heat_stress_mitigation",
        "frost_protection",
        "disease_preventative",
    }:
        new_status = "action_required"

    elif action_type == "no_action":
        execution_log.append(
            f"SKIPPED: no_action for farmer {farmer_id}."
        )
        return None

    # --------------------------------------------------------
    # Idempotency
    # --------------------------------------------------------

    if old_status == new_status and (
        not new_date
        or _is_relative_schedule(new_date)
        or str(old_date) == str(new_date)
    ):
        execution_log.append(
            f"SKIPPED: Activity {activity_id} for farmer "
            f"{farmer_id} is already in the requested state."
        )
        return None

    # --------------------------------------------------------
    # Apply controlled mutation
    # --------------------------------------------------------

    _set_activity_field(
        activity,
        "status",
        new_status,
    )

    # Only write a concrete date to FarmerDB.
    # Relative/weather-dependent conditions are handled by Calendar
    # as pending conditions instead.
    if new_date and not _is_relative_schedule(new_date):
        _set_activity_field(
            activity,
            "scheduled_date",
            new_date,
        )

    execution_log.append(
        f"SUCCESS: Farmer {farmer_id}, activity {activity_id}: "
        f"{old_status} → {new_status}"
    )

    return PlanUpdateRecord(
        farmer_id=farmer_id,
        activity_id=activity_id,
        activity_type=str(
            _get_activity_field(
                activity,
                "activity_type",
                action_type,
            )
        ),
        old_status=old_status,
        new_status=new_status,
        rescheduled_to=new_date,
        details={
            "action_type": action_type,
            "threat_event_id": threat_id,
            "previous_scheduled_date": old_date,
            "description": action.get("description", ""),
            "schedule_type": (
                "conditional"
                if _is_relative_schedule(new_date)
                else "fixed"
            ),
        },
    )


# ============================================================
# Calendar Execution
# ============================================================

def _execute_calendar_action(
    threat_id: str,
    farmer: Dict[str, Any],
    action: Dict[str, Any],
    plan_update: Optional[PlanUpdateRecord],
    execution_log: List[str],
) -> Optional[CalendarOperation]:
    """
    Execute Calendar-related behavior.

    Fixed dates:
        Create/update a calendar event.

    Relative or weather-dependent conditions:
        Record a pending condition instead of inventing a date.

    Actions without an affected activity:
        Do not create a meaningless calendar event.
    """
    farmer_id = _get_farmer_id(farmer)

    if not farmer_id:
        return None

    activity_id = action.get("affected_activity_id")
    action_type = _enum_value(action.get("action_type"))
    rescheduled_date = action.get("rescheduled_date")

    operation_id = _calendar_operation_id(
        farmer_id,
        activity_id,
    )

    timestamp = _now()

    # --------------------------------------------------------
    # No affected activity
    # --------------------------------------------------------

    if not activity_id:
        execution_log.append(
            f"SKIPPED: Calendar action for farmer {farmer_id} "
            "has no affected_activity_id."
        )
        return CalendarOperation(
            operation_id=operation_id,
            farmer_id=farmer_id,
            activity_id=None,
            operation="skip",
            calendar_event_id=None,
            status=TaskStatus.SKIPPED,
            message=(
                "No affected activity was supplied; "
                "no calendar event was created."
            ),
            timestamp=timestamp,
        )

    # --------------------------------------------------------
    # No rescheduling information
    # --------------------------------------------------------

    if not rescheduled_date:
        execution_log.append(
            f"SKIPPED: Calendar action for farmer {farmer_id}, "
            f"activity {activity_id} has no rescheduled date."
        )
        return CalendarOperation(
            operation_id=operation_id,
            farmer_id=farmer_id,
            activity_id=activity_id,
            operation="skip",
            calendar_event_id=None,
            status=TaskStatus.SKIPPED,
            message="No calendar scheduling change was requested.",
            timestamp=timestamp,
        )

    # --------------------------------------------------------
    # Conditional / relative scheduling
    # --------------------------------------------------------

    if _is_relative_schedule(rescheduled_date):
        execution_log.append(
            f"PENDING: Calendar condition for farmer {farmer_id}, "
            f"activity {activity_id}: {rescheduled_date}"
        )

        return CalendarOperation(
            operation_id=operation_id,
            farmer_id=farmer_id,
            activity_id=activity_id,
            operation="pending_condition",
            calendar_event_id=None,
            status=TaskStatus.QUEUED,
            message=(
                f"Calendar update is pending the condition: "
                f"{rescheduled_date}"
            ),
            timestamp=timestamp,
        )

    # --------------------------------------------------------
    # Concrete calendar date
    # --------------------------------------------------------

    db_farmer = _get_db_farmer(farmer_id)

    if db_farmer is None:
        execution_log.append(
            f"FAILED: Farmer {farmer_id} was not found while "
            "processing Calendar action."
        )

        return CalendarOperation(
            operation_id=operation_id,
            farmer_id=farmer_id,
            activity_id=activity_id,
            operation="reschedule",
            calendar_event_id=None,
            status=TaskStatus.FAILED,
            message="Farmer was not found in FarmerDB.",
            timestamp=timestamp,
        )

    activity = _find_activity(
        db_farmer,
        activity_id,
    )

    if activity is None:
        execution_log.append(
            f"FAILED: Activity {activity_id} for farmer "
            f"{farmer_id} was not found while processing Calendar."
        )

        return CalendarOperation(
            operation_id=operation_id,
            farmer_id=farmer_id,
            activity_id=activity_id,
            operation="reschedule",
            calendar_event_id=None,
            status=TaskStatus.FAILED,
            message="Activity was not found in FarmerDB.",
            timestamp=timestamp,
        )

    old_date = _get_activity_field(
        activity,
        "scheduled_date",
    )

    # --------------------------------------------------------
    # Existing Calendar event mapping
    # --------------------------------------------------------

    existing_event_id = _get_activity_field(
        activity,
        "calendar_event_id",
    )

    try:
        if existing_event_id:
            updated_event = default_calendar_provider.update_event(
                existing_event_id,
                start=str(rescheduled_date),
                end=str(rescheduled_date),
            )

            execution_log.append(
                f"SUCCESS: Calendar event {existing_event_id} "
                f"rescheduled from {old_date} to {rescheduled_date}."
            )

            return CalendarOperation(
                operation_id=operation_id,
                farmer_id=farmer_id,
                activity_id=activity_id,
                operation="reschedule",
                calendar_event_id=existing_event_id,
                status=TaskStatus.SUCCESS,
                message=(
                    f"Calendar event rescheduled from "
                    f"{old_date} to {rescheduled_date}."
                ),
                timestamp=timestamp,
            )

        # ----------------------------------------------------
        # Create event if no event exists
        # ----------------------------------------------------

        event = default_calendar_provider.create_event(
            title=(
                f"WeatherGPT: "
                f"{action.get('title') or action_type}"
            ),
            description=(
                action.get("description")
                or f"WeatherGPT action for farmer {farmer_id}."
            ),
            start=str(rescheduled_date),
            end=str(rescheduled_date),
            location=(
                farmer.get("location")
                or db_farmer.get("location")
            ),
        )

        event_id = getattr(
            event,
            "event_id",
            None,
        )

        if isinstance(event, dict):
            event_id = event.get("event_id")

        if event_id:
            _set_activity_field(
                activity,
                "calendar_event_id",
                event_id,
            )

        execution_log.append(
            f"SUCCESS: Created calendar event {event_id} "
            f"for activity {activity_id}."
        )

        return CalendarOperation(
            operation_id=operation_id,
            farmer_id=farmer_id,
            activity_id=activity_id,
            operation="create",
            calendar_event_id=event_id,
            status=TaskStatus.SUCCESS,
            message=(
                f"Created calendar event {event_id} "
                f"for {rescheduled_date}."
            ),
            timestamp=timestamp,
        )

    except Exception as exc:
        execution_log.append(
            f"FAILED: Calendar operation for farmer "
            f"{farmer_id}, activity {activity_id}: {exc}"
        )

        return CalendarOperation(
            operation_id=operation_id,
            farmer_id=farmer_id,
            activity_id=activity_id,
            operation="reschedule",
            calendar_event_id=existing_event_id,
            status=TaskStatus.FAILED,
            message=f"Calendar operation failed: {exc}",
            timestamp=timestamp,
        )


# ============================================================
# Main Executor
# ============================================================

def run_executor_node(
    state: Dict[str, Any],
) -> Dict[str, Any]:
    """
    LangGraph-compatible Executor node.

    Flow:

        Strategist
            ↓
        ActionItems
            ↓
        Executor
            ├── FarmerDB
            ├── Calendar
            ├── Alert Dispatcher
            ├── Radio-GPT queue
            └── Dashboard events
    """

    execution_log: List[str] = []
    dispatched_alerts = []
    applied_plan_updates: List[PlanUpdateRecord] = []
    calendar_operations: List[CalendarOperation] = []
    dashboard_events = []

    threat = state.get("threat") or {}

    threat_id = str(
        threat.get("event_id")
        or state.get("strategist_output", {}).get(
            "threat_event_id",
            "UNKNOWN-EVENT",
        )
    )

    # --------------------------------------------------------
    # Safety: Executor should only run for a detected threat.
    # --------------------------------------------------------

    if not state.get("threat_detected", False):
        execution_log.append(
            "SKIPPED: Executor received no detected threat."
        )

        executor_output = ExecutorOutput(
            threat_event_id=threat_id,
            execution_status=ExecutionStatus.SKIPPED.value,
            total_alerts_dispatched=0,
            total_plans_updated=0,
            total_calendar_operations=0,
            dispatched_alerts=[],
            applied_plan_updates=[],
            calendar_operations=[],
            dashboard_events=[],
            next_observation_schedule=[],
            execution_log=execution_log,
        )

        return {
            "execution_summary": {
                "status": ExecutionStatus.SKIPPED.value,
                "alerts": 0,
                "plan_updates": 0,
                "calendar_operations": 0,
            },
            "dispatched_alerts": [],
            "applied_plan_updates": [],
            "calendar_operations": [],
            "executor_output": executor_output.model_dump(),
            "alert_status": "no_alert_needed",
        }

    execution_log.append(
        f"Executor started for threat {threat_id}."
    )

    assessments = state.get(
        "strategist_assessments",
        [],
    )

    # Fallback to StrategistOutput if assessments are not separately
    # available in state.
    if not assessments:
        strategist_output = (
            state.get("strategist_output")
            or {}
        )

        assessments = strategist_output.get(
            "assessments",
            [],
        )

    dispatcher = AlertDispatcher()

    # --------------------------------------------------------
    # Build farmer lookup from state
    # --------------------------------------------------------

    affected_farmers = state.get(
        "affected_farmers",
        [],
    )

    farmer_lookup = {}

    for farmer in affected_farmers:
        farmer_id = _get_farmer_id(farmer)

        if farmer_id:
            farmer_lookup[farmer_id] = farmer

    # --------------------------------------------------------
    # Process every FarmerAssessment
    # --------------------------------------------------------

    for assessment in assessments:
        farmer_id = assessment.get("farmer_id")

        if not farmer_id:
            execution_log.append(
                "SKIPPED: FarmerAssessment has no farmer_id."
            )
            continue

        farmer = farmer_lookup.get(
            farmer_id,
            {
                "farmer_id": farmer_id,
                "name": assessment.get(
                    "farmer_name",
                    "Farmer",
                ),
            },
        )

        db_farmer = _get_db_farmer(
            farmer_id
        )

        if db_farmer:
            merged_farmer = {
                **db_farmer,
                **farmer,
            }
        else:
            merged_farmer = farmer

        farmer_name = _get_farmer_name(
            farmer,
            db_farmer,
        )

        actions = _get_actions(
            assessment
        )

        # ----------------------------------------------------
        # Execute farm actions
        # ----------------------------------------------------

        farmer_plan_updates_before = len(
            applied_plan_updates
        )

        for action in actions:
            validation_error = _validate_action(
                action
            )

            if validation_error:
                execution_log.append(
                    f"FAILED: Farmer {farmer_id}: "
                    f"{validation_error}"
                )
                continue

            plan_update = _execute_plan_action(
                threat_id=threat_id,
                farmer=merged_farmer,
                action=action,
                execution_log=execution_log,
            )

            if plan_update:
                applied_plan_updates.append(
                    plan_update
                )

            # ------------------------------------------------
            # Calendar execution
            # ------------------------------------------------

            calendar_operation = (
                _execute_calendar_action(
                    threat_id=threat_id,
                    farmer=merged_farmer,
                    action=action,
                    plan_update=plan_update,
                    execution_log=execution_log,
                )
            )

            if (
                calendar_operation
                and calendar_operation.status != TaskStatus.SKIPPED
            ):
                calendar_operations.append(
                    calendar_operation
                )

        farmer_plan_updates_after = len(
            applied_plan_updates
        )

        farmer_plan_was_updated = (
            farmer_plan_updates_after
            > farmer_plan_updates_before
        )

        # ----------------------------------------------------
        # Alert dispatch
        # ----------------------------------------------------

        if state.get(
            "alert_required",
            False,
        ):
            primary_action = (
                actions[0].get("title")
                if actions
                else "Weather emergency advisory"
            )

            urgency = "high"

            if actions:
                urgency = str(
                    actions[0].get(
                        "urgency",
                        "high",
                    )
                )

            sms_alert = dispatcher.create_sms_alert(
                threat_id=threat_id,
                farmer=merged_farmer,
                action_title=primary_action,
                urgency=urgency,
            )

            if sms_alert:
                dispatched_alerts.append(
                    sms_alert
                )

        # ----------------------------------------------------
        # Radio-GPT handoff
        # ----------------------------------------------------

        radio_payloads = state.get(
            "radio_gpt_payload",
            [],
        )

        for payload in radio_payloads:
            if payload.get(
                "farmer_id"
            ) != farmer_id:
                continue

            multilingual = payload.get(
                "multilingual_scripts",
                {},
            )

            language = str(
                merged_farmer.get(
                    "language",
                    "en",
                )
            ).lower()

            script = (
                multilingual.get(language)
                or payload.get("script")
                or multilingual.get("en")
                or ""
            )

            if not script:
                execution_log.append(
                    f"SKIPPED: No Radio-GPT script "
                    f"for farmer {farmer_id}."
                )
                continue

            radio_alert = (
                dispatcher.queue_radio_gpt_broadcast(
                    threat_id=threat_id,
                    farmer_id=farmer_id,
                    farmer_name=farmer_name,
                    phone=payload.get(
                        "phone",
                        merged_farmer.get(
                            "phone"
                        ),
                    ),
                    script=script,
                    language=language,
                    urgency="high",
                )
            )

            if radio_alert:
                dispatched_alerts.append(
                    radio_alert
                )

        # ----------------------------------------------------
        # Dashboard event
        # ----------------------------------------------------

        farmer_calendar_operations = [
            operation
            for operation in calendar_operations
            if operation.farmer_id == farmer_id
        ]

        successful_calendar_operations = [
            operation
            for operation in farmer_calendar_operations
            if operation.status == TaskStatus.SUCCESS
        ]

        pending_calendar_operations = [
            operation
            for operation in farmer_calendar_operations
            if operation.status == TaskStatus.QUEUED
            and operation.operation == "pending_condition"
        ]


        failed_calendar_operations = [
            operation
            for operation in farmer_calendar_operations
            if operation.status == TaskStatus.FAILED
        ]

        if successful_calendar_operations:
            calendar_status = "updated"

        elif pending_calendar_operations:
            calendar_status = "pending_condition"

        elif failed_calendar_operations:
            calendar_status = "failed"

        elif farmer_calendar_operations:
            calendar_status = "unchanged"

        else:
            calendar_status = "unchanged"

        action_title = (
            actions[0].get("title")
            if actions
            else "Weather advisory"
        )

        dashboard_event = (
            dispatcher.create_dashboard_event(
                threat_id=threat_id,
                farmer_id=farmer_id,
                farmer_name=farmer_name,
                risk_level=str(
                    assessment.get(
                        "risk_level",
                        state.get(
                            "risk_level",
                            "unknown",
                        ),
                    )
                ),
                action_title=action_title,
                execution_status="processed",
                calendar_status=calendar_status,
                details={
                    "risk_score": assessment.get(
                        "risk_score"
                    ),
                    "action_count": len(actions),
                    "plan_updated": farmer_plan_was_updated,
                    "calendar_operations": len(
                        farmer_calendar_operations
                    ),
                    "calendar_successes": len(
                        successful_calendar_operations
                    ),
                    "calendar_pending": len(
                        pending_calendar_operations
                    ),
                    "calendar_failures": len(
                        failed_calendar_operations
                    ),
                    "replanning_required": assessment.get(
                        "replanning_required",
                        False,
                    ),
                },
            )
        )

        dashboard_events.append(
            dashboard_event
        )

    # --------------------------------------------------------
    # Monitoring / re-observation information
    # --------------------------------------------------------

    next_observation_schedule = []

    for assessment in assessments:
        trigger = assessment.get(
            "next_observation"
        )

        if trigger:
            if hasattr(
                trigger,
                "model_dump",
            ):
                trigger = trigger.model_dump()

            next_observation_schedule.append(
                trigger
            )

    # --------------------------------------------------------
    # Determine overall execution status
    # --------------------------------------------------------

    failure_count = sum(
        1
        for log in execution_log
        if log.startswith("FAILED:")
    )

    success_count = sum(
        1
        for log in execution_log
        if log.startswith("SUCCESS:")
    )

    if failure_count == 0 and (
        success_count > 0
        or dispatched_alerts
        or dashboard_events
        or calendar_operations
    ):
        overall_status = (
            ExecutionStatus.SUCCESS.value
        )

    elif success_count > 0 or dispatched_alerts:
        overall_status = (
            ExecutionStatus.PARTIAL_SUCCESS.value
        )

    elif failure_count > 0:
        overall_status = (
            ExecutionStatus.FAILED.value
        )

    else:
        overall_status = (
            ExecutionStatus.SKIPPED.value
        )

    # --------------------------------------------------------
    # Alert status
    # --------------------------------------------------------

    if not state.get(
        "alert_required",
        False,
    ):
        alert_status = "no_alert_needed"

    elif dispatched_alerts and failure_count == 0:
        alert_status = "dispatched"

    elif dispatched_alerts:
        alert_status = "partially_dispatched"

    else:
        alert_status = "failed"

    # --------------------------------------------------------
    # Execution receipt
    # --------------------------------------------------------

    executor_output = ExecutorOutput(
        threat_event_id=threat_id,
        execution_status=overall_status,
        total_alerts_dispatched=len(
            dispatched_alerts
        ),
        total_plans_updated=len(
            applied_plan_updates
        ),
        total_calendar_operations=len(
            calendar_operations
        ),
        dispatched_alerts=dispatched_alerts,
        applied_plan_updates=applied_plan_updates,
        calendar_operations=calendar_operations,
        dashboard_events=dashboard_events,
        next_observation_schedule=(
            next_observation_schedule
        ),
        execution_log=execution_log,
    )

    execution_summary = {
        "status": overall_status,
        "threat_event_id": threat_id,
        "alerts": len(
            dispatched_alerts
        ),
        "plan_updates": len(
            applied_plan_updates
        ),
        "calendar_operations": len(
            calendar_operations
        ),
        "dashboard_events": len(
            dashboard_events
        ),
        "failures": failure_count,
        "timestamp": _now(),
    }

    execution_log.append(
        f"Executor completed with status="
        f"{overall_status}."
    )

    return {
        "execution_summary": execution_summary,

        "dispatched_alerts": [
            alert.model_dump()
            for alert in dispatched_alerts
        ],

        "applied_plan_updates": [
            update.model_dump()
            for update in applied_plan_updates
        ],

        "calendar_operations": [
            operation.model_dump()
            for operation in calendar_operations
        ],

        "executor_output": (
            executor_output.model_dump()
        ),

        "alert_status": alert_status,
    }