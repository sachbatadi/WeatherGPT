# WeatherGPT Agent Communication Contracts

This document defines the official interface contracts between the autonomous agents in the **WeatherGPT** architecture for SIH.

```text
                  WEATHER API
                       ↓
               👁️ SENTINEL AGENT
             (Consensus & Hazard Detection)
                       ↓  [Threat JSON]
              🧠 STRATEGIST AGENT
            (Agronomic Risk & Re-planning)
                       ↓  [Risk + Action Payload]
             🔀 ORCHESTRATOR (LangGraph)
                       ↓
               ⚡ EXECUTOR AGENT
             (Dispatch & Plan Synchronization)
                ↙          ↓          ↘
        📱 SMS Alerts   📅 Calendar   📊 Dashboard & DB
          (Localized)      Sync         (Telemetry)
```

---

## 1. Sentinel Agent $\rightarrow$ Strategist Agent Contract (`Threat JSON`)

When the Sentinel Agent verifies an anomalous or hazardous weather pattern across multi-source forecast models (ECMWF, GFS, ICON), it emits a standardized `Threat JSON` object.

### Schema (`agents/sentinel/schemas.py`)
```json
{
  "event_id": "EVT-20260915-001",
  "event_type": "heavy_rain",
  "severity": "high",
  "probability": 0.85,
  "confidence": "high",
  "confidence_reason": "High consensus: 3 of 3 models (ECMWF, GFS, ICON) agree on precipitation timing and intensity (18-22 mm/h).",
  "location": "Jalandhar",
  "coordinates": {
    "latitude": 31.326,
    "longitude": 75.5762
  },
  "time_to_event_minutes": 30,
  "duration_hours": 3.0,
  "rainfall_mm": 60.0,
  "wind_speed_kmh": 22.0,
  "wind_gust_kmh": 36.0,
  "temp_c": 26.5,
  "temp_max_c": 26.5,
  "temp_min_c": 23.0,
  "humidity_pct": 88.0,
  "hail_risk": false,
  "metadata": {
    "source": "open-meteo-ensemble",
    "consensus_ratio": 1.0
  }
}
```

### Supported Threat Classifications
- `heavy_rain`: Cumulative 3-hour precipitation $\ge 20$ mm or flash deluge.
- `high_wind`: Sustained winds $\ge 20$ km/h (chemical spraying drift limit) or gusts $\ge 40$ km/h.
- `extreme_heat`: Peak temperatures $\ge 38^\circ\text{C}$ (thermal stress for flowering crops).
- `frost`: Minimum night temperatures $\le 4^\circ\text{C}$ (foliage burn hazard).
- `hail`: Convective thunderstorm cells with hail probability (WMO codes 96/99).
- `cyclone`: Dual-hazard convergence of gale-force winds and torrential rain.
- `drought`: Prolonged zero-precipitation window under high evaporation.
- `none`: Safe, non-hazardous observation routine.

---

## 2. Strategist Agent $\rightarrow$ Orchestrator Contract (`Risk + Action Payload`)

The Strategist Agent consumes the `Threat JSON`, queries `FarmerDB` for farmers in the affected region, evaluates agronomic risk using deterministic soil hydrology and crop-stage matrices, re-plans active farm schedules, and generates the action payload.

### Dynamic Soil Drying Formula
$$\text{Drying Days} = \max\left(2, \min\left(10, \text{round}\left(\frac{\text{Rainfall (mm)}}{12.0} \times \text{Soil Factor}\right)\right)\right)$$
*(Soil factors: Clay = 1.5×, Loam = 1.0×, Sand = 0.5×)*

