from typing import Dict, Optional

from .schemas import ConversationContext, ConversationalQuery


class ContextManager:
    """
    Manages lightweight conversation memory across multi-turn interactions.
    Tracks active location, crop, farmer ID, last intent, and time references.
    """

    def __init__(self):
        self._sessions: Dict[str, ConversationContext] = {}

    def get_or_create_context(self, session_id: str = "default") -> ConversationContext:
        """Fetch existing session context or create a new one."""
        if session_id not in self._sessions:
            self._sessions[session_id] = ConversationContext(session_id=session_id)
        return self._sessions[session_id]

    def resolve_query(
        self,
        query: ConversationalQuery,
        session_id: str = "default",
    ) -> ConversationalQuery:
        """
        Enrich a query using stored context entities (e.g. resolving implicit locations).
        """
        context = self.get_or_create_context(session_id)

        resolved_location = query.location or context.current_location or "Jalandhar"
        resolved_crop = query.crop or context.current_crop
        resolved_farmer_id = query.farmer_id or context.current_farmer_id

        # Return updated query copy with resolved contextual entities
        updated_entities = dict(query.entities)
        updated_entities["location"] = resolved_location
        if resolved_crop:
            updated_entities["crop"] = resolved_crop
        if resolved_farmer_id:
            updated_entities["farmer_id"] = resolved_farmer_id

        return ConversationalQuery(
            query=query.query,
            intent=query.intent,
            location=resolved_location,
            time_reference=query.time_reference or context.last_time_reference,
            crop=resolved_crop,
            farmer_id=resolved_farmer_id,
            language=query.language,
            confidence=query.confidence,
            entities=updated_entities,
            requires_agent=query.requires_agent,
            requires_weather_data=query.requires_weather_data,
            requires_historical_data=query.requires_historical_data,
        )

    def update(
        self,
        session_id: str,
        query: ConversationalQuery,
        weather_data: Optional[Dict] = None,
    ) -> None:
        """Update context with processed query and weather data."""
        context = self.get_or_create_context(session_id)
        context.update(query, weather_data)
        context.history.append({
            "query": query.query,
            "intent": query.intent.value if hasattr(query.intent, "value") else str(query.intent),
            "location": query.location,
            "crop": query.crop,
            "farmer_id": query.farmer_id,
            "time_reference": query.time_reference,
        })

    def clear(self, session_id: str = "default") -> None:
        """Clear memory for a given session ID."""
        if session_id in self._sessions:
            del self._sessions[session_id]
