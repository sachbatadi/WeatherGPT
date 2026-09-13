"""
Agricultural Risk Engine (Module 5 & Module 9).

Deterministic, transparent agronomic risk calculations based on:
1. Threat characteristics (Sentinel output: rainfall, wind, temp, probability, confidence)
2. Crop biology and growth stage vulnerability
3. Soil hydrology and water holding capacity
4. Active farm schedule interference (irrigation, spraying, harvest)

Per the WeatherGPT design guide:
"Important: the LLM should not invent weather numbers. Structured weather data,
calculations and risk rules/models should produce the evidence; the AI should
reason/orchestrate and explain that evidence."
"""

from typing import Dict, Any, List, Tuple
from .schemas import (
    SeverityLevel,
    ActionType,
    UrgencyLevel,
    ActionItem,
    FarmerProfile,
    FarmActivity
)


# Crop vulnerability multipliers by growth stage
# Higher value indicates greater sensitivity to weather stress
STAGE_SENSITIVITY: Dict[str, Dict[str, float]] = {
    "wheat": {
        "sowing": 1.2,          # Sensitive to waterlogging / seed rot
        "vegetative": 0.8,      # More resilient
        "flowering": 1.5,       # Highly sensitive to heavy rain (pollen wash) & heat
        "grain_filling": 1.3,   # Vulnerable to terminal heat and lodging
        "maturity": 1.4,        # Vulnerable to rain / grain sprouting
        "harvesting": 1.5       # Vulnerable to rain / spoilage
    },
    "rice": {
        "sowing": 1.1,
        "vegetative": 0.7,      # Enjoys standing water
        "flowering": 1.4,       # Wind and rain disrupt pollination
        "grain_filling": 1.1,
        "maturity": 1.4,
        "harvesting": 1.5
    },
    "cotton": {
        "sowing": 1.2,
        "vegetative": 0.9,
        "flowering": 1.4,       # Square shedding on heavy rain
        "grain_filling": 1.3,   # Boll development
        "maturity": 1.5,        # Heavy rain discolors open bolls
        "harvesting": 1.5
    },
    "tomato": {
        "sowing": 1.3,
        "vegetative": 1.1,
        "flowering": 1.5,       # Blossom drop on heat or water excess
        "grain_filling": 1.3,   # Fruit development (cracking on deluge)
        "maturity": 1.4,
        "harvesting": 1.4
    },
    "mustard": {
        "sowing": 1.1,
        "vegetative": 0.8,
        "flowering": 1.5,       # Frost / cloudiness causes aphid outbreak
        "grain_filling": 1.2,
        "maturity": 1.3,
        "harvesting": 1.4
    }
}

# Soil drainage and saturation factors
SOIL_DRAINAGE_DAYS: Dict[str, int] = {
    "clay": 6,       # Slow drainage, high waterlogging risk
    "black_soil": 5, # High swell, retains water very long
    "loamy": 4,      # Ideal balanced retention
    "silty": 4,      # Moderate drainage
    "sandy": 2       # Fast drainage, rapid drying
}


