from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend.schemas import ChatApiRequest, ChatApiResponse
from services.chat import build_grounded_reply
from services.monitoring import get_system_health

app = FastAPI(
    title="WeatherGPT Backend API",
    description="Conversational AI + Radio-GPT Hybrid Engine for Disaster Management",
    version="1.0.0",
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "status": "online",
        "service": "WeatherGPT API Engine",
        "endpoints": ["/api/chat", "/health"],
    }


@app.get("/health")
@app.get("/api/health")
def health_check():
    return get_system_health()


@app.post("/api/chat", response_model=ChatApiResponse)
def chat_endpoint(request: ChatApiRequest) -> ChatApiResponse:
    """
    Conversational endpoint:
    Processes user query using ConversationalService intelligence layer.
    """
    try:
        return build_grounded_reply(request)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
