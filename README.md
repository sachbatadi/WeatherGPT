# WeatherGPT

Agentic, explainable agricultural weather intelligence and disaster-alert system.

## Run locally

### Backend Setup (FastAPI & Agent System)

```bash
# 1. Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure local environment
cp .env.example .env

# 4. Start backend API server
uvicorn backend.app:app --reload --port 8000
```

Open http://127.0.0.1:8000/docs for the interactive Swagger/OpenAPI documentation.

### Frontend Setup

The repository provides a clean `frontend/` directory ready for modern SPA development (React, Vite, Next.js, or Vue) connecting to the backend REST API:

```bash
cd frontend
# If initializing with Vite/React:
npm create vite@latest . -- --template react-ts
npm install
npm run dev
```

The frontend can consume backend endpoints at `http://127.0.0.1:8000/api/*`. If hosting frontend on a custom domain/port (e.g. `http://localhost:5173`), configure `CORS_ORIGINS` in `.env`.

## Demo endpoints

- `GET /api/health`
- `GET /api/weather/current?location=Jalandhar&mode=mock&scenario=heavy_rain`
- `POST /api/pipeline/run`
- `GET /api/farmers`
- `GET /api/farmers/F001`
- `GET /api/farmers/F001/dashboard`
- `GET /api/alerts`
- `GET /api/weather/providers?location=Jalandhar` (real Open-Meteo query)
- `POST /api/chat` (deterministic, grounded advisory; no LLM is used)
- `POST /api/monitor/run?mode=mock`

## Safety model

Weather values, threat detection, risk calculations, recommendations, and
alerts are produced from structured provider data and deterministic agent
logic. The chat endpoint is grounded against that structured result and does
not invent numerical values. The IMD adapter remains intentionally disabled
until the team obtains an authorized IMD data integration.

## Outbound Farmer SMS Integration

WeatherGPT includes a production-ready, provider-based outbound SMS layer to deliver timely, actionable disaster advisories directly to registered farmers in their preferred language (English, Hindi, Punjabi).

### Safety Defaults

- **Safe Local Default:** By default, `SMS_ENABLED=false` and `SMS_PROVIDER=mock`. **No real SMS is ever sent** during test suites, local development, or initial server boot.
- **Audit Persistence:** Every alert dispatch attempt (whether mock, skipped, sent, or failed) is stored in the SQLite `alert_logs` audit trail with its channel, phone number, provider name, provider message ID, status, timestamp, and safe error message.
- **Idempotency:** In-memory idempotency keys (`{threat_id}:{farmer_id}:{action}`) ensure duplicate alerts are never dispatched twice for the same threat.
- **Validation:** Phone numbers are strictly normalized to international E.164 format (e.g. `919934768317` for India). Non-conforming numbers fail safely without invoking external APIs.

### Configuration Environment Variables

| Variable | Default | Description |
|---|---|---|
| `SMS_ENABLED` | `false` | Master toggle: set to `true` to attempt outbound delivery via configured provider. |
| `SMS_PROVIDER` | `mock` | `mock` for safe local development/tests, or `vonage` for live SMS delivery. |
| `VONAGE_API_KEY` | *(empty)* | Vonage API Key from Vonage API Dashboard (keep blank in git / repo). |
| `VONAGE_API_SECRET` | *(empty)* | Vonage API Secret from Vonage API Dashboard (keep blank in git / repo). |
| `SMS_SENDER_ID` | `WeatherGPT` | Alphanumeric sender ID or virtual number registered with Vonage. |

### How to Safely Enable Real SMS Delivery (Vonage)

