"""
Agricultural Risk Engine (Module 5 & Module 9).

Deterministic, transparent agronomic risk calculations based on:
1. Multi-source weather parameters (Rainfall, Wind speed, Temp, Humidity, Probability, Confidence)
2. Soil hydrology (Infiltration rate, water retention, and dynamic drying days)
3. Crop biology & Growth Stage Sensitivity (Wheat, Rice, Cotton, Tomato, Mustard, Maize, Potato, etc.)
4. Active farm calendar interference (Irrigation, Spraying, Fertilization, Harvesting)
5. Disease & Pathogen epidemiology (Late blight in potato/tomato, rust in wheat, blast in paddy)
6. Next observation window calculation for continuous monitoring.
"""

from typing import Dict, Any, List, Tuple
from .schemas import (
    SeverityLevel,
    ActionType,
    UrgencyLevel,
    ActionItem,
    FarmerProfile,
    FarmActivity,
    RiskBreakdown,
    NextObservationTrigger
)


# Crop vulnerability multipliers by growth stage
STAGE_SENSITIVITY: Dict[str, Dict[str, float]] = {
    "wheat": {
        "sowing": 1.2,          # Sensitive to waterlogging / seed rot
        "vegetative": 0.8,      # Highly resilient
        "flowering": 1.5,       # Highly sensitive to heavy rain (pollen wash) & heat stress
        "grain_filling": 1.3,   # Vulnerable to terminal heat stress and lodging
        "maturity": 1.4,        # Vulnerable to rain / grain sprouting
        "harvesting": 1.5       # Vulnerable to rainfall spoilage
    },
    "rice": {
        "sowing": 1.1,
        "vegetative": 0.7,      # High water tolerance
        "flowering": 1.4,       # Wind and deluge cause empty panicles
        "grain_filling": 1.1,
        "maturity": 1.4,
        "harvesting": 1.5
    },
    "cotton": {
        "sowing": 1.2,
        "vegetative": 0.9,
        "flowering": 1.4,       # Square shedding on excess moisture
        "grain_filling": 1.3,   # Boll development
        "maturity": 1.5,        # Deluge stains and damages open cotton bolls
        "harvesting": 1.5
    },
    "tomato": {
        "sowing": 1.3,
        "vegetative": 1.1,
        "flowering": 1.5,       # Blossom drop from thermal or water stress
        "grain_filling": 1.3,   # Fruit cracking on sudden deluge
        "maturity": 1.4,
        "harvesting": 1.4
    },
    "potato": {
        "sowing": 1.3,          # Tuber rot in waterlogged soil
        "vegetative": 1.1,      # Late blight risk in humid cool conditions
        "flowering": 1.2,
        "grain_filling": 1.3,   # Tuber bulking
        "maturity": 1.4,        # Wet harvest causes rot during storage
        "harvesting": 1.5
    },
    "mustard": {
        "sowing": 1.1,
        "vegetative": 0.8,
        "flowering": 1.5,       # Frost / cloudiness causes aphid outbreak
        "grain_filling": 1.2,
        "maturity": 1.3,
        "harvesting": 1.4
    },
    "maize": {
        "sowing": 1.1,
        "vegetative": 0.9,
        "flowering": 1.4,       # Tassel desiccation or pollen wash
        "grain_filling": 1.2,
        "maturity": 1.3,
        "harvesting": 1.4
    }
}

# Soil drainage multipliers (higher = retains water longer, takes longer to dry)
SOIL_FACTORS: Dict[str, float] = {
    "clay": 1.5,
    "black_soil": 1.4,
    "silty": 1.1,
    "loamy": 1.0,
    "red_soil": 0.85,
    "sandy": 0.5
}


