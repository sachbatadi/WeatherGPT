"""
WeatherGPT Calendar Subsystem (tools/calendar/__init__.py).

Provides calendar management abstraction with support for:
- MockCalendarProvider (default for local development and deterministic tests)
- GoogleCalendarProvider (live Google Calendar API integration)
"""

import os
from typing import Optional
from .base import CalendarEvent, CalendarProvider
from .mock_calendar import MockCalendarProvider
from .google_calendar import GoogleCalendarProvider


def get_calendar_provider(mode: Optional[str] = None) -> CalendarProvider:
    """
    Factory function returning the configured CalendarProvider.
    Defaults to MockCalendarProvider unless CALENDAR_MODE=google is set.
    """
    selected_mode = (mode or os.getenv("CALENDAR_MODE", "mock")).strip().lower()
    if selected_mode == "google":
        return GoogleCalendarProvider()
    return MockCalendarProvider()


# Default singleton instance
default_calendar_provider = get_calendar_provider()

__all__ = [
    "CalendarEvent",
    "CalendarProvider",
    "MockCalendarProvider",
    "GoogleCalendarProvider",
    "get_calendar_provider",
    "default_calendar_provider"
]
