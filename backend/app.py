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

import os
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

# Ensure project root is in sys.path so modules (config, agents, database, etc.) load regardless of cwd
_ROOT_DIR = Path(__file__).resolve().parent.parent
if str(_ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(_ROOT_DIR))
_BACKEND_DIR = Path(__file__).resolve().parent
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

# Centralized Settings & Tools
from config.settings import settings
from database.connection import (
    init_db,
    log_threat_event,
    log_alert,
    get_alert_logs,
    get_alert_log_by_provider_message_id,
    update_alert_status_by_provider_id,
    check_db_health,
)
from tools.farmer.farmer_db import default_farmer_db
from agents.orchestrator.graph import build_graph
from agents.sentinel.agent import SentinelAgent
from services.chat import build_grounded_reply
from services.monitoring import run_monitoring_cycle
from tools.weather.providers import WeatherProviderService
from tools.notifications.sms import verify_vonage_signature, parse_vonage_delivery_receipt

try:
    from .schemas import (
        HealthResponse,
        ReadinessResponse,
        CurrentWeatherResponse,
        PipelineRunRequest,
        PipelineRunResponse,
        FarmerListResponse,
        FarmerProfileResponse,
        FarmerDashboardResponse,
        AlertListResponse,
        AlertLogRecord,
        DeliveryReceiptResponse,
        ErrorResponse,
        ChatRequest,
        ChatResponse,
        ProviderStatusResponse,
        MonitoringRunResponse,
        VALID_MOCK_SCENARIOS,
        VALID_MODES,
    )
except (ImportError, ValueError):
    from schemas import (
        HealthResponse,
        ReadinessResponse,
        CurrentWeatherResponse,
        PipelineRunRequest,
        PipelineRunResponse,
        FarmerListResponse,
        FarmerProfileResponse,
        FarmerDashboardResponse,
        AlertListResponse,
        AlertLogRecord,
        DeliveryReceiptResponse,
        ErrorResponse,
        ChatRequest,
        ChatResponse,
        ProviderStatusResponse,
        MonitoringRunResponse,
        VALID_MOCK_SCENARIOS,
        VALID_MODES,
    )

# ---------------------------------------------------------------------------
# Strict CORS Allowed Origins (Local dev + configured production origins)
# ---------------------------------------------------------------------------
ALLOWED_DEV_ORIGINS: List[str] = [
    "http://localhost:3000",       # React / Next.js dev server
    "http://localhost:5173",       # Vite / Vue dev server
    "http://localhost:8000",       # Local testing / Docs
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:8000",
]


def get_allowed_cors_origins() -> List[str]:
    """
    Return combined list of local development origins and any production
    origins configured via the CORS_ORIGINS environment variable.
    """
    origins = list(ALLOWED_DEV_ORIGINS)
    custom_origins = getattr(settings.system, "cors_origins", "")
    if custom_origins:
        for org in custom_origins.split(","):
            org_clean = org.strip()
            if org_clean and org_clean not in origins:
                origins.append(org_clean)
    return origins


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


