"""
Google Calendar API Provider (tools/calendar/google_calendar.py).

Implements live Google Calendar event operations using the official
Google Calendar API.

Credentials and configuration are loaded from environment variables.

Environment variables:
    GOOGLE_CALENDAR_ID
    GOOGLE_APPLICATION_CREDENTIALS
"""

import os
from typing import Optional, Dict, Any, List

from .base import CalendarProvider, CalendarEvent


class GoogleCalendarProvider(CalendarProvider):
    """
    Live Google Calendar integration using google-api-python-client.

    This provider implements the same interface as MockCalendarProvider,
    allowing the Executor to switch between mock and real calendar
    implementations without changing Executor logic.
    """

    def __init__(
        self,
        calendar_id: Optional[str] = None,
        credentials_path: Optional[str] = None
    ):
        self.calendar_id = (
            calendar_id
            or os.getenv("GOOGLE_CALENDAR_ID", "primary")
        )

        self.credentials_path = (
            credentials_path
            or os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        )

        self._service = None

    # ------------------------------------------------------------------
    # GOOGLE SERVICE INITIALIZATION
    # ------------------------------------------------------------------

    def _get_service(self):
        """
        Lazily initialize the Google Calendar API service.

        The API libraries and credentials are loaded only when a real
        calendar operation is requested.
        """

        if self._service is not None:
            return self._service

        try:
            from googleapiclient.discovery import build
            from google.oauth2 import service_account
        except ImportError as exc:
            raise RuntimeError(
                "Google Calendar API libraries are not installed.\n"
                "Install them with:\n"
                "pip install google-api-python-client "
                "google-auth google-auth-oauthlib "
                "google-auth-httplib2"
            ) from exc

        if not self.credentials_path:
            raise RuntimeError(
                "Google Calendar credentials are not configured.\n"
                "Set GOOGLE_APPLICATION_CREDENTIALS in .env "
                "or use CALENDAR_MODE=mock."
            )

        if not os.path.exists(self.credentials_path):
            raise RuntimeError(
                f"Google Calendar credentials file not found:\n"
                f"{self.credentials_path}\n\n"
                "Please check GOOGLE_APPLICATION_CREDENTIALS "
                "or use CALENDAR_MODE=mock."
            )

        scopes = [
            "https://www.googleapis.com/auth/calendar"
        ]

        try:
            credentials = (
                service_account
                .Credentials
                .from_service_account_file(
                    self.credentials_path,
                    scopes=scopes
                )
            )

            self._service = build(
                "calendar",
                "v3",
                credentials=credentials
            )

        except Exception as exc:
            raise RuntimeError(
                f"Failed to initialize Google Calendar service: {exc}"
            ) from exc

        return self._service

    # ------------------------------------------------------------------
    # HELPERS
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_start(result: Dict[str, Any]) -> str:
        """
        Extract the start value from a Google Calendar event.
        """
        start = result.get("start", {})

        return (
            start.get("date")
            or start.get("dateTime")
            or ""
        )

    @staticmethod
    def _extract_end(result: Dict[str, Any]) -> str:
        """
        Extract the end value from a Google Calendar event.
        """
        end = result.get("end", {})

        return (
            end.get("date")
            or end.get("dateTime")
            or ""
        )

    @staticmethod
    def _is_all_day(result: Dict[str, Any]) -> bool:
        """
        Determine whether a Google Calendar event is an all-day event.
        """
        return "date" in result.get("start", {})

    @staticmethod
    def _extract_metadata(
        result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Extract private extended properties from a Google Calendar event.
        """
        extended_properties = result.get(
            "extendedProperties",
            {}
        )

        private_properties = extended_properties.get(
            "private",
            {}
        )

        return dict(private_properties)

    def _result_to_calendar_event(
        self,
        result: Dict[str, Any]
    ) -> CalendarEvent:
        """
        Convert a Google Calendar API event into our standardized
        CalendarEvent model.
        """

        return CalendarEvent(
            event_id=result.get("id", ""),
            title=result.get("summary", ""),
            description=result.get("description", ""),
            start=self._extract_start(result),
            end=self._extract_end(result),
            location=result.get("location"),
            is_all_day=self._is_all_day(result),
            status=result.get("status", "confirmed"),
            metadata=self._extract_metadata(result)
        )

    # ------------------------------------------------------------------
    # CREATE
    # ------------------------------------------------------------------

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
        """
        Create a new Google Calendar event.
        """

        service = self._get_service()

        body: Dict[str, Any] = {
            "summary": title,
            "description": description,
        }

        if location:
            body["location"] = location

        if is_all_day:
            body["start"] = {
                "date": start
            }

            body["end"] = {
                "date": end
            }

        else:
            body["start"] = {
                "dateTime": start
            }

            body["end"] = {
                "dateTime": end
            }

        # Store WeatherGPT information inside Google's private
        # extended properties.
        if metadata:
            body["extendedProperties"] = {
                "private": {
                    str(key): str(value)
                    for key, value in metadata.items()
                }
            }

        # Google Calendar allows specifying an event ID, but only
        # when the ID satisfies Google's event ID requirements.
        if event_id:
            body["id"] = event_id

        try:
            result = (
                service.events()
                .insert(
                    calendarId=self.calendar_id,
                    body=body
                )
                .execute()
            )

        except Exception as exc:
            raise RuntimeError(
                f"Failed to create Google Calendar event: {exc}"
            ) from exc

        return self._result_to_calendar_event(result)

    # ------------------------------------------------------------------
    # GET
    # ------------------------------------------------------------------

    def get_event(
        self,
        event_id: str
    ) -> Optional[CalendarEvent]:
        """
        Retrieve an existing Google Calendar event.

        Returns None if the event does not exist.
        """

        service = self._get_service()

        try:
            result = (
                service.events()
                .get(
                    calendarId=self.calendar_id,
                    eventId=event_id
                )
                .execute()
            )

        except Exception:
            return None

        return self._result_to_calendar_event(result)

    # ------------------------------------------------------------------
    # UPDATE
    # ------------------------------------------------------------------

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
        """
        Update/reschedule an existing Google Calendar event.

        Uses PATCH so that fields not supplied by the Executor remain
        unchanged.
        """

        service = self._get_service()

        existing = self.get_event(event_id)

        if existing is None:
            return None

        patch_body: Dict[str, Any] = {}

        if title is not None:
            patch_body["summary"] = title

        if description is not None:
            patch_body["description"] = description

        if location is not None:
            patch_body["location"] = location

        if start is not None:
            if existing.is_all_day:
                patch_body["start"] = {
                    "date": start
                }
            else:
                patch_body["start"] = {
                    "dateTime": start
                }

        if end is not None:
            if existing.is_all_day:
                patch_body["end"] = {
                    "date": end
                }
            else:
                patch_body["end"] = {
                    "dateTime": end
                }

        if metadata is not None:
            merged_metadata = dict(existing.metadata)
            merged_metadata.update(metadata)

            patch_body["extendedProperties"] = {
                "private": {
                    str(key): str(value)
                    for key, value in merged_metadata.items()
                }
            }

        # Nothing to update.
        if not patch_body:
            return existing

        try:
            result = (
                service.events()
                .patch(
                    calendarId=self.calendar_id,
                    eventId=event_id,
                    body=patch_body
                )
                .execute()
            )

        except Exception as exc:
            raise RuntimeError(
                f"Failed to update Google Calendar event "
                f"{event_id}: {exc}"
            ) from exc

        return self._result_to_calendar_event(result)

    # ------------------------------------------------------------------
    # DELETE
    # ------------------------------------------------------------------

    def delete_event(
        self,
        event_id: str
    ) -> bool:
        """
        Delete an existing Google Calendar event.

        Returns:
            True  -> event successfully deleted
            False -> event was not found or deletion failed
        """

        service = self._get_service()

        try:
            (
                service.events()
                .delete(
                    calendarId=self.calendar_id,
                    eventId=event_id
                )
                .execute()
            )

            return True

        except Exception:
            return False

    # ------------------------------------------------------------------
    # LIST
    # ------------------------------------------------------------------

    def list_events(self) -> List[CalendarEvent]:
        """
        Retrieve up to 100 events from the configured calendar.
        """

        service = self._get_service()

        try:
            result = (
                service.events()
                .list(
                    calendarId=self.calendar_id,
                    maxResults=100,
                    singleEvents=True,
                    orderBy="startTime"
                )
                .execute()
            )

        except Exception as exc:
            raise RuntimeError(
                f"Failed to list Google Calendar events: {exc}"
            ) from exc

        items = result.get("items", [])

        return [
            self._result_to_calendar_event(item)
            for item in items
        ]