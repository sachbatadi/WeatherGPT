"""
Calendar integration tests for WeatherGPT Executor.

Uses MockCalendarProvider only.
No real Google Calendar API calls are made.
"""

from tools.calendar import MockCalendarProvider
from tools.calendar.base import CalendarEvent


def test_calendar_create_update_delete():
    """Test the complete Calendar CRUD lifecycle."""

    calendar = MockCalendarProvider()

    # ---------------------------------------------------------
    # CREATE
    # ---------------------------------------------------------

    event = calendar.create_event(
        title="WeatherGPT: Postpone Irrigation",
        start="2026-09-19",
        end="2026-09-20",
        description="Postpone irrigation because of heavy rainfall.",
        location="Jalandhar",
        is_all_day=True,
        metadata={
            "source": "WeatherGPT",
            "farmer_id": "F001",
            "activity_id": "ACT-001",
            "threat_event_id": "EVT-20260913-001",
            "action_type": "postpone_irrigation",
        },
    )

    assert isinstance(event, CalendarEvent)
    assert event.event_id == "cal_evt_mock_0001"
    assert event.title == "WeatherGPT: Postpone Irrigation"
    assert event.start == "2026-09-19"
    assert event.end == "2026-09-20"

    # ---------------------------------------------------------
    # GET
    # ---------------------------------------------------------

    fetched = calendar.get_event(
        event.event_id
    )

    assert fetched is not None
    assert fetched.event_id == event.event_id
    assert fetched.metadata["farmer_id"] == "F001"
    assert fetched.metadata["activity_id"] == "ACT-001"

    # ---------------------------------------------------------
    # UPDATE / RESCHEDULE
    # ---------------------------------------------------------

    updated = calendar.update_event(
        event_id=event.event_id,
        start="2026-09-23",
        end="2026-09-24",
        description=(
            "Irrigation rescheduled after "
            "weather threat."
        ),
        metadata={
            "rescheduled": "true"
        },
    )

    assert updated is not None
    assert updated.start == "2026-09-23"
    assert updated.end == "2026-09-24"

    # Existing metadata should remain.
    assert updated.metadata["farmer_id"] == "F001"
    assert updated.metadata["activity_id"] == "ACT-001"

    # New metadata should be added.
    assert updated.metadata["rescheduled"] == "true"

    # ---------------------------------------------------------
    # LIST
    # ---------------------------------------------------------

    events = calendar.list_events()

    assert len(events) == 1
    assert events[0].event_id == event.event_id
    assert events[0].start == "2026-09-23"

    # ---------------------------------------------------------
    # DELETE
    # ---------------------------------------------------------

    deleted = calendar.delete_event(
        event.event_id
    )

    assert deleted is True

    # Event should no longer exist.
    assert calendar.get_event(
        event.event_id
    ) is None

    assert calendar.list_events() == []


def test_calendar_failure_simulation():
    """Verify that the mock provider can simulate failures."""

    calendar = MockCalendarProvider()

    calendar.should_fail = True

    try:
        calendar.create_event(
            title="Test Event",
            start="2026-09-20",
            end="2026-09-21",
        )

        assert False, (
            "Expected Mock Calendar failure "
            "was not raised."
        )

    except RuntimeError as exc:

        assert (
            str(exc)
            == "Simulated Mock Calendar Failure"
        )