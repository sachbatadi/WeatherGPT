"""
In-Memory Mock Calendar Provider (tools/calendar/mock_calendar.py).

Provides a deterministic, fast in-memory calendar implementation for
development, CI/CD, and unit tests without external network or Google API calls.
"""

from typing import Optional, Dict, Any, List
import copy
from .base import CalendarProvider, CalendarEvent


class MockCalendarProvider(CalendarProvider):
    """
    In-memory mock calendar provider with deterministic event tracking and failure simulation.
    """

    def __init__(self, initial_events: Optional[List[CalendarEvent]] = None):
        self._events: Dict[str, CalendarEvent] = {}
        self._counter = 1
        self.should_fail = False
        self.failure_message = "Simulated Mock Calendar Failure"

        if initial_events:
            for evt in initial_events:
                self._events[evt.event_id] = copy.deepcopy(evt)

    def clear(self) -> None:
        """Clear all stored calendar events and reset counter."""
        self._events.clear()
        self._counter = 1
        self.should_fail = False

    def create_event(
        self,
        title: str,
        start: str,
        end: str,
        description: str = "",
        location: Optional[str] = None,
        is_all_day: bool = True,
        metadata: Optional[Dict[str, Any]] = None,
        event_id: Optional[str] = None
    ) -> CalendarEvent:
        if self.should_fail:
            raise RuntimeError(self.failure_message)

        if not event_id:
            event_id = f"cal_evt_mock_{self._counter:04d}"
            self._counter += 1

        event = CalendarEvent(
            event_id=event_id,
            title=title,
            description=description,
            start=start,
            end=end,
            location=location,
            is_all_day=is_all_day,
            status="confirmed",
            metadata=copy.deepcopy(metadata or {})
        )
        self._events[event_id] = event
        return copy.deepcopy(event)

    def get_event(self, event_id: str) -> Optional[CalendarEvent]:
        if self.should_fail:
            raise RuntimeError(self.failure_message)
        event = self._events.get(event_id)
        return copy.deepcopy(event) if event else None

    def update_event(
        self,
        event_id: str,
        title: Optional[str] = None,
        start: Optional[str] = None,
        end: Optional[str] = None,
        description: Optional[str] = None,
        location: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[CalendarEvent]:
        if self.should_fail:
            raise RuntimeError(self.failure_message)

        event = self._events.get(event_id)
        if not event:
            return None

        data = event.model_dump()
        if title is not None:
            data["title"] = title
        if start is not None:
            data["start"] = start
        if end is not None:
            data["end"] = end
        if description is not None:
            data["description"] = description
        if location is not None:
            data["location"] = location
        if metadata is not None:
            merged_meta = dict(data.get("metadata", {}))
            merged_meta.update(metadata)
            data["metadata"] = merged_meta

        updated = CalendarEvent(**data)
        self._events[event_id] = updated
        return copy.deepcopy(updated)

    def delete_event(self, event_id: str) -> bool:
        if self.should_fail:
            raise RuntimeError(self.failure_message)

        if event_id in self._events:
            del self._events[event_id]
            return True
        return False

    def list_events(self) -> List[CalendarEvent]:
        if self.should_fail:
            raise RuntimeError(self.failure_message)
        return [copy.deepcopy(e) for e in self._events.values()]
