import os
from typing import Optional

from agents.conversational.schemas import ChatRequest
from agents.conversational.service import ConversationalService
from backend.schemas import ChatApiRequest, ChatApiResponse

# Global singleton instance of ConversationalService
_conversational_service: Optional[ConversationalService] = None


def get_conversational_service() -> ConversationalService:
    """Retrieve or initialize the global ConversationalService instance."""
    global _conversational_service
    if _conversational_service is None:
        _conversational_service = ConversationalService()
    return _conversational_service


def build_grounded_reply(request: ChatApiRequest) -> ChatApiResponse:
    """
    Bridge adapter connecting the FastAPI endpoint (POST /api/chat)
    directly to the Conversational Intelligence Layer (ConversationalService).
    """
    if request.mode:
        os.environ["WEATHER_MODE"] = request.mode.strip().lower()

    service = get_conversational_service()

    # Map FastAPI request into ConversationalService ChatRequest
    chat_req = ChatRequest(
        message=request.message,
        location=request.location,
        farmer_id=request.farmer_id,
        crop=request.crop,
        language=request.language,
        conversation_id=request.conversation_id or "default",
    )

    # Process through ConversationalService (single source of truth)
    res = service.process_query(chat_req)

    intent_str = res.intent.value if hasattr(res.intent, "value") else str(res.intent)

    # Return backwards-compatible ChatApiResponse
    return ChatApiResponse(
        reply=res.response,
        intent=intent_str,
        grounding=res.data_source,
        llm_used=res.agent_used,
        location=res.location,
        data_source=res.data_source,
        agent_used=res.agent_used,
        actions=res.actions,
        confidence=res.confidence,
        language=res.language,
        raw_data=res.raw_data,
    )