To enable live SMS delivery to farmers:
1. Register on [Vonage API Developer Portal](https://dashboard.nexmo.com/) and acquire account credits.
2. In your Vonage Dashboard, retrieve your **API Key** and **API Secret**.
3. Open your local `.env` file (never commit `.env` to source control) and configure:
   ```bash
   SMS_ENABLED=true
   SMS_PROVIDER=vonage
   VONAGE_API_KEY="your_vonage_api_key_here"
   VONAGE_API_SECRET="your_vonage_api_secret_here"
   # Optional registered sender ID:
   SMS_SENDER_ID="WeatherGPT"
   ```
4. Verify farmer profiles in the database or seed data have valid mobile numbers (e.g., `+91-9876543210` or `9876543210`).
5. Run the pipeline with a threat scenario:
   ```bash
   curl -X POST http://127.0.0.1:8000/api/pipeline/run \
     -H "Content-Type: application/json" \
     -d '{"location": "Jalandhar", "mode": "mock", "scenario": "heavy_rain"}'
   ```
6. Inspect the audit log via `GET /api/alerts` to confirm delivery status (`status: "success"` or `"failed"`), provider (`vonage`), and provider message ID (`provider_message_id`).

## Vonage SMS Delivery-Receipt (DLR) Webhook

WeatherGPT provides an automated, production-grade delivery receipt webhook endpoint that receives delivery status callbacks from Vonage and updates existing alert audit records in SQLite.

### Webhook Endpoint

- **Path:** `POST /api/webhooks/vonage/delivery-receipt`
- **Supported Formats:** JSON or Form-URL-Encoded / Query parameters.
- **Audit Synchronization:** Looks up the alert audit entry by `messageId` and updates status to `delivered`, `failed`, `rejected`, or `expired`. Unrecognized statuses fallback safely to `unknown`.
- **Idempotency:** Repeated delivery receipts for the same message ID and terminal status are accepted without redundant database writes.
- **Tamper Protection:** The endpoint only updates pre-existing alert records created by WeatherGPT dispatches; arbitrary audit record injection is rejected.

### Delivery Receipt Environment Variables

| Variable | Default | Description |
|---|---|---|
| `VONAGE_SIGNATURE_SECRET` | *(empty)* | Webhook signature secret from Vonage API Settings. When set, all incoming DLR requests must carry a valid HMAC signature (`sig`). |
| `VONAGE_SIGNATURE_METHOD` | `sha256` | Hash algorithm for signature verification: `sha256` (recommended), `sha512`, `md5`, or `sha1`. |

### Deployment Configuration Steps

1. **Enable Signature Verification (Recommended):**
   In the [Vonage Developer Dashboard](https://dashboard.nexmo.com/settings), navigate to **API Settings** > **Signature Secret**. Copy your signature secret and add to `.env`:
   ```bash
   VONAGE_SIGNATURE_SECRET="your_signature_secret_here"
   VONAGE_SIGNATURE_METHOD="sha256"
   ```
2. **Configure Webhook Callback URL in Vonage:**
   In your Vonage Dashboard or SMS settings, set the Delivery Receipt Webhook URL to your deployed domain:
   ```
   https://<your-domain>/api/webhooks/vonage/delivery-receipt
   ```
   - **HTTP Method:** `POST`
   - **Encoding:** `JSON` (recommended) or form-urlencoded.
3. **Verify Incoming Receipts:**
   Query `GET /api/alerts` to view updated statuses (`delivered`, `failed`, etc.) alongside the provider message ID and any delivery error details.

## Health and Readiness Probes

WeatherGPT provides two distinct observability endpoints for uptime monitoring and container orchestration:

- **Liveness Probe:** `GET /api/health`
  - Returns `200 OK` when the FastAPI web application is responsive.
  - Returns current execution modes (`weather_mode`, `calendar_provider`, `version`).
- **Readiness Probe:** `GET /api/ready`
  - Returns `200 OK` with `status: "ready"` only when the SQLite database is reachable, required tables are initialized, and runtime dependencies are verified.
  - Returns `503 Service Unavailable` with `status: "not_ready"` if SQLite connection fails or tables are missing.

```bash
# Test readiness probe locally
curl -i http://127.0.0.1:8000/api/ready
```

## Production Docker Deployment

WeatherGPT includes a production Dockerfile and Docker Compose configuration with named volume data persistence:

```bash
# 1. Prepare production environment file (ensure secrets are populated)
cp .env.example .env

# 2. Build and start the container in detached mode
docker compose up -d --build

# 3. Check container logs and readiness probe
docker compose logs -f weathergpt-api
curl -i http://localhost:8000/api/ready
```

### SQLite Data Persistence Guarantee

In `docker-compose.yml`, the application uses a named Docker volume `weathergpt-data` mapped to `/app/data` with `DATABASE_URL=sqlite:////app/data/weathergpt.db`. This ensures:
- Farmer profiles, threat audit logs, and delivery receipts are **never lost** during container updates, restarts, or image rebuilds.
- Automatic health check (`CMD-SHELL` querying `/api/ready`) tests database and service health every 30s.

## Pre-Deployment Checklist

Before deploying WeatherGPT to production or turning on live SMS (`SMS_ENABLED=true`), complete every step in this checklist:

### 1. HTTPS & Public Domain
- [ ] Ensure the application is deployed behind a reverse proxy (e.g. Caddy, Nginx, Cloudflare, or AWS ALB) terminating **HTTPS** with valid TLS certificates.
- [ ] Configure `CORS_ORIGINS` in `.env` to include your production frontend domain(s) (e.g. `https://app.yourdomain.com`).

### 2. Database Persistence & Automated Backups
- [ ] Verify that `DATABASE_URL` points to persistent storage (named volume `/app/data/weathergpt.db` in Docker, or persistent EBS/block volume).
- [ ] Schedule automated SQLite backups using SQLite's online backup API or `.backup` cron command:
  ```bash
  sqlite3 /app/data/weathergpt.db ".backup '/backups/weathergpt-$(date +%Y%m%d%H%M%S).db'"
  ```

### 3. Vonage Webhook Signature & Callback URL
- [ ] Retrieve your **Signature Secret** from the [Vonage Dashboard API Settings](https://dashboard.nexmo.com/settings).
- [ ] Set in `.env`:
  ```bash
  VONAGE_SIGNATURE_SECRET="your_signature_secret"
  VONAGE_SIGNATURE_METHOD="sha256"
  ```
- [ ] Set your public Delivery Receipt Webhook URL in the Vonage SMS Settings dashboard:
  ```
  https://<your-public-domain>/api/webhooks/vonage/delivery-receipt
  ```
  *(HTTP POST, JSON format)*

### 4. DLT Sender ID & Regulatory Approvals (India)
- [ ] If sending SMS to Indian numbers (+91):
  - Ensure your Principal Entity and Sender ID (Header) are registered on a TRAI-compliant DLT portal (e.g., Vilpower / Jio / Airtel DLT).
  - Register approved Content Templates for weather and agronomic emergency advisories.
  - Set `SMS_SENDER_ID` to your registered 6-character DLT Header or assigned Vonage virtual number.
- [ ] Keep `SMS_ENABLED=false` until test dispatches and template matching are verified.

### 5. Environment Secrets Isolation
- [ ] Confirm `.env` is listed in `.gitignore` and has **never** been committed to git (`git status` and `git log`).
- [ ] Provide production secrets via container environment variables or secrets manager (e.g., AWS Secrets Manager, GCP Secret Manager, Vault).

### 6. Monitoring & Alerting
- [ ] Point uptime monitors (Datadog, Prometheus, UptimeKuma) to `GET /api/ready` with a 30-second interval.
- [ ] Monitor Vonage account credit balance to prevent dispatch failure code `9` (*Partner out of quota*).

## Tests

```bash
.venv/bin/python -m pytest -v
```
