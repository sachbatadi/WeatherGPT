"""
Calendar Provider Base Abstraction (tools/calendar/base.py).

Defines the core abstract interface for calendar operations:
- MockCalendarProvider (for tests and local development)
- GoogleCalendarProvider (for live Google Calendar API integration)
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class CalendarEvent(BaseModel):
    """
    Standardized Calendar Event representation across all calendar providers.
    """
    event_id: str = Field(..., description="Unique event identifier")
    title: str = Field(..., description="Event summary/title")
    description: str = Field(default="", description="Detailed event description")
    start: str = Field(..., description="Start date (YYYY-MM-DD) or ISO datetime")
    end: str = Field(..., description="End date (YYYY-MM-DD) or ISO datetime")
    location: Optional[str] = Field(None, description="Physical location or village/field")
    is_all_day: bool = Field(default=True, description="True for date-only all-day events")
    status: str = Field(default="confirmed", description="Status: confirmed, cancelled, tentative")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Custom metadata e.g. farmer_id, activity_id")


class CalendarProvider(ABC):
    """
    Abstract Base Class for Calendar Providers.
    Decouples the Executor Agent from any specific calendar backend.
    """

    @abstractmethod
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
        """Create a new calendar event and return the resulting CalendarEvent."""
        pass

    @abstractmethod
    def get_event(self, event_id: str) -> Optional[CalendarEvent]:
        """Fetch an existing calendar event by unique event ID."""
        pass

    @abstractmethod
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
        """Update/reschedule an existing calendar event. Returns updated event or None if not found."""
        pass

    @abstractmethod
    def delete_event(self, event_id: str) -> bool:
        """Delete/cancel an existing calendar event. Returns True if successfully deleted."""
        pass

    @abstractmethod
    def list_events(self) -> List[CalendarEvent]:
        """List all managed calendar events."""
        pass