class RiskEngine:
    """
    Deterministic Agricultural Decision & Risk Calculation Engine.
    """

    @classmethod
    def evaluate_farmer_risk(
        cls,
        threat: Dict[str, Any],
        farmer: FarmerProfile
    ) -> Tuple[SeverityLevel, float, List[str], List[ActionItem], bool, List[FarmActivity]]:
        """
        Evaluate risk, generate recommended actions, and re-plan activities.

        Returns:
            (risk_level, risk_score, risk_factors, actions, replanning_required, updated_plan)
        """
        event_type = str(threat.get("event_type", "unknown")).lower()
        threat_severity = str(threat.get("severity", "medium")).lower()
        probability = float(threat.get("probability", 0.7))
        confidence = str(threat.get("confidence", "high")).lower()

        # Specific weather parameters
        rainfall_mm = float(threat.get("rainfall_mm") or 0.0)
        wind_speed_kmh = float(threat.get("wind_speed_kmh") or 0.0)
        temp_c = float(threat.get("temp_c") or 25.0)
        temp_max_c = float(threat.get("temp_max_c") or temp_c)
        temp_min_c = float(threat.get("temp_min_c") or temp_c)
        hail_risk = bool(threat.get("hail_risk", False))

        crop_name = farmer.crop.lower()
        stage_name = farmer.crop_stage.lower()
        soil_type = farmer.soil_type.lower()

        # Base severity score
        base_score_map = {"low": 20.0, "medium": 45.0, "high": 70.0, "critical": 90.0}
        score = base_score_map.get(threat_severity, 40.0)

        # Multi-source confidence weight
        conf_factor = 1.0 if confidence == "high" else (0.85 if confidence == "medium" else 0.70)
        score *= (probability * 0.5 + 0.5) * conf_factor

        # Crop sensitivity multiplier
        crop_multipliers = STAGE_SENSITIVITY.get(crop_name, {})
        stage_mult = crop_multipliers.get(stage_name, 1.0)
        score *= stage_mult

        # Soil factor
        if "rain" in event_type or rainfall_mm > 0:
            if soil_type in ("clay", "black_soil"):
                score *= 1.25  # Increased risk of waterlogging
            elif soil_type == "sandy":
                score *= 0.85  # Drains quickly

        risk_factors: List[str] = []
        actions: List[ActionItem] = []
        replanning_required = False
        updated_plan = [act.model_copy(deep=True) for act in farmer.current_plan]

        # -------------------------------------------------------------------
        # 1. HEAVY RAINFALL / PRECIPITATION EVALUATION
        # -------------------------------------------------------------------
        if "rain" in event_type or rainfall_mm >= 15.0 or "cyclone" in event_type:
            if rainfall_mm >= 50.0:
                risk_factors.append(
                    f"Excessive rainfall anticipated: {rainfall_mm:.1f} mm may cause field inundation."
                )
            elif rainfall_mm >= 20.0:
                risk_factors.append(
                    f"Substantial rainfall expected: {rainfall_mm:.1f} mm."
                )

            # Crop stage impact
            if stage_name == "flowering":
                risk_factors.append(
                    f"{farmer.crop} is in Flowering stage: rain risks washing off pollen and reducing grain set."
                )
            elif stage_name in ("maturity", "harvesting"):
                risk_factors.append(
                    f"{farmer.crop} is at Maturity/Harvest: rain can cause grain blackening, fungal rot, or lodging."
                )

            # Check planned irrigation
            for act in updated_plan:
                if act.activity_type.lower() == "irrigation" and act.status != "cancelled":
                    replanning_required = True
                    act.status = "postponed"
                    dry_days = SOIL_DRAINAGE_DAYS.get(soil_type, 4)
                    rescheduled_text = f"+{dry_days} days after rain ceases"

                    risk_factors.append(
                        f"Scheduled irrigation conflicts with incoming {rainfall_mm:.0f} mm rain on {soil_type} soil."
                    )
                    actions.append(
                        ActionItem(
                            action_type=ActionType.POSTPONE_IRRIGATION,
                            title="Postpone Scheduled Irrigation",
                            description=(
                                f"Cancel scheduled irrigation for your {farmer.crop}. The forecasted "
                                f"{rainfall_mm:.1f} mm rainfall will adequately saturate the {soil_type} soil. "
                                f"Re-assess moisture in {dry_days} days."
                            ),
                            urgency=UrgencyLevel.HIGH if rainfall_mm > 30 else UrgencyLevel.MEDIUM,
                            target_date=act.scheduled_date,
                            rescheduled_date=rescheduled_text,
                            affected_activity_id=act.activity_id
                        )
                    )

            # Check planned spraying (chemical wash-off)
            for act in updated_plan:
                if act.activity_type.lower() in ("spraying", "fertilizer") and act.status != "cancelled":
                    replanning_required = True
                    act.status = "postponed"
                    risk_factors.append("Rain will wash off sprayed pesticides/fertilizers within 24-48 hours.")
                    actions.append(
                        ActionItem(
                            action_type=ActionType.RESCHEDULE_SPRAY,
                            title="Delay Chemical / Fertilizer Spraying",
                            description=(
                                f"Hold off on spraying {act.details.get('chemical', 'treatments')}. "
                                f"Rain within 24h wastes chemicals and causes environmental run-off."
                            ),
                            urgency=UrgencyLevel.HIGH,
                            target_date=act.scheduled_date,
                            rescheduled_date="After foliage dries post-rain",
                            affected_activity_id=act.activity_id
                        )
                    )

            # Field drainage recommendation for heavy downpours
            if (rainfall_mm >= 40.0 or "clay" in soil_type) and rainfall_mm >= 25.0:
                actions.append(
                    ActionItem(
                        action_type=ActionType.DRAINAGE_PREPARATION,
                        title="Clear Field Drainage Channels",
                        description=(
                            f"Inspect field bunds and clear excess water drainage outlets to prevent "
                            f"waterlogging and root hypoxia in {soil_type} soil."
                        ),
                        urgency=UrgencyLevel.HIGH if rainfall_mm >= 50.0 else UrgencyLevel.MEDIUM
                    )
                )

            # Harvest protection
            if stage_name in ("maturity", "harvesting"):
                actions.append(
                    ActionItem(
                        action_type=ActionType.EXPEDITE_HARVEST,
                        title="Expedite Harvest / Protect Cut Produce",
                        description=(
                            f"If harvesting has begun, move cut crops to elevated dry storage or cover with "
                            f"tarpaulins before rain commences."
                        ),
                        urgency=UrgencyLevel.IMMEDIATE if rainfall_mm >= 30.0 else UrgencyLevel.HIGH
                    )
                )

        # -------------------------------------------------------------------
        # 2. HIGH WIND / GALE EVALUATION
        # -------------------------------------------------------------------
        if "wind" in event_type or wind_speed_kmh >= 20.0 or "cyclone" in event_type:
            risk_factors.append(f"High wind speeds forecasted: {wind_speed_kmh:.1f} km/h.")
            if wind_speed_kmh >= 35.0 and stage_name in ("grain_filling", "maturity"):
                risk_factors.append(f"Tall {farmer.crop} stalks are vulnerable to wind lodging/flattening.")

            # Spray drift risk
            for act in updated_plan:
                if act.activity_type.lower() == "spraying" and act.status != "cancelled":
                    replanning_required = True
                    act.status = "postponed"
                    actions.append(
                        ActionItem(
                            action_type=ActionType.RESCHEDULE_SPRAY,
                            title="Halt Spraying due to Wind Drift",
                            description=(
                                f"Wind speed of {wind_speed_kmh:.1f} km/h exceeds the safe spraying threshold (15 km/h). "
                                f"Postpone pesticide application to avoid drift and off-target damage."
                            ),
                            urgency=UrgencyLevel.HIGH,
                            target_date=act.scheduled_date,
                            rescheduled_date="When wind speed drops below 15 km/h",
                            affected_activity_id=act.activity_id
                        )
                    )

        # -------------------------------------------------------------------
        # 3. EXTREME HEAT / HEATWAVE EVALUATION
        # -------------------------------------------------------------------
        if "heat" in event_type or temp_max_c >= 38.0:
            risk_factors.append(f"Extreme heat stress: temperatures up to {temp_max_c:.1f}°C.")
            if stage_name == "flowering":
                risk_factors.append("High temperature causes pollen sterility and blossom drop.")
                actions.append(
                    ActionItem(
                        action_type=ActionType.HEAT_STRESS_MITIGATION,
                        title="Apply Light Evening Irrigation / Mulch",
                        description=(
                            "Provide light irrigation in late evening or early morning to cool soil root zones "
                            "and maintain microclimate humidity."
                        ),
                        urgency=UrgencyLevel.HIGH
                    )
                )

        # -------------------------------------------------------------------
        # 4. FROST / COLD SNAP EVALUATION
        # -------------------------------------------------------------------
        if "frost" in event_type or temp_min_c <= 4.0:
            risk_factors.append(f"Low temperature hazard: minimum temperature drops to {temp_min_c:.1f}°C.")
            actions.append(
                ActionItem(
                    action_type=ActionType.FROST_PROTECTION,
                    title="Implement Frost Safeguards",
                    description=(
                        "Irrigate lightly in the evening or create controlled perimeter smoke blankets "
                        "to raise ambient field temperature and prevent frost injury."
                    ),
                    urgency=UrgencyLevel.IMMEDIATE
                )
            )

        # -------------------------------------------------------------------
        # 5. HAIL RISK
        # -------------------------------------------------------------------
        if hail_risk or "hail" in event_type:
            risk_factors.append("Hail threat: severe mechanical damage to crop canopy and stems.")
            score = max(score, 85.0)
            actions.append(
                ActionItem(
                    action_type=ActionType.PROTECTIVE_COVERING,
                    title="Deploy Hail Nets / Secure Infrastructure",
                    description="Erect anti-hail nets if available, secure polyhouse coverings, and protect nurseries.",
                    urgency=UrgencyLevel.IMMEDIATE
                )
            )

        # -------------------------------------------------------------------
        # Default if no specific threat triggers actions
        # -------------------------------------------------------------------
        if not actions:
            actions.append(
                ActionItem(
                    action_type=ActionType.NO_ACTION,
                    title="Maintain Current Farm Plan",
                    description="Current weather conditions pose minimal risk to scheduled activities.",
                    urgency=UrgencyLevel.LOW
                )
            )

        # Final score clamping and level determination
        final_score = max(0.0, min(100.0, round(score, 1)))

        if final_score >= 70.0:
            risk_level = SeverityLevel.CRITICAL
        elif final_score >= 48.0:
            risk_level = SeverityLevel.HIGH
        elif final_score >= 25.0:
            risk_level = SeverityLevel.MEDIUM
        else:
            risk_level = SeverityLevel.LOW

        return risk_level, final_score, risk_factors, actions, replanning_required, updated_plan
