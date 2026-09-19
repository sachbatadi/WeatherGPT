/**
 * Centralized WeatherGPT Backend Integration Client
 * Directly connects Frontend UI with FastAPI LangGraph Backend (backend/app.py)
 * Supports live endpoint calls, local dev proxy, cloud deployment URLs, and graceful fallbacks.
 */

export interface SystemHealth {
  status: string;
  weather_mode: string;
  calendar_provider: string;
  default_location: string;
  version: string;
  timestamp: string;
}

export interface CurrentWeatherTelemetry {
  location: string;
  source: string;
  temperature_c: number;
  humidity_pct: number;
  precipitation_mm: number;
  wind_speed_kmh: number;
  wind_gust_kmh?: number;
  threat_detected: boolean;
  threat_type: string;
  threat_severity: string;
  confidence: number;
  confidence_reason?: string;
  timestamp: string;
}

export interface PipelineRunResult {
  status: string;
  location: string;
  threat_detected: boolean;
  threat?: {
    event_type?: string;
    severity?: string;
    confidence?: number;
    rainfall_mm?: number;
    wind_speed_kmh?: number;
    temp_c?: number;
    humidity_pct?: number;
    confidence_reason?: string;
  };
  risk_level?: string;
  alert_required: boolean;
  replanning_required: boolean;
  affected_farmers: Array<{
    farmer_id: string;
    name: string;
    location: string;
    crop: string;
    risk_level?: string;
    phone?: string;
  }>;
  recommended_actions: string[];
  execution_summary?: string;
  audit_event_id?: number;
  timestamp: string;
}

export interface FarmerRecord {
  farmer_id: string;
  name: string;
  phone?: string;
  language?: string;
  location: string;
  district?: string;
  state?: string;
  land_size_acres?: number;
  crop: string;
  crop_stage: string;
  soil_type?: string;
  irrigation_method?: string;
  current_plan: Array<{
    activity_id: string;
    activity_type: string;
    scheduled_date: string;
    status: string;
    details?: any;
  }>;
}

export interface AlertLogRecord {
  id: number;
  farmer_id?: string;
  phone?: string;
  channel?: string;
  severity?: string;
  message?: string;
  status?: string;
  error_message?: string;
  provider_message_id?: string;
  created_at: string;
}

const BACKEND_URL_KEY = 'weathergpt_backend_url';

export function getBackendUrl(): string {
  try {
    const custom = localStorage.getItem(BACKEND_URL_KEY);
    if (custom && custom.trim()) return custom.trim().replace(/\/+$/, '');
  } catch {}
  
  const envUrl = (import.meta as any).env?.VITE_BACKEND_URL;
  if (envUrl && String(envUrl).trim()) {
    return String(envUrl).trim().replace(/\/+$/, '');
  }

  // If running on localhost/127.0.0.1, default to FastAPI port 8000
  if (typeof window !== 'undefined' && (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')) {
    return 'http://127.0.0.1:8000';
  }

  // On production / Vercel: use relative URL if proxy configured, or current origin
  return '';
}

export function setBackendUrl(url: string): void {
  try {
    if (url.trim()) {
      localStorage.setItem(BACKEND_URL_KEY, url.trim().replace(/\/+$/, ''));
    } else {
      localStorage.removeItem(BACKEND_URL_KEY);
    }
  } catch {}
}

/**
 * Check if FastAPI backend is healthy and responding
 */
export async function checkBackendHealth(): Promise<{ connected: boolean; health?: SystemHealth; url: string }> {
  const base = getBackendUrl();
  const endpoint = base ? `${base}/api/health` : '/api/health';

  try {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 3500);

    const res = await fetch(endpoint, { signal: controller.signal });
    clearTimeout(timeout);

    if (res.ok) {
      const data = await res.json();
      if (data && (data.status === 'healthy' || data.version)) {
        return { connected: true, health: data, url: base || 'Same Origin' };
      }
    }
  } catch (err) {
    // Backend not reachable
  }

  return { connected: false, url: base || 'Default' };
}

/**
 * Ingest live weather & evaluate threat from Sentinel Agent
 */
export async function fetchCurrentWeather(
  location = 'Patiala',
  mode = 'live'
): Promise<CurrentWeatherTelemetry | null> {
  const base = getBackendUrl();
  const locParam = encodeURIComponent(location);
  const endpoint = base
    ? `${base}/api/weather/current?location=${locParam}&mode=${mode}`
    : `/api/weather/current?location=${locParam}&mode=${mode}`;

  try {
    const res = await fetch(endpoint);
    if (res.ok) {
      return await res.json();
    }
  } catch (err) {
    console.warn('[BackendAPI] fetchCurrentWeather failed:', err);
  }
  return null;
}

/**
 * Execute full LangGraph agent workflow:
 * Sentinel (Observe) -> Strategist (Assess & Plan) -> Executor (Dispatch & Sync)
 */
export async function runAgentPipeline(
  location = 'Patiala',
  mode = 'live',
  scenario?: string
): Promise<PipelineRunResult | null> {
  const base = getBackendUrl();
  const endpoint = base ? `${base}/api/pipeline/run` : '/api/pipeline/run';

  try {
    const res = await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        location,
        mode,
        scenario: scenario || (mode === 'mock' ? 'heavy_rain' : undefined),
      }),
    });

    if (res.ok) {
      return await res.json();
    }
  } catch (err) {
    console.error('[BackendAPI] runAgentPipeline error:', err);
  }
  return null;
}

/**
 * Retrieve registered farmers list from SQLite database
 */
export async function fetchRegisteredFarmers(location?: string): Promise<FarmerRecord[]> {
  const base = getBackendUrl();
  const query = location ? `?location=${encodeURIComponent(location)}` : '';
  const endpoint = base ? `${base}/api/farmers${query}` : `/api/farmers${query}`;

  try {
    const res = await fetch(endpoint);
    if (res.ok) {
      const data = await res.json();
      return data.farmers || [];
    }
  } catch (err) {
    console.warn('[BackendAPI] fetchRegisteredFarmers failed:', err);
  }
  return [];
}

/**
 * Fetch dispatched alert audit records from SQLite persistence
 */
export async function fetchDispatchedAlerts(farmerId?: string, limit = 50): Promise<AlertLogRecord[]> {
  const base = getBackendUrl();
  const params = new URLSearchParams();
  if (farmerId) params.set('farmer_id', farmerId);
  params.set('limit', String(limit));

  const endpoint = base ? `${base}/api/alerts?${params.toString()}` : `/api/alerts?${params.toString()}`;

  try {
    const res = await fetch(endpoint);
    if (res.ok) {
      const data = await res.json();
      return data.alerts || [];
    }
  } catch (err) {
    console.warn('[BackendAPI] fetchDispatchedAlerts failed:', err);
  }
  return [];
}

/**
 * Grounded conversational advisory using live weather facts and farmer profile
 */
export async function sendGroundedChatAdvisory(
  message: string,
  language = 'en',
  location = 'Patiala',
  farmerId?: string
): Promise<{ reply: string; grounding_used: boolean } | null> {
  const base = getBackendUrl();
  const endpoint = base ? `${base}/api/chat` : '/api/chat';

  try {
    const res = await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message,
        language,
        location,
        farmer_id: farmerId,
      }),
    });

    if (res.ok) {
      return await res.json();
    }
  } catch (err) {
    console.warn('[BackendAPI] sendGroundedChatAdvisory failed:', err);
  }
  return null;
}