class RiskEngine:
    """
    Deterministic Agricultural Decision & Risk Calculation Engine.
    """

    @classmethod
    def calculate_drying_days(cls, rainfall_mm: float, soil_type: str) -> int:
        """
        Scientifically estimate days needed for soil to return to field capacity.
        Drying Days = max(2, min(10, round((rainfall_mm / 12.0) * soil_factor)))
        """
        soil_clean = soil_type.lower()
        factor = SOIL_FACTORS.get(soil_clean, 1.0)
        if rainfall_mm <= 10.0:
            return 2
        days = round((rainfall_mm / 12.0) * factor)
        return max(2, min(10, days))

    @classmethod
    def evaluate_farmer_risk(
        cls,
        threat: Dict[str, Any],
        farmer: FarmerProfile
    ) -> Tuple[
        SeverityLevel,
        float,
        RiskBreakdown,
        List[str],
        List[ActionItem],
        bool,
        List[FarmActivity],
        NextObservationTrigger
    ]:
        """
        Evaluate full risk profile, recommended actions, updated activity schedule,
        and continuous monitoring trigger.
        """
        event_type = str(threat.get("event_type", "unknown")).lower()
        threat_severity = str(threat.get("severity", "medium")).lower()
        probability = float(threat.get("probability", 0.7))
        confidence = str(threat.get("confidence", "high")).lower()

        # Weather parameters
        rainfall_mm = float(threat.get("rainfall_mm") or 0.0)
        wind_speed_kmh = float(threat.get("wind_speed_kmh") or 0.0)
        temp_c = float(threat.get("temp_c") or 25.0)
        temp_max_c = float(threat.get("temp_max_c") or temp_c)
        temp_min_c = float(threat.get("temp_min_c") or temp_c)
        humidity_pct = float(threat.get("humidity_pct") or 60.0)
        hail_risk = bool(threat.get("hail_risk", False))

        crop_name = farmer.crop.lower()
        stage_name = farmer.crop_stage.lower()
        soil_type = farmer.soil_type.lower()

        # Sub-score calculations (0-100)
        precip_risk = 0.0
        wind_risk = 0.0
        thermal_risk = 0.0
        disease_risk = 0.0

        risk_factors: List[str] = []
        actions: List[ActionItem] = []
        replanning_required = False
        updated_plan = [act.model_copy(deep=True) for act in farmer.current_plan]

        # -------------------------------------------------------------------
        # 1. PRECIPITATION & DRAINAGE EVALUATION
        # -------------------------------------------------------------------
        if "rain" in event_type or rainfall_mm >= 12.0 or "cyclone" in event_type:
            # Calculate precipitation sub-score
            precip_risk = min(100.0, (rainfall_mm / 60.0) * 80.0)
            if soil_type in ("clay", "black_soil"):
                precip_risk = min(100.0, precip_risk * 1.25)
            elif soil_type == "sandy":
                precip_risk *= 0.85

            if rainfall_mm >= 50.0:
                risk_factors.append(
                    f"Excessive rainfall anticipated: {rainfall_mm:.1f} mm may trigger flash waterlogging."
                )
            elif rainfall_mm >= 20.0:
                risk_factors.append(
                    f"Substantial rainfall expected: {rainfall_mm:.1f} mm."
                )

            # Crop stage vulnerability
            if stage_name == "flowering":
                risk_factors.append(
                    f"{farmer.crop} is in Flowering stage: rain risks washing off pollen and reducing seed set."
                )
            elif stage_name in ("maturity", "harvesting"):
                risk_factors.append(
                    f"{farmer.crop} is at Maturity/Harvest: rain can trigger seed sprouting and mould formation."
                )

            # Check planned irrigation interference
            dry_days = cls.calculate_drying_days(rainfall_mm, soil_type)
            for act in updated_plan:
                if act.activity_type.lower() == "irrigation" and act.status != "cancelled":
                    replanning_required = True
                    act.status = "postponed"
                    rescheduled_text = f"+{dry_days} days after rain ceases"

                    risk_factors.append(
                        f"Scheduled irrigation conflicts with incoming {rainfall_mm:.0f} mm rain on {soil_type} soil."
                    )
                    actions.append(
                        ActionItem(
                            action_type=ActionType.POSTPONE_IRRIGATION,
                            title="Postpone Scheduled Irrigation",
                            description=(
                                f"Cancel scheduled watering for your {farmer.crop}. Forecasted {rainfall_mm:.1f} mm "
                                f"rain will fully meet soil moisture requirements. Re-assess soil moisture in {dry_days} days."
                            ),
                            urgency=UrgencyLevel.HIGH if rainfall_mm > 30 else UrgencyLevel.MEDIUM,
                            target_date=act.scheduled_date,
                            rescheduled_date=rescheduled_text,
                            affected_activity_id=act.activity_id
                        )
                    )

            # Check planned fertilization interference (nitrogen leaching)
            for act in updated_plan:
                if act.activity_type.lower() in ("fertilization", "fertilizer") and act.status != "cancelled":
                    replanning_required = True
                    act.status = "postponed"
                    risk_factors.append(
                        "Heavy rainfall will cause nitrate leaching and nutrient runoff if fertilizer is applied now."
                    )
                    actions.append(
                        ActionItem(
                            action_type=ActionType.DELAY_FERTILIZATION,
                            title="Delay Fertilizer Application",
                            description=(
                                f"Postpone fertilizer application ({act.details.get('fertilizer', 'Urea')}). "
                                f"Applying before {rainfall_mm:.0f} mm rain wastes 40-60% of fertilizer into groundwater runoff."
                            ),
                            urgency=UrgencyLevel.HIGH,
                            target_date=act.scheduled_date,
                            rescheduled_date=f"+{max(2, dry_days - 1)} days post-rain when soil is moist",
                            affected_activity_id=act.activity_id
                        )
                    )

            # Drainage clearing advice
            if (rainfall_mm >= 35.0 or "clay" in soil_type) and rainfall_mm >= 20.0:
                actions.append(
                    ActionItem(
                        action_type=ActionType.DRAINAGE_PREPARATION,
                        title="Clear Field Drainage Channels",
                        description=(
                            f"Inspect field perimeter bunds and open drainage outlets to avoid root suffocation "
                            f"in {soil_type} soil."
                        ),
                        urgency=UrgencyLevel.HIGH if rainfall_mm >= 45.0 else UrgencyLevel.MEDIUM
                    )
                )

            # Harvest protection
            if stage_name in ("maturity", "harvesting"):
                actions.append(
                    ActionItem(
                        action_type=ActionType.EXPEDITE_HARVEST,
                        title="Expedite Harvest / Protect Produce",
                        description="Cover harvested piles with tarpaulins or move to covered threshing floors immediately.",
                        urgency=UrgencyLevel.IMMEDIATE if rainfall_mm >= 30.0 else UrgencyLevel.HIGH
                    )
                )

        # -------------------------------------------------------------------
        # 2. HIGH WIND & SPRAY DRIFT EVALUATION
        # -------------------------------------------------------------------
        if "wind" in event_type or wind_speed_kmh >= 18.0 or "cyclone" in event_type:
            wind_risk = min(100.0, (wind_speed_kmh / 50.0) * 90.0)
            risk_factors.append(f"High wind speeds forecasted: {wind_speed_kmh:.1f} km/h.")

            if wind_speed_kmh >= 32.0 and stage_name in ("grain_filling", "maturity"):
                risk_factors.append(f"Tall {farmer.crop} crop is at risk of lodging/falling flat.")

            # Spray interference
            for act in updated_plan:
                if act.activity_type.lower() == "spraying" and act.status != "cancelled":
                    replanning_required = True
                    act.status = "postponed"
                    actions.append(
                        ActionItem(
                            action_type=ActionType.RESCHEDULE_SPRAY,
                            title="Halt Spraying due to Wind Drift",
                            description=(
                                f"Wind speed of {wind_speed_kmh:.1f} km/h exceeds the 15 km/h safety threshold. "
                                f"Postpone pesticide application to avoid dangerous drift and poor canopy coverage."
                            ),
                            urgency=UrgencyLevel.HIGH,
                            target_date=act.scheduled_date,
                            rescheduled_date="When wind speed subsides below 15 km/h",
                            affected_activity_id=act.activity_id
                        )
                    )

        # -------------------------------------------------------------------
        # 3. THERMAL STRESS (HEATWAVE / FROST)
        # -------------------------------------------------------------------
        if "heat" in event_type or temp_max_c >= 38.0:
            thermal_risk = min(100.0, max(0.0, (temp_max_c - 35.0) * 15.0))
            risk_factors.append(f"Extreme heat stress: forecast high of {temp_max_c:.1f}°C.")
            if stage_name == "flowering":
                risk_factors.append("High ambient temperatures can cause pollen desiccation and blossom drop.")
                actions.append(
                    ActionItem(
                        action_type=ActionType.HEAT_STRESS_MITIGATION,
                        title="Apply Light Evening Irrigation / Mulch",
                        description=(
                            "Provide light evening sprinkler irrigation or apply straw mulching to cool "
                            "the root zone microclimate."
                        ),
                        urgency=UrgencyLevel.HIGH
                    )
                )

        if "frost" in event_type or temp_min_c <= 4.0:
            thermal_risk = max(thermal_risk, min(100.0, (5.0 - temp_min_c) * 20.0))
            risk_factors.append(f"Frost hazard: night temperature drops to {temp_min_c:.1f}°C.")
            actions.append(
                ActionItem(
                    action_type=ActionType.FROST_PROTECTION,
                    title="Implement Frost Safeguards",
                    description=(
                        "Lightly irrigate field perimeter in the late evening or create dense smoke blankets "
                        "to trap ground radiation and protect against frost scorch."
                    ),
                    urgency=UrgencyLevel.IMMEDIATE
                )
            )

        # -------------------------------------------------------------------
        # 4. DISEASE & HUMIDITY HAZARD (Fungal / Blight Risk)
        # -------------------------------------------------------------------
        if humidity_pct >= 80.0 and 14.0 <= temp_c <= 25.0:
            disease_risk = min(100.0, (humidity_pct - 75.0) * 4.0 + 30.0)
            if crop_name in ("potato", "tomato"):
                risk_factors.append(
                    f"Prolonged humidity ({humidity_pct:.0f}%) and {temp_c:.1f}°C creates ideal conditions for Late Blight (Phytophthora)."
                )
                actions.append(
                    ActionItem(
                        action_type=ActionType.DISEASE_PREVENTATIVE,
                        title="Prepare Prophylactic Fungicide Spray",
                        description=(
                            f"Inspect {farmer.crop} lower foliage for water-soaked lesions. Plan a prophylactic "
                            f"mancozeb / copper spray once rain and wind clear."
                        ),
                        urgency=UrgencyLevel.MEDIUM
                    )
                )
            elif crop_name == "wheat" and stage_name in ("vegetative", "flowering"):
                risk_factors.append(f"Persistent dampness ({humidity_pct:.0f}%) increases Yellow Rust vulnerability.")

        # -------------------------------------------------------------------
        # 5. HAIL HAZARD
        # -------------------------------------------------------------------
        if hail_risk or "hail" in event_type:
            risk_factors.append("Hail threat: severe mechanical damage to crop canopy and developing fruit.")
            precip_risk = max(precip_risk, 90.0)
            actions.append(
                ActionItem(
                    action_type=ActionType.PROTECTIVE_COVERING,
                    title="Deploy Hail Nets / Protect Nursery Beds",
                    description="Erect anti-hail netting if available and protect seedling nurseries.",
                    urgency=UrgencyLevel.IMMEDIATE
                )
            )

        # -------------------------------------------------------------------
        # Default if no actions triggered
        # -------------------------------------------------------------------
        if not actions:
            actions.append(
                ActionItem(
                    action_type=ActionType.NO_ACTION,
                    title="Maintain Current Farm Plan",
                    description="Weather forecast indicates favorable conditions; proceed with planned activities.",
                    urgency=UrgencyLevel.LOW
                )
            )

        # Calculate composite score
        crop_multipliers = STAGE_SENSITIVITY.get(crop_name, {})
        stage_mult = crop_multipliers.get(stage_name, 1.0)

        # Weighted maximum composite
        base_threat_val = {"low": 20.0, "medium": 45.0, "high": 70.0, "critical": 90.0}.get(threat_severity, 40.0)
        component_max = max(precip_risk, wind_risk, thermal_risk, disease_risk, base_threat_val)

        conf_weight = 1.0 if confidence == "high" else (0.85 if confidence == "medium" else 0.70)
        prob_weight = (probability * 0.4 + 0.6)
        raw_composite = component_max * stage_mult * conf_weight * prob_weight

        # Add interference bonus
        if replanning_required:
            raw_composite += 10.0

        final_score = max(0.0, min(100.0, round(raw_composite, 1)))

        if final_score >= 70.0:
            risk_level = SeverityLevel.CRITICAL
        elif final_score >= 48.0:
            risk_level = SeverityLevel.HIGH
        elif final_score >= 25.0:
            risk_level = SeverityLevel.MEDIUM
        else:
            risk_level = SeverityLevel.LOW

        breakdown = RiskBreakdown(
            precipitation_risk=round(precip_risk, 1),
            wind_risk=round(wind_risk, 1),
            thermal_risk=round(thermal_risk, 1),
            disease_risk=round(disease_risk, 1)
        )

        # Determine next observation window
        if rainfall_mm > 0:
            obs_trigger = NextObservationTrigger(
                trigger_type="reassess_soil_moisture",
                reassess_after_hours=max(6, int(threat.get("duration_hours", 3.0)) + 4),
                condition=f"Check if rainfall ceased and verify soil infiltration on {soil_type} field"
            )
        elif wind_speed_kmh > 15:
            obs_trigger = NextObservationTrigger(
                trigger_type="wind_normalization_check",
                reassess_after_hours=4,
                condition="Verify wind speed dropped below 15 km/h to open safe spraying window"
            )
        else:
            obs_trigger = NextObservationTrigger(
                trigger_type="routine_cycle_check",
                reassess_after_hours=12,
                condition="Routine forecast synchronization"
            )

        return (
            risk_level,
            final_score,
            breakdown,
            risk_factors,
            actions,
            replanning_required,
            updated_plan,
            obs_trigger
        )
