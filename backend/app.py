"""
WeatherGPT FastAPI Web Application (backend/app.py).

Exposes 6 REST API endpoints:
1. GET  /api/health                     - System health & mode status
2. GET  /api/weather/current            - Normalized weather & hazard detection
3. POST /api/pipeline/run               - End-to-end agentic workflow execution
4. GET  /api/farmers                    - List farmer profiles (with location filter)
5. GET  /api/farmers/{id}/dashboard     - Farmer dashboard summary card & plan
6. GET  /api/alerts                     - Dispatched notification audit logs
"""

from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

# Centralized Settings & Tools
from config.settings import settings
from database.connection import init_db, log_threat_event, log_alert, get_alert_logs
from tools.farmer.farmer_db import default_farmer_db
from agents.orchestrator.graph import build_graph
from agents.sentinel.agent import SentinelAgent

from .schemas import (
    HealthResponse,
    CurrentWeatherResponse,
    PipelineRunRequest,
    PipelineRunResponse,
    FarmerListResponse,
    FarmerProfileResponse,
    FarmerDashboardResponse,
    AlertListResponse,
    AlertLogRecord,
    ErrorResponse,
    VALID_MOCK_SCENARIOS,
    VALID_MODES,
)

# ---------------------------------------------------------------------------
# Strict CORS Allowed Origins (Local frontend dev only - No wildcard "*")
# ---------------------------------------------------------------------------
ALLOWED_DEV_ORIGINS: List[str] = [
    "http://localhost:3000",       # React / Next.js dev server
    "http://localhost:5173",       # Vite / Vue dev server
    "http://localhost:8000",       # Local testing / Docs
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:8000",
]


# ---------------------------------------------------------------------------
# Core Handler Logic (Reusable for both FastAPI routes and direct testing)
# ---------------------------------------------------------------------------

