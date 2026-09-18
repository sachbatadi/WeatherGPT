# WeatherGPT Developer Handoff Guide

Welcome to WeatherGPT! This document summarizes the project architecture, currently completed backend & agent services, available REST API contracts, and suggested next steps for frontend and agent expansion.

---

## 1. Project Overview

WeatherGPT is an agentic, explainable agricultural weather intelligence and disaster-alert system designed for farmers in Punjab, Haryana, and across India. It evaluates real-time and mock meteorological conditions against strict agronomic thresholds, determines localized crop risks, reformulates farm activity calendars, and dispatches localized alerts via SMS and Radio GPT voice scripts in Punjabi, Hindi, and English.

---

## 2. Completed Architecture & Backend Work

### A. Core Multi-Agent Workflow (`agents/`)
- **Sentinel Agent (`agents/sentinel/`):** Ingests weather telemetry (from Open-Meteo live API or SIH disaster presets like heavy rain, high wind, extreme heat, and frost). Evaluates agricultural safety thresholds and outputs structured `ThreatEvent` payloads with confidence ratings.
- **Strategist Agent (`agents/strategist/`):** Evaluates threat events against individual farmer profiles (crop, growth stage, soil type, irrigation method). Assesses risk scores (0–100) and formulates emergency farm interventions.
- **Executor Agent (`agents/executor/`):** Reschedules affected farm activities (e.g. halts chemical spraying or postpones irrigation) and queues/dispatches multilingual alerts with idempotency protection.
- **Orchestrator Graph (`agents/orchestrator/`):** State graph coordinating the complete Sentinel $\to$ Strategist $\to$ Executor pipeline.

### B. REST API Layer (`backend/app.py` & `backend/schemas.py`)
FastAPI application with strict CORS, structured Pydantic validation, safe error handling (no stack traces leaked in 500 errors), and optional API key middleware:

| Endpoint | Method | Description | Auth Required? |
|---|---|---|---|
| `/api/health` | `GET` | System health, version, and execution modes | Public |
| `/api/ready` | `GET` | Comprehensive readiness probe checking SQLite connectivity and schema | Public |
| `/api/weather/current` | `GET` | Normalized weather data & hazard detection (`location`, `mode`, `scenario`) | Public |
| `/api/weather/providers`| `GET` | Multi-source weather consensus (live Open-Meteo) | Public |
| `/api/pipeline/run` | `POST` | Triggers the complete end-to-end multi-agent workflow | Public |
| `/api/farmers` | `GET` | List registered farmer profiles with location filtering | Protected (if `API_KEY` set) |
| `/api/farmers/{id}` | `GET` | Retrieve individual farmer profile | Protected (if `API_KEY` set) |
| `/api/farmers/{id}/dashboard` | `GET` | Farmer summary card, risk badge, and scheduled calendar plan | Protected (if `API_KEY` set) |
| `/api/alerts` | `GET` | Dispatched notification audit logs | Protected (if `API_KEY` set) |
| `/api/chat` | `POST` | Grounded agronomic conversational advisory (strictly deterministic facts) | Public |
| `/api/monitor/run` | `POST` | Manual monitoring cycle across registered farmers | Public |
| `/api/webhooks/vonage/delivery-receipt` | `POST` | Inbound Vonage delivery receipt handler with cryptographic signature verification | Vonage Webhook Signature |

### C. Outbound SMS & Webhooks (`tools/notifications/sms.py`)
- Provider pattern supporting `mock` (safe local default) and `vonage` (live Vonage SMS REST API).
- International E.164 phone normalization (e.g. `+91-9876543210` $\to$ `919876543210`).
- Duplicate-send prevention via in-memory idempotency cache.
- Official Vonage webhook signature verification supporting leading `&`, parameter sorting, `&`/`=` sanitization, and SHA-256 / SHA-512 / MD5 HMAC digests.

### D. SQLite Persistence (`database/`)
- Database connection management in `database/connection.py`.
- Tables: `farmers`, `farm_activities`, `threat_event_logs`, `alert_logs`.
- Persistent Docker volume mapping in `docker-compose.yml`.

### E. Test Suite (`tests/`)
- Complete pytest test suite with **107 passing tests** covering Sentinel, Strategist, Orchestrator, Database, API, Vonage SMS, and Delivery Receipts.

---

## 3. Unfinished / Next Step Work for Frontend & Integration

### A. Frontend Application (`frontend/`)
The `frontend/` folder has been restored to a clean state with `frontend/.gitkeep`.
1. **Initialize Frontend Framework:**
   - Initialize a modern React/Vite/TypeScript or Next.js application inside `frontend/`.
   - Setup styling (TailwindCSS or Vanilla CSS / styled-components).
2. **Build User Interfaces:**
   - **Operations & Weather Dashboard:** Live radar / telemetry card fetching `GET /api/weather/current` and `GET /api/weather/providers`.
   - **Disaster Simulation Console:** Control panel to run `POST /api/pipeline/run` with SIH scenarios (`heavy_rain`, `high_wind`, `extreme_heat`, `frost`).
   - **Farmer Profile & Plan View:** View farmer cards from `GET /api/farmers` and dynamic dashboard summary cards from `GET /api/farmers/{id}/dashboard`.
   - **Alert Log Stream:** Real-time table viewing dispatches from `GET /api/alerts`.
   - **Farmer Advisory Chat:** Chat interface connected to `POST /api/chat`.

### B. Agent & Data Enhancements
1. **India Meteorological Department (IMD) Adapter:**
   - `tools/weather/providers.py` contains a reserved `IMDProvider` stub. If official IMD API credentials become available, implement the authorized adapter.
2. **Persistent Audio Generation for Radio GPT:**
   - The strategist currently generates multilingual scripts (`agents/strategist/schemas.py`). Integrate a text-to-speech engine (e.g. Google Cloud TTS or ElevenLabs) to synthesize MP3/WAV audio alerts for illiterate farmers.
3. **Automated Scheduler:**
   - `services/monitoring.py` supports running monitoring cycles on demand. A lightweight cron or Celery/APScheduler task can invoke `handle_monitoring_run` periodically.

---

## 4. How to Run Locally

### Start Backend
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn backend.app:app --reload --port 8000
```

### Run Tests
```bash
PYTHONPATH=. pytest -v
```

### Run via Docker Compose
```bash
docker compose up -d --build
```
Check health:
```bash
curl http://127.0.0.1:8000/api/ready
```
