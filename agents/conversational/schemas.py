from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class IntentType(str, Enum):
    WEATHER = "weather"
    FORECAST = "forecast"
    WARNING = "warning"
    AGRICULTURE = "agriculture"
    AGRICULTURE_EXPLANATION = "agriculture_explanation"
    CLIMATE = "climate"
    EMERGENCY = "emergency"
    GENERAL_WEATHER = "general_weather"
    UNKNOWN = "unknown"


class ExtractedEntities(BaseModel):
    location: Optional[str] = None
    time_reference: Optional[str] = None
    crop: Optional[str] = None
    farmer_id: Optional[str] = None
    language: str = "en"
    confidence: float = 1.0
    custom_entities: Dict[str, Any] = Field(default_factory=dict)


class ConversationalQuery(BaseModel):
    query: str
    intent: IntentType
    location: Optional[str] = None
    time_reference: Optional[str] = None
    crop: Optional[str] = None
    farmer_id: Optional[str] = None
    language: str = "en"
    confidence: float = 1.0
    entities: Dict[str, Any] = Field(default_factory=dict)
    requires_agent: bool = False
    requires_weather_data: bool = False
    requires_historical_data: bool = False


class ConversationContext(BaseModel):
    session_id: str = "default"
    current_location: Optional[str] = None
    current_crop: Optional[str] = None
    current_farmer_id: Optional[str] = None
    last_intent: Optional[IntentType] = None
    last_time_reference: Optional[str] = None
    last_weather_context: Optional[Dict[str, Any]] = None
    history: List[Dict[str, Any]] = Field(default_factory=list)

    def update(
        self,
        query: ConversationalQuery,
        weather_data: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Update context from a processed query."""
        if query.location:
            self.current_location = query.location
        if query.crop:
            self.current_crop = query.crop
        if query.farmer_id:
            self.current_farmer_id = query.farmer_id
        if query.time_reference:
            self.last_time_reference = query.time_reference
        if query.intent != IntentType.UNKNOWN:
            self.last_intent = query.intent
        if weather_data:
            self.last_weather_context = weather_data


class ChatRequest(BaseModel):
    message: str
    location: Optional[str] = None
    farmer_id: Optional[str] = None
    crop: Optional[str] = None
    language: Optional[str] = None
    conversation_id: Optional[str] = "default"


class GroundedResponse(BaseModel):
    text: str
    data_source: str
    agent_used: Optional[str] = None
    raw_data: Optional[Dict[str, Any]] = None
    actions: List[str] = Field(default_factory=list)
    reasoning: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    intent: IntentType
    location: Optional[str] = None
    data_source: str = "WeatherGPT Engine"
    agent_used: Optional[str] = None
    actions: List[str] = Field(default_factory=list)
    confidence: float = 1.0
    language: str = "en"
    raw_data: Optional[Dict[str, Any]] = None
