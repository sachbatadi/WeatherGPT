from typing import Optional

from .context import ContextManager
from .intent import QueryUnderstanding
from .response import ResponseGenerator
from .router import QueryRouter
from .schemas import ChatRequest, ChatResponse, ConversationalQuery, GroundedResponse


class ConversationalService:
    """
    Main entry-point for the Conversational WeatherGPT layer.
    Exposes clean service methods compatible with backend/API integration (e.g. POST /chat).
    """

    def __init__(
        self,
        query_understanding: Optional[QueryUnderstanding] = None,
        context_manager: Optional[ContextManager] = None,
        query_router: Optional[QueryRouter] = None,
        response_generator: Optional[ResponseGenerator] = None,
    ):
        self.understanding = query_understanding or QueryUnderstanding()
        self.context = context_manager or ContextManager()
        self.router = query_router or QueryRouter()
        self.generator = response_generator or ResponseGenerator()

    def process_query(self, request: ChatRequest) -> ChatResponse:
        """
        Process a ChatRequest end-to-end:
        1. Parse intent & entities
        2. Resolve implicit conversational context (multi-turn memory)
        3. Route query to tool/agent
        4. Generate grounded multi-lingual response
        5. Update context memory
        """
        parsed = self.understanding.parse(
            query=request.message,
            override_location=request.location,
            override_farmer_id=request.farmer_id,
            override_crop=request.crop,
            override_language=request.language,
        )

        session_id = request.conversation_id or "default"
        resolved = self.context.resolve_query(parsed, session_id=session_id)

        grounded = self.router.route(resolved)

        chat_response = self.generator.generate(grounded, resolved)

        self.context.update(
            session_id=session_id,
            query=resolved,
            weather_data=grounded.raw_data,
        )

        return chat_response