def handle_readiness(db_url: Optional[str] = None) -> Dict[str, Any]:
    """
    Comprehensive readiness probe verifying SQLite database connectivity and schema readiness.
    Used by container orchestrators (Kubernetes / Docker) and uptime monitors.
    """
    db_status = check_db_health(db_url)
    is_ready = db_status["connected"] and db_status["tables_ready"]
    return {
        "status": "ready" if is_ready else "not_ready",
        "database": db_status,
        "weather_mode": settings.system.weather_mode,
        "calendar_provider": settings.system.calendar_provider,
        "sms_enabled": settings.sms.sms_enabled,
        "sms_provider": settings.sms.sms_provider,
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
    initial_state = {
        "location": location,
        "mode": (mode or settings.system.weather_mode).strip().lower(),
        "mock_scenario": scenario,
    }
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


def handle_get_farmer(farmer_id: str) -> Dict[str, Any]:
    """
    Retrieve full farmer profile by farmer_id.
    Raises LookupError if farmer profile does not exist.
    """
    clean_id = (farmer_id or "").strip()
    if not clean_id:
        raise ValueError("Farmer ID must not be empty.")

    farmer = default_farmer_db.get_farmer_by_id(clean_id)
    if not farmer:
        raise LookupError(f"Farmer profile with ID '{clean_id}' not found.")
    return farmer


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


def handle_vonage_delivery_receipt(
    payload: Dict[str, Any],
    signature_secret: Optional[str] = None,
    signature_method: str = "sha256",
    db_url: Optional[str] = None,
    allow_unsigned_when_no_secret: bool = False,
) -> Dict[str, Any]:
    """
    Process an inbound Vonage Delivery Receipt (DLR) webhook callback.
    Validates signature using Vonage's official algorithm, matches alert by message ID, and updates status safely.
    In production, a configured signature secret is required; unsigned callbacks are rejected.
    """
    secret = signature_secret if signature_secret is not None else settings.credentials.vonage_signature_secret
    method = signature_method or settings.sms.vonage_signature_method

    # 1. Validate signature
    is_valid = verify_vonage_signature(
        params=payload,
        signature_secret=secret,
        method=method,
        allow_unsigned_when_no_secret=allow_unsigned_when_no_secret,
    )
    if not is_valid:
        raise PermissionError("Invalid webhook signature: callback verification failed.")


    # 2. Parse delivery receipt payload
    parsed = parse_vonage_delivery_receipt(payload)
    message_id = parsed.get("message_id")
    new_status = parsed.get("status", "unknown")
    error_message = parsed.get("error_message")
    timestamp = parsed.get("timestamp")

    if not message_id:
        return {
            "status": "ignored",
            "message_id": None,
            "delivery_status": new_status,
            "matched": False,
            "detail": "Delivery receipt payload missing messageId.",
        }

    # 3. Check for existing audit record
    existing_record = get_alert_log_by_provider_message_id(message_id, db_url=db_url)
    if not existing_record:
        return {
            "status": "unmatched",
            "message_id": message_id,
            "delivery_status": new_status,
            "matched": False,
            "detail": f"No alert record found matching provider message ID '{message_id}'.",
        }

    # 4. Idempotent update: check if already in terminal state
    current_status = str(existing_record.get("status", "")).strip().lower()
    if current_status == new_status:
        return {
            "status": "ignored",
            "message_id": message_id,
            "delivery_status": new_status,
            "matched": True,
            "detail": f"Alert record is already in status '{new_status}'.",
        }

    # 5. Update SQLite audit record
    updated = update_alert_status_by_provider_id(
        provider_message_id=message_id,
        new_status=new_status,
        error_message=error_message,
        timestamp=timestamp,
        db_url=db_url,
    )

    return {
        "status": "updated" if updated else "failed",
        "message_id": message_id,
        "delivery_status": new_status,
        "matched": True,
        "detail": f"Alert audit record status updated to '{new_status}'.",
    }


def handle_provider_weather(location: str) -> Dict[str, Any]:
    """Fetch a normalized provider response with honest verification metadata."""
    clean_location = (location or "").strip()
    if len(clean_location) < 2:
        raise ValueError("Location query parameter must be at least 2 characters.")
    return WeatherProviderService().fetch(clean_location)


def handle_chat(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Build a grounded response from structured weather facts and farmer profile."""
    farmer_id = payload.get("farmer_id")
    farmer = None
    if farmer_id and str(farmer_id).strip():
        farmer = default_farmer_db.get_farmer_by_id(str(farmer_id).strip())

    loc = payload.get("location")
    if (not loc or loc == "Jalandhar") and farmer and farmer.get("location"):
        loc = farmer["location"]

    weather = handle_current_weather(
        location=loc,
        mode=payload.get("mode"),
        scenario=payload.get("scenario"),
    )
    return build_grounded_reply(
        message=payload["message"],
        weather=weather,
        farmer=farmer,
        language=payload.get("language") or "en",
    )


def handle_monitoring_run(mode: str = "mock") -> Dict[str, Any]:
    """Run a manual monitoring cycle; scheduling is intentionally opt-in."""
    normalized_mode = (mode or "mock").strip().lower()
    if normalized_mode not in VALID_MODES:
        raise ValueError("mode must be 'mock' or 'live'.")
    farmers = default_farmer_db.get_all_farmers()
    return run_monitoring_cycle(farmers, handle_pipeline_run, mode=normalized_mode)


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

    import logging
    import hmac

    logger = logging.getLogger("weathergpt.api")

    # 1. CORS Middleware supporting local development and deployed Vercel apps
    api_app.add_middleware(
        CORSMiddleware,
        allow_origins=get_allowed_cors_origins(),
        allow_origin_regex=r"https://.*\.vercel\.app",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 2. Production API Key Authentication Middleware
    @api_app.middleware("http")
    async def api_key_auth_middleware(request: Request, call_next):
        """
        Protects sensitive endpoints (/api/farmers, /api/alerts) when API_KEY is configured in the environment.
        Public endpoints (health, readiness, docs, webhooks) remain unauthenticated.
        Uses constant-time string comparison to prevent timing attacks.
        """
        path = request.url.path
        configured_api_key = (getattr(settings.system, "api_key", None) or os.getenv("API_KEY", "")).strip()

        # Only protect farmer and alert endpoints if an API_KEY is configured
        is_protected = (
            path.startswith("/api/farmers") or path == "/api/alerts" or path.startswith("/api/alerts/")
        )

        if is_protected and configured_api_key:
            # Check X-API-Key header or Authorization: Bearer <key>
            header_key = request.headers.get("x-api-key", "").strip()
            if not header_key:
                auth_header = request.headers.get("authorization", "").strip()
                if auth_header.lower().startswith("bearer "):
                    header_key = auth_header[7:].strip()

            if not header_key or not hmac.compare_digest(header_key, configured_api_key):
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={
                        "error": "Unauthorized",
                        "detail": "Invalid or missing API key. Provide valid credentials via X-API-Key or Authorization header.",
                        "status_code": 401
                    }
                )

        return await call_next(request)

    # 3. Global Error Handlers for Clean JSON Responses
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
        # Log full internal exception and traceback securely on server side
        logger.error(f"Internal server error processing {request.method} {request.url.path}: {exc}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal Server Error",
                "detail": "An internal server error occurred. Please contact the system administrator.",
                "status_code": 500
            }
        )

    # 4. Route Definitions
    @api_app.get(
        "/api/health",
        response_model=HealthResponse,
        summary="System Health & Mode",
        tags=["System"]
    )
    def get_health():
        return handle_health()

    @api_app.get(
        "/api/ready",
        response_model=ReadinessResponse,
        summary="System Readiness Probe",
        tags=["System"]
    )
    def get_readiness():
        readiness = handle_readiness()
        if readiness["status"] != "ready":
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content=readiness
            )
        return readiness

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
        except TimeoutError as e:
            raise HTTPException(status_code=504, detail=f"Weather provider timed out: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Weather ingestion failed: {str(e)}")

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
        except TimeoutError as e:
            raise HTTPException(status_code=504, detail=f"Pipeline weather provider timed out: {str(e)}")
        except Exception as e:
            logger.error(f"Pipeline execution failed: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="An error occurred during pipeline execution.")

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
        "/api/farmers/{farmer_id}",
        response_model=FarmerProfileResponse,
        summary="Get Farmer Profile by ID",
        tags=["Farmers"]
    )
    def get_farmer(
        farmer_id: str = Path(..., description="Unique farmer identifier (e.g. F001)")
    ):
        try:
            return handle_get_farmer(farmer_id=farmer_id)
        except LookupError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"Failed to retrieve farmer profile: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="An error occurred while retrieving the farmer profile.")

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
            logger.error(f"Failed to generate farmer dashboard: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="An error occurred while generating the farmer dashboard.")

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

    @api_app.post(
        "/api/webhooks/vonage/delivery-receipt",
        response_model=DeliveryReceiptResponse,
        summary="Vonage SMS Delivery Receipt (DLR) Webhook",
        tags=["Alerts"],
    )
    async def vonage_delivery_receipt_webhook(request: Request):
        """
        Secure callback receiving Vonage SMS delivery status updates.
        Validates cryptographic signatures when configured and safely updates audit logs.
        """
        # Parse payload from either JSON body or form/query params (Vonage supports both)
        payload: Dict[str, Any] = {}
        content_type = request.headers.get("content-type", "").lower()

        if "application/json" in content_type:
            try:
                payload = await request.json()
            except Exception:
                payload = {}
        else:
            try:
                form = await request.form()
                payload = dict(form)
            except Exception:
                pass

        # Merge with query parameters if present (Vonage GET/POST query fallback)
        if request.query_params:
            for k, v in request.query_params.items():
                if k not in payload:
                    payload[k] = v

        try:
            return handle_vonage_delivery_receipt(payload)
        except PermissionError as exc:
            raise HTTPException(status_code=401, detail=str(exc))
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        except Exception as exc:
            logger.error(f"Delivery receipt processing failed: {exc}", exc_info=True)
            raise HTTPException(status_code=500, detail="An error occurred while processing the delivery receipt.")


    @api_app.get(
        "/api/weather/providers",
        response_model=ProviderStatusResponse,
        summary="Live provider response and verification status",
        tags=["Weather"],
    )
    def get_provider_weather(location: str = Query("Jalandhar", description="Target location name")):
        try:
            return handle_provider_weather(location)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        except TimeoutError as exc:
            raise HTTPException(status_code=504, detail=f"Weather provider timed out: {str(exc)}")
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"Weather provider failed: {str(exc)}")

    @api_app.post(
        "/api/chat",
        response_model=ChatResponse,
        summary="Grounded farming advisory",
        tags=["Conversation"],
    )
    def chat(payload: ChatRequest):
        try:
            return handle_chat(payload.model_dump())
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        except TimeoutError as exc:
            raise HTTPException(status_code=504, detail=f"Weather provider timed out: {str(exc)}")
        except Exception as exc:
            logger.error(f"Chat advisory failed: {exc}", exc_info=True)
            raise HTTPException(status_code=500, detail="An error occurred while generating the farming advisory.")

    @api_app.post(
        "/api/monitor/run",
        response_model=MonitoringRunResponse,
        summary="Run one farmer monitoring cycle",
        tags=["Monitoring"],
    )
    def run_monitoring(mode: str = Query("mock", description="mock or live weather mode")):
        try:
            return handle_monitoring_run(mode)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        except TimeoutError as exc:
            raise HTTPException(status_code=504, detail=f"Weather provider timed out: {str(exc)}")
        except Exception as exc:
            logger.error(f"Monitoring cycle failed: {exc}", exc_info=True)
            raise HTTPException(status_code=500, detail="An error occurred during the monitoring cycle.")

    return api_app


# Instantiate application
app = create_app()
