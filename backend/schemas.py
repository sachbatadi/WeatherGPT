from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ChatApiRequest(BaseModel):
    """API request model for POST /api/chat."""
    message: str
    location: Optional[str] = None
    farmer_id: Optional[str] = None
    crop: Optional[str] = None
    language: Optional[str] = None
    mode: Optional[str] = "mock"
    scenario: Optional[str] = None
    conversation_id: Optional[str] = "default"


class ChatApiResponse(BaseModel):
    """API response model for POST /api/chat."""
    reply: str
    intent: str
    grounding: str
    llm_used: Optional[str] = None
    location: Optional[str] = None
    data_source: str = "WeatherGPT Engine"
    agent_used: Optional[str] = None
    actions: List[str] = Field(default_factory=list)
    confidence: float = 1.0
    language: str = "en"
    raw_data: Optional[Dict[str, Any]] = None