def handle_health() -> Dict[str, Any]:
    """Return system health status and configuration toggles."""
    return {
        "status": "healthy",
        "weather_mode": settings.system.weather_mode,
        "calendar_provider": settings.system.calendar_provider,
        "default_location": settings.system.default_location,
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def handle_current_weather(
    location: Optional[str] = None,
    mode: Optional[str] = None,
    scenario: Optional[str] = None
) -> Dict[str, Any]:
    """
    Fetch normalized weather telemetry and evaluate hazard detection for location.
    Does NOT call external weather APIs if mode is 'mock' or if invalid.
    """
    target_loc = (location or settings.system.default_location).strip()
    if not target_loc or len(target_loc) < 2:
        raise ValueError("Location query parameter must be a non-empty string with at least 2 characters.")

    target_mode = (mode or settings.system.weather_mode).strip().lower()
    if target_mode not in VALID_MODES:
        raise ValueError(f"Invalid mode '{mode}'. Must be 'mock' or 'live'.")

    target_scenario = scenario or ("heavy_rain" if target_mode == "mock" else None)
    if target_scenario and target_scenario not in VALID_MOCK_SCENARIOS:
        raise ValueError(f"Invalid scenario '{scenario}'. Must be one of: {sorted(VALID_MOCK_SCENARIOS)}")

    agent = SentinelAgent()
    output = agent.observe_and_detect(
        location=target_loc,
        mode=target_mode,
        mock_scenario=target_scenario
    )

    current_data = output.weather_data.get("current", {})
    threat = output.threat

    return {
        "location": target_loc,
        "source": output.weather_data.get("source", "mock"),
        "temperature_c": float(current_data.get("temperature_c") or threat.temp_c or 25.0),
        "humidity_pct": float(current_data.get("humidity_pct") or threat.humidity_pct or 60.0),
        "precipitation_mm": float(current_data.get("precipitation_mm") or threat.rainfall_mm or 0.0),
        "wind_speed_kmh": float(current_data.get("wind_speed_kmh") or threat.wind_speed_kmh or 0.0),
        "wind_gust_kmh": float(current_data.get("wind_gust_kmh") or threat.wind_gust_kmh or 0.0) if current_data.get("wind_gust_kmh") or threat.wind_gust_kmh else None,
        "threat_detected": output.threat_detected,
        "threat_type": threat.event_type if output.threat_detected else "none",
        "threat_severity": threat.severity,
        "confidence": threat.confidence,
        "confidence_reason": threat.confidence_reason,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def handle_pipeline_run(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute full LangGraph agent workflow:
    Sentinel (Observe) -> Strategist (Assess & Plan) -> Executor (Dispatch & Sync)
    Persists threat events and alert receipts into local SQLite database.
    """
    location = str(request_data.get("location") or "Jalandhar").strip()
    if not location or len(location) < 2:
        raise ValueError("Location must be a non-empty string with at least 2 characters.")

    mode = request_data.get("mode")
    if mode and mode.lower() not in VALID_MODES:
        raise ValueError(f"Invalid mode '{mode}'. Must be 'mock' or 'live'.")

    scenario = request_data.get("scenario")
    if scenario and scenario.lower() not in VALID_MOCK_SCENARIOS:
        raise ValueError(f"Invalid scenario '{scenario}'. Must be one of: {sorted(VALID_MOCK_SCENARIOS)}")

    # Execute compiled LangGraph workflow
    graph = build_graph()
    initial_state = {"location": location}
    result = graph.invoke(initial_state)

    threat_dict = result.get("threat", {})
    audit_id = None

    # Persist threat audit log if a threat was detected
    if result.get("threat_detected") and threat_dict:
        try:
            audit_id = log_threat_event(threat_dict)
        except Exception:
            pass

    # Persist dispatched alert records if any were created
    dispatched = result.get("dispatched_alerts", [])
    for alert in dispatched:
        try:
            log_alert(alert)
        except Exception:
            pass

    return {
        "status": "completed",
        "location": location,
        "threat_detected": bool(result.get("threat_detected", False)),
        "threat": threat_dict if result.get("threat_detected") else None,
        "risk_level": result.get("risk_level"),
        "alert_required": bool(result.get("alert_required", False)),
        "replanning_required": bool(result.get("replanning_required", False)),
        "affected_farmers": result.get("affected_farmers", []),
        "recommended_actions": result.get("recommended_actions", []),
        "execution_summary": result.get("execution_summary"),
        "audit_event_id": audit_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def handle_get_farmers(location: Optional[str] = None) -> Dict[str, Any]:
    """Retrieve all farmers or filter by location."""
    if location and location.strip():
        farmers = default_farmer_db.get_farmers_by_location(location.strip())
    else:
        farmers = default_farmer_db.get_all_farmers()

    return {
        "total_count": len(farmers),
        "farmers": farmers,
    }


def handle_get_farmer_dashboard(farmer_id: str) -> Dict[str, Any]:
    """
    Retrieve structured farmer summary card, active schedule, and risk badge.
    Raises LookupError if farmer profile does not exist.
    """
    clean_id = (farmer_id or "").strip()
    if not clean_id:
        raise ValueError("Farmer ID must not be empty.")

    farmer = default_farmer_db.get_farmer_by_id(clean_id)
    if not farmer:
        raise LookupError(f"Farmer profile with ID '{clean_id}' not found.")

    # Determine badge color and risk status from farm plan
    current_plan = farmer.get("current_plan", [])
    has_postponed = any(a.get("status") == "postponed" for a in current_plan)
    has_cancelled = any(a.get("status") == "cancelled" for a in current_plan)

    if has_cancelled:
        risk_level = "critical"
        badge_color = "red"
    elif has_postponed:
        risk_level = "high"
        badge_color = "orange"
    else:
        risk_level = "low"
        badge_color = "green"

    # Query recent alert history from SQLite
    recent_alerts = []
    try:
        recent_alerts = get_alert_logs(farmer_id=clean_id, limit=5)
    except Exception:
        pass

    return {
        "farmer_id": farmer["farmer_id"],
        "name": farmer["name"],
        "phone": farmer.get("phone"),
        "language": farmer.get("language", "en"),
        "location": farmer["location"],
        "crop": farmer["crop"],
        "crop_stage": farmer["crop_stage"],
        "soil_type": farmer.get("soil_type", "loamy"),
        "irrigation_method": farmer.get("irrigation_method", "flood"),
        "risk_level": risk_level,
        "badge_color": badge_color,
        "active_plan_count": len(current_plan),
        "scheduled_activities": current_plan,
        "recent_alerts": recent_alerts,
    }


def handle_get_alerts(farmer_id: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
    """Fetch recent alert records from SQLite persistence layer."""
    clean_fid = farmer_id.strip() if farmer_id and farmer_id.strip() else None
    capped_limit = max(1, min(100, limit))

    logs = get_alert_logs(farmer_id=clean_fid, limit=capped_limit)
    return {
        "total_count": len(logs),
        "alerts": logs,
    }


# ---------------------------------------------------------------------------
# FastAPI Application & Router Initialization
# ---------------------------------------------------------------------------

try:
    from fastapi import FastAPI, HTTPException, Query, Path, Request, status
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse
    from fastapi.exceptions import RequestValidationError
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False


def create_app() -> Any:
    """FastAPI application factory with strict CORS and structured JSON errors."""
    if not HAS_FASTAPI:
        # Return lightweight placeholder object if fastapi is not yet installed
        class DummyApp:
            title = "WeatherGPT API"
        return DummyApp()

    api_app = FastAPI(
        title="WeatherGPT API",
        description="Agentic AI-powered agricultural weather intelligence and disaster management REST API.",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )

    # 1. Strict CORS Middleware for local development addresses only
    api_app.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_DEV_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

    # 2. Global Error Handlers for Clean JSON Responses
    @api_app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": "Validation Error",
                "detail": str(exc.errors()[0]["msg"] if exc.errors() else "Invalid request payload"),
                "status_code": 422
            }
        )

    @api_app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": "Request Failed",
                "detail": exc.detail,
                "status_code": exc.status_code
            }
        )

    @api_app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal Server Error",
                "detail": str(exc),
                "status_code": 500
            }
        )

    # 3. Route Definitions
    @api_app.get(
        "/api/health",
        response_model=HealthResponse,
        summary="System Health & Mode",
        tags=["System"]
    )
    def get_health():
        return handle_health()

    @api_app.get(
        "/api/weather/current",
        response_model=CurrentWeatherResponse,
        summary="Current Weather & Hazard Evaluation",
        tags=["Weather"]
    )
    def get_current_weather(
        location: str = Query("Jalandhar", description="Target location name"),
        mode: Optional[str] = Query(None, description="Ingestion mode: 'mock' or 'live'"),
        scenario: Optional[str] = Query(None, description="Optional SIH disaster scenario preset")
    ):
        try:
            return handle_current_weather(location=location, mode=mode, scenario=scenario)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Weather ingestion failed: {str(e)}")

    @api_app.post(
        "/api/pipeline/run",
        response_model=PipelineRunResponse,
        summary="Run End-to-End Agent Workflow",
        tags=["Pipeline"]
    )
    def run_pipeline(payload: PipelineRunRequest):
        try:
            return handle_pipeline_run(payload.model_dump())
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Pipeline execution failed: {str(e)}")

    @api_app.get(
        "/api/farmers",
        response_model=FarmerListResponse,
        summary="List Registered Farmers",
        tags=["Farmers"]
    )
    def get_farmers(
        location: Optional[str] = Query(None, description="Filter by location/district/state")
    ):
        return handle_get_farmers(location=location)

    @api_app.get(
        "/api/farmers/{farmer_id}/dashboard",
        response_model=FarmerDashboardResponse,
        summary="Farmer Summary Card & Plan",
        tags=["Farmers"]
    )
    def get_farmer_dashboard(
        farmer_id: str = Path(..., description="Unique farmer identifier (e.g. F001)")
    ):
        try:
            return handle_get_farmer_dashboard(farmer_id=farmer_id)
        except LookupError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @api_app.get(
        "/api/alerts",
        response_model=AlertListResponse,
        summary="Dispatched Alert Audit Logs",
        tags=["Alerts"]
    )
    def get_alerts(
        farmer_id: Optional[str] = Query(None, description="Filter alerts by farmer ID"),
        limit: int = Query(50, ge=1, le=100, description="Max records to return")
    ):
        return handle_get_alerts(farmer_id=farmer_id, limit=limit)

    return api_app


# Instantiate application
app = create_app()
