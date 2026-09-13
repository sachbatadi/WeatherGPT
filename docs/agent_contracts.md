# WeatherGPT Agent Communication Contracts

This document defines the interface contracts between the autonomous agents in the WeatherGPT architecture for SIH.

```
                  WEATHER API
                       ↓
              👤 MEMBER 2: SENTINEL AGENT
                       ↓  [Threat JSON]
              👤 MEMBER 3: STRATEGIST AGENT
                       ↓  [Risk + Action Payload]
              👤 ORCHESTRATOR (LangGraph)
                 ↙           ↓           ↘
         👤 MEMBER 4    👤 MEMBER 5    👤 MEMBER 6
          RADIO-GPT      DASHBOARD     DATABASE/API
              ↓
            VOICE / 📞
              ↓
           FARMER
```

---

## 1. Sentinel Agent $\rightarrow$ Strategist Agent Contract (`Threat JSON`)

When the Sentinel Agent detects an anomalous or hazardous weather pattern from verified weather APIs, it emits a `Threat JSON` object.

### Schema (`agents/sentinel/schemas.py`)
```json
{
  "event_id": "EVT-20260913-001",
  "event_type": "heavy_rain",
  "severity": "high",
  "probability": 0.85,
  "confidence": "high",
  "confidence_reason": "3 of 4 forecast models agree on rainfall timing and intensity",
  "location": "Jalandhar",
  "coordinates": {
    "latitude": 31.326,
    "longitude": 75.5762
  },
  "time_to_event_minutes": 30,
  "duration_hours": 3.5,
  "rainfall_mm": 60.0,
  "wind_speed_kmh": 28.0,
  "temp_c": 26.5,
  "humidity_pct": 88.0,
  "hail_risk": false,
  "metadata": {}
}
```

### Supported Event Types
- `heavy_rain`: Extreme precipitation, flash flooding, waterlogging.
- `high_wind`: Gale, strong gusts (drift hazard for spraying, lodging for crops).
- `extreme_heat`: Heatwave, thermal stress, flower drop.
- `frost`: Cold shock, night frost damage.
- `hail`: Hailstorms damaging canopy and fruit.
- `cyclone`: Combined storm, destructive winds, deluge.
- `drought`: Extended dry spell, soil moisture depletion.

---

## 2. Strategist Agent $\rightarrow$ Orchestrator Contract (`Risk + Action Payload`)

The Strategist Agent receives the `Threat JSON`, loads the affected farmer profiles, evaluates agronomic impact, updates active farm schedules (re-planning), and generates the `Risk + Action` payload.

### Schema (`agents/strategist/schemas.py`)
```json
{
  "threat_event_id": "EVT-20260913-001",
  "overall_risk_level": "high",
  "affected_farmers_count": 2,
  "alert_required": true,
  "assessments": [
    {
      "farmer_id": "F001",
      "farmer_name": "Gurpreet Singh",
      "crop": "Wheat",
      "crop_stage": "Flowering",
      "risk_level": "high",
      "risk_score": 78.5,
      "risk_factors": [
        "Excessive rainfall anticipated: 60.0 mm may cause field inundation.",
        "Wheat is in Flowering stage: rain risks washing off pollen and reducing grain set.",
        "Scheduled irrigation conflicts with incoming 60 mm rain on loamy soil."
      ],
      "actions": [
        {
          "action_type": "postpone_irrigation",
          "title": "Postpone Scheduled Irrigation",
          "description": "Cancel scheduled irrigation for your Wheat. The forecasted 60.0 mm rainfall will adequately saturate the loamy soil. Re-assess moisture in 4 days.",
          "urgency": "high",
          "target_date": "2026-09-15",
          "rescheduled_date": "+4 days after rain ceases",
          "affected_activity_id": "ACT-001"
        },
        {
          "action_type": "drainage_preparation",
          "title": "Clear Field Drainage Channels",
          "description": "Inspect field bunds and clear excess water drainage outlets to prevent waterlogging and root hypoxia in loamy soil.",
          "urgency": "high"
        }
      ],
      "plain_language_explanation": "WeatherGPT detected a HIGH risk from incoming Heavy Rain in Jalandhar (60 mm rainfall predicted with 85% confidence (HIGH)). For your Wheat (Flowering stage) on Loamy soil: Scheduled irrigation conflicts with incoming 60 mm rain. Recommended Strategy: Postpone Scheduled Irrigation; Clear Field Drainage Channels.",
      "radio_gpt_script": "Attention Gurpreet Singh ji from Jalandhar. This is an urgent WeatherGPT update for your Wheat crop. Heavy rainfall of 60.0 millimeters is expected in 30 minutes. Action required: Postpone Scheduled Irrigation. Also: Clear Field Drainage Channels. Please stay safe and consult the WeatherGPT dashboard for updated schedules.",
      "dashboard_summary": {
        "farmer_id": "F001",
        "farmer_name": "Gurpreet Singh",
        "crop": "Wheat",
        "crop_stage": "Flowering",
        "soil_type": "Loamy",
        "risk_level": "high",
        "risk_score": 78.5,
        "badge_color": "orange",
        "primary_action": "Postpone Scheduled Irrigation",
        "action_count": 2,
        "replanning_required": true
      },
      "replanning_required": true,
      "updated_plan": [
        {
          "activity_id": "ACT-001",
          "activity_type": "irrigation",
          "scheduled_date": "2026-09-15",
          "details": {"duration_hours": 4},
          "status": "postponed"
        }
      ]
    }
  ]
}
```

---

## 3. Orchestrator `WeatherState` Integration

In the LangGraph state graph, the `strategist` node can be executed with:

```python
from agents.strategist import run_strategist_node

# In LangGraph builder:
graph.add_node("strategist", run_strategist_node)
```

The strategist populates the shared `WeatherState`:
- `state["risk_level"]`: `"high"` / `"critical"` / `"medium"` / `"low"`
- `state["recommended_actions"]`: List of concise action titles.
- `state["alert_required"]`: Boolean flag indicating if Radio-GPT / SMS should trigger.
- `state["replanning_required"]`: Boolean flag indicating whether DB schedule should update.
- `state["radio_gpt_payload"]`: Ready-to-speak scripts for Member 4.
- `state["dashboard_payload"]`: UI card states and alert badges for Member 5.