### Schema (`agents/strategist/schemas.py`)
```json
{
  "threat_event_id": "EVT-20260915-001",
  "overall_risk_level": "critical",
  "affected_farmers_count": 2,
  "alert_required": true,
  "assessments": [
    {
      "farmer_id": "F001",
      "farmer_name": "Gurpreet Singh",
      "crop": "Wheat",
      "crop_stage": "Flowering",
      "soil_type": "Loamy",
      "risk_level": "critical",
      "risk_score": 100.0,
      "risk_breakdown": {
        "precipitation_risk": 80.0,
        "wind_risk": 39.6,
        "thermal_risk": 0.0,
        "disease_risk": 0.0
      },
      "risk_factors": [
        "Excessive rainfall anticipated: 60.0 mm may trigger flash waterlogging.",
        "Wheat is in Flowering stage: rain risks washing off pollen and reducing seed set.",
        "Scheduled irrigation conflicts with incoming 60 mm rain on Loamy soil.",
        "Heavy rainfall will cause nitrate leaching and nutrient runoff if fertilizer is applied now."
      ],
      "actions": [
        {
          "action_type": "postpone_irrigation",
          "title": "Postpone Scheduled Irrigation",
          "description": "Cancel scheduled watering for your Wheat. Forecasted 60.0 mm rain will fully meet soil moisture requirements. Re-assess soil moisture in 5 days.",
          "urgency": "high",
          "target_date": "2026-09-15",
          "rescheduled_date": "+5 days after rain ceases",
          "affected_activity_id": "ACT-001"
        },
        {
          "action_type": "delay_fertilization",
          "title": "Delay Fertilizer Application",
          "description": "Postpone fertilizer application (Urea top-dressing). Applying before 60 mm rain wastes 40-60% of fertilizer into groundwater runoff.",
          "urgency": "high",
          "target_date": "2026-09-16",
          "rescheduled_date": "+4 days post-rain when soil is moist",
          "affected_activity_id": "ACT-002"
        },
        {
          "action_type": "drainage_preparation",
          "title": "Clear Field Drainage Channels",
          "description": "Inspect field perimeter bunds and open drainage outlets to avoid root suffocation in Loamy soil.",
          "urgency": "high"
        }
      ],
      "plain_language_explanation": "WeatherGPT detected a CRITICAL risk from incoming Heavy Rain in Jalandhar (60.0 mm rainfall predicted with 85% probability (HIGH confidence)). For your Wheat (Flowering stage) on Loamy soil: Scheduled irrigation conflicts with incoming 60 mm rain. Recommended Strategy: Postpone Scheduled Irrigation; Delay Fertilizer Application; Clear Field Drainage Channels.",
      "dashboard_summary": {
        "farmer_id": "F001",
        "farmer_name": "Gurpreet Singh",
        "crop": "Wheat",
        "crop_stage": "Flowering",
        "soil_type": "Loamy",
        "risk_level": "critical",
        "risk_score": 100.0,
        "badge_color": "red",
        "primary_action": "Postpone Scheduled Irrigation",
        "action_count": 3,
        "replanning_required": true,
        "next_review_hours": 7
      },
      "replanning_required": true,
      "updated_plan": [
        {
          "activity_id": "ACT-001",
          "activity_type": "irrigation",
          "scheduled_date": "2026-09-15",
          "details": {"duration_hours": 4, "target_depth_cm": 5},
          "status": "postponed"
        },
        {
          "activity_id": "ACT-002",
          "activity_type": "fertilization",
          "scheduled_date": "2026-09-16",
          "details": {"fertilizer": "Urea top-dressing", "quantity_kg": 50},
          "status": "postponed"
        }
      ],
      "next_observation": {
        "trigger_type": "reassess_soil_moisture",
        "reassess_after_hours": 7,
        "condition": "Check if rainfall ceased and verify soil infiltration on Loamy field"
      }
    }
  ]
}
```

---

## 3. Continuous Re-Observation Trigger (`NextObservationTrigger`)

To complete the autonomous agent cycle (*Observe $\rightarrow$ Predict $\rightarrow$ Evaluate Risk $\rightarrow$ Plan $\rightarrow$ Execute $\rightarrow$ Observe Again*), the Strategist outputs instructions telling Sentinel when and what to verify next:

```json
{
  "trigger_type": "reassess_soil_moisture",
  "reassess_after_hours": 7,
  "condition": "Check if rainfall ceased and verify soil infiltration on Loamy field"
}
```

- **Rainfall Events**: Triggers observation 4–8 hours after rain ceases to verify real soil saturation and drainage before resuming irrigation.
- **Wind Events**: Triggers observation 3–4 hours later to detect wind drop below 15 km/h and open safe spraying windows.
- **Routine Weather**: Triggers standard 12-hour forecast re-synchronization.

---

## 4. Orchestrator $\rightarrow$ Executor Agent Contract (`ExecutorOutput`)

The **Executor Agent** receives the approved strategy from the Orchestrator and executes real-world synchronizations:
1. **Plan & Calendar Updates**: Updates the database (`FarmerDB`) and synchronizes events with Google Calendar or Mock Calendar.
2. **Localized SMS Dispatch**: Generates localized SMS alerts in the farmer's preferred language (English, Hindi, or Punjabi).
3. **Dashboard Telemetry**: Publishes live status events to the UI dashboard feed.
4. **Idempotency Protection**: Ensures duplicate alerts and operations are suppressed on re-runs.

### Schema (`agents/executor/schemas.py`)
```json
{
  "execution_summary": {
    "status": "success",
    "threat_event_id": "EVT-20260915-001",
    "alerts": 2,
    "plan_updates": 2,
    "calendar_operations": 2,
    "dashboard_events": 2,
    "failures": 0,
    "timestamp": "2026-09-16T06:00:00Z"
  },
  "dispatched_alerts": [
    {
      "dispatch_id": "DISP-0001",
      "farmer_id": "F001",
      "farmer_name": "Gurpreet Singh",
      "phone": "+91-9876543210",
      "channel": "sms",
      "language": "pa",
      "urgency": "high",
      "message": "ਵੈਦਰ-ਜੀਪੀਟੀ ਅਲਰਟ: Gurpreet Singh ਜੀ, ਤੁਹਾਡੀ Wheat ਫ਼ਸਲ ਲਈ ਜ਼ਰੂਰੀ ਸੂਚਨਾ: Postpone Scheduled Irrigation। ਵੇਰਵਿਆਂ ਲਈ ਡੈਸ਼ਬੋਰਡ ਦੇਖੋ।",
      "status": "queued",
      "timestamp": "2026-09-16T06:00:00Z"
    }
  ],
  "applied_plan_updates": [
    {
      "farmer_id": "F001",
      "activity_id": "ACT-001",
      "activity_type": "irrigation",
      "original_date": "2026-09-15",
      "new_date": "+5 days after rain ceases",
      "action_type": "postpone_irrigation",
      "reason": "Forecasted 60.0 mm rain satisfies moisture requirements."
    }
  ],
  "calendar_operations": [
    {
      "operation": "update",
      "event_id": "cal_evt_mock_0001",
      "title": "WeatherGPT: Postpone Scheduled Irrigation",
      "start": "2026-09-20",
      "end": "2026-09-21",
      "status": "success"
    }
  ],
  "alert_status": "dispatched"
}
```

---

## 5. Orchestrator `WeatherState` Central Bus Integration

The entire system integrates through the shared LangGraph state graph in [`agents/orchestrator/graph.py`](file:///c:/Users/ssumi/OneDrive/Documents/SIH/weather%20GPT(local)/WeatherGPT/agents/orchestrator/graph.py):

```python
from langgraph.graph import StateGraph, START, END
from .state import WeatherState
from .nodes import run_sentinel, run_strategist
from .router import threat_router
from agents.executor.agent import run_executor_node

def build_graph():
    graph = StateGraph(WeatherState)

    # Agent Nodes
    graph.add_node("sentinel", run_sentinel)
    graph.add_node("strategist", run_strategist)
    graph.add_node("executor", run_executor_node)

    # Workflow Edges
    graph.add_edge(START, "sentinel")
    graph.add_conditional_edges(
        "sentinel",
        threat_router,
        {
            "strategist": "strategist",
            "monitor": END
        }
    )
    graph.add_edge("strategist", "executor")
    graph.add_edge("executor", END)

    return graph.compile()
```

### Complete `WeatherState` Keys (`agents/orchestrator/state.py`):
| State Key | Populated By | Purpose |
|---|---|---|
| `location` | Initial Input | Target village or district |
| `weather_data` | Sentinel | Raw and normalized multi-model weather telemetry |
| `threat_detected` | Sentinel | Boolean flag triggering the threat router |
| `threat` | Sentinel | Validated `ThreatEvent` JSON |
| `affected_farmers` | Strategist | List of farmers matching location with risk levels |
| `risk_level` | Strategist | Composite risk (`"low"`, `"medium"`, `"high"`, `"critical"`) |
| `recommended_actions` | Strategist | Prioritized list of actionable farm steps |
| `alert_required` | Strategist | Boolean flag indicating whether emergency alerts trigger |
| `replanning_required` | Strategist | Boolean flag indicating calendar schedule changes |
| `strategist_output` | Strategist | Complete serializable `StrategistOutput` object |
| `dashboard_payload` | Strategist | Color-coded badges and metric summaries for frontend |
| `execution_summary` | Executor | Execution status receipt (updates, alerts, failures) |
| `dispatched_alerts` | Executor | Multi-channel queued alert records (SMS) |
| `applied_plan_updates` | Executor | Synchronized plan modification logs |
| `calendar_operations` | Executor | Google Calendar / Mock Calendar update receipts |
| `alert_status` | Executor | Dispatch status (`"dispatched"`, `"no_alert_needed"`) |
