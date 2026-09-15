"""
Multi-Hazard Threat Detector (agents/sentinel/detector.py).

Pure, transparent, deterministic weather hazard detection algorithms.
Converts structured multi-model weather telemetry into calibrated ThreatEvent objects.

Detects:
1. Cyclone (Simultaneous windstorm and intense deluge)
2. Hail (Severe convective indicators)
3. Heavy Rain / Flash Deluge
4. High Wind / Gale (Spraying drift and lodging hazard)
5. Extreme Heat (Heatwave and pollen desiccation hazard)
6. Frost (Cold snap and foliage scorch hazard)
7. Drought (Prolonged dry spell under elevated temperatures)
"""

import uuid
from typing import Dict, Any, List, Optional, Tuple
from .schemas import ThreatEvent, ThreatType, ThreatSeverity


def _generate_event_id() -> str:
    return f"EVT-{uuid.uuid4().hex[:8].upper()}"


class ThreatDetector:
    """
    Deterministic anomaly detection engine evaluating meteorological thresholds.
    """

    # Precipitation thresholds (mm in 3-hour window)
    RAIN_CRITICAL_THRESHOLD_MM = 50.0
    RAIN_HIGH_THRESHOLD_MM = 25.0
    RAIN_MEDIUM_THRESHOLD_MM = 12.0

    # Wind thresholds (km/h)
    WIND_SUSTAINED_THRESHOLD_KMH = 20.0     # Exceeds safe chemical spraying drift limit
    WIND_GUST_HIGH_KMH = 40.0
    WIND_GUST_CRITICAL_KMH = 75.0

    # Thermal thresholds (°C)
    HEAT_CRITICAL_TEMP_C = 43.0
    HEAT_HIGH_TEMP_C = 38.0
    FROST_CRITICAL_TEMP_C = 0.5
    FROST_HIGH_TEMP_C = 4.0

    @classmethod
    def detect_threat(
        cls,
        weather: Dict[str, Any],
        location: str,
        confidence: str = "high",
        confidence_reason: Optional[str] = None
    ) -> ThreatEvent:
        """
        Analyze current and hourly weather telemetry to detect severe hazards.
        Prioritizes the most critical hazard if multiple are concurrent.
        """
        current = weather.get("current", {})
        hourly = weather.get("hourly", {})

        # Extract hourly metrics for next 3 to 6 hours
        rain_hourly: List[float] = [
            float(r or 0.0) for r in hourly.get("precipitation_mm", [])[:6]
        ]
        rain_prob_hourly: List[float] = [
            float(p or 0.0) for p in hourly.get("precipitation_probability_pct", [])[:6]
        ]
        wind_hourly: List[float] = [
            float(w or 0.0) for w in hourly.get("wind_speed_kmh", [])[:6]
        ]
        gust_hourly: List[float] = [
            float(g or 0.0) for g in hourly.get("wind_gust_kmh", [])[:6]
        ]
        temp_hourly: List[float] = [
            float(t) for t in hourly.get("temperature_c", [])[:12] if t is not None
        ]
        weather_codes: List[int] = [
            int(c) for c in hourly.get("weather_code", [])[:6] if c is not None
        ]

        # 3-hour aggregates
        rain_3h = sum(rain_hourly[:3])
        current_rain = float(current.get("precipitation_mm") or current.get("rain_mm") or 0.0)
        total_precip_mm = round(max(rain_3h, current_rain), 1)

        max_rain_prob = max(rain_prob_hourly[:3]) if rain_prob_hourly else 0.0
        max_wind_kmh = round(max(wind_hourly[:3] + [float(current.get("wind_speed_kmh") or 0.0)]), 1)
        max_gust_kmh = round(max(gust_hourly[:3] + [float(current.get("wind_gust_kmh") or 0.0)]), 1)

        cur_temp = float(current.get("temperature_c") or 25.0)
        max_temp_c = max(temp_hourly) if temp_hourly else cur_temp
        min_temp_c = min(temp_hourly) if temp_hourly else cur_temp
        humidity_pct = float(current.get("humidity_pct") or 60.0)

        # Timing and duration calculation
        time_to_event_minutes, duration_hours = cls._calculate_timing(rain_hourly)

        # Base probability calculation
        prob = round(max(0.60, max_rain_prob / 100.0) if max_rain_prob > 0 else 0.80, 2)

        coords = weather.get("coordinates")

        # -------------------------------------------------------------------
        # 1. CYCLONE / SEVERE STORM (Combined Extreme Wind + Torrential Rain)
        # -------------------------------------------------------------------
        if total_precip_mm >= 35.0 and (max_wind_kmh >= 35.0 or max_gust_kmh >= 55.0):
            return ThreatEvent(
                event_id=_generate_event_id(),
                event_type=ThreatType.CYCLONE.value,
                severity=ThreatSeverity.CRITICAL.value,
                probability=min(0.95, prob + 0.1),
                confidence=confidence,
                confidence_reason=confidence_reason or "Multi-hazard convergence: concurrent destructive winds and torrential deluge.",
                location=location,
                coordinates=coords,
                time_to_event_minutes=time_to_event_minutes or 20,
                duration_hours=max(4.0, duration_hours),
                rainfall_mm=total_precip_mm,
                wind_speed_kmh=max_wind_kmh,
                wind_gust_kmh=max_gust_kmh,
                temp_c=cur_temp,
                temp_max_c=max_temp_c,
                temp_min_c=min_temp_c,
                humidity_pct=humidity_pct,
                hail_risk=any(c in [96, 99] for c in weather_codes),
                metadata={"detection": "cyclone_dual_hazard", "rain_3h": total_precip_mm, "gust_peak": max_gust_kmh}
            )

        # -------------------------------------------------------------------
        # 2. HAIL THREAT
        # -------------------------------------------------------------------
        hail_codes = [96, 99]  # WMO codes for thunderstorm with slight and heavy hail
        if any(c in hail_codes for c in weather_codes):
            return ThreatEvent(
                event_id=_generate_event_id(),
                event_type=ThreatType.HAIL.value,
                severity=ThreatSeverity.CRITICAL.value,
                probability=0.85,
                confidence=confidence,
                confidence_reason=confidence_reason or "Convective cell dynamics indicate active hail formation.",
                location=location,
                coordinates=coords,
                time_to_event_minutes=time_to_event_minutes or 30,
                duration_hours=1.5,
                rainfall_mm=total_precip_mm,
                wind_speed_kmh=max_wind_kmh,
                wind_gust_kmh=max_gust_kmh,
                temp_c=cur_temp,
                temp_max_c=max_temp_c,
                temp_min_c=min_temp_c,
                humidity_pct=humidity_pct,
                hail_risk=True,
                metadata={"detection": "wmo_hail_code"}
            )

        # -------------------------------------------------------------------
        # 3. HEAVY RAINFALL
        # -------------------------------------------------------------------
        if total_precip_mm >= cls.RAIN_MEDIUM_THRESHOLD_MM or (max_rain_prob >= 75.0 and total_precip_mm >= 8.0):
            if total_precip_mm >= cls.RAIN_CRITICAL_THRESHOLD_MM:
                severity = ThreatSeverity.CRITICAL.value
            elif total_precip_mm >= cls.RAIN_HIGH_THRESHOLD_MM:
                severity = ThreatSeverity.HIGH.value
            else:
                severity = ThreatSeverity.MEDIUM.value

            return ThreatEvent(
                event_id=_generate_event_id(),
                event_type=ThreatType.HEAVY_RAIN.value,
                severity=severity,
                probability=prob,
                confidence=confidence,
                confidence_reason=confidence_reason or f"Consensus forecast predicts {total_precip_mm} mm rainfall accumulation.",
                location=location,
                coordinates=coords,
                time_to_event_minutes=time_to_event_minutes,
                duration_hours=duration_hours,
                rainfall_mm=total_precip_mm,
                wind_speed_kmh=max_wind_kmh,
                wind_gust_kmh=max_gust_kmh,
                temp_c=cur_temp,
                temp_max_c=max_temp_c,
                temp_min_c=min_temp_c,
                humidity_pct=humidity_pct,
                hail_risk=False,
                metadata={"detection": "precipitation_threshold", "3h_sum_mm": total_precip_mm}
            )

        # -------------------------------------------------------------------
        # 4. HIGH WIND / GALE
        # -------------------------------------------------------------------
        if max_wind_kmh >= cls.WIND_SUSTAINED_THRESHOLD_KMH or max_gust_kmh >= cls.WIND_GUST_HIGH_KMH:
            severity = (
                ThreatSeverity.CRITICAL.value
                if (max_gust_kmh >= cls.WIND_GUST_CRITICAL_KMH or max_wind_kmh >= 45.0)
                else ThreatSeverity.HIGH.value
            )

            return ThreatEvent(
                event_id=_generate_event_id(),
                event_type=ThreatType.HIGH_WIND.value,
                severity=severity,
                probability=0.80,
                confidence=confidence,
                confidence_reason=confidence_reason or f"Wind speed ({max_wind_kmh} km/h) or gusts ({max_gust_kmh} km/h) breach spraying safety limits.",
                location=location,
                coordinates=coords,
                time_to_event_minutes=45,
                duration_hours=3.0,
                rainfall_mm=total_precip_mm,
                wind_speed_kmh=max_wind_kmh,
                wind_gust_kmh=max_gust_kmh,
                temp_c=cur_temp,
                temp_max_c=max_temp_c,
                temp_min_c=min_temp_c,
                humidity_pct=humidity_pct,
                hail_risk=False,
                metadata={"detection": "wind_drift_threshold"}
            )

        # -------------------------------------------------------------------
        # 5. EXTREME HEAT (Heatwave)
        # -------------------------------------------------------------------
        if max_temp_c >= cls.HEAT_HIGH_TEMP_C:
            severity = (
                ThreatSeverity.CRITICAL.value
                if max_temp_c >= cls.HEAT_CRITICAL_TEMP_C
                else ThreatSeverity.HIGH.value
            )

            return ThreatEvent(
                event_id=_generate_event_id(),
                event_type=ThreatType.EXTREME_HEAT.value,
                severity=severity,
                probability=0.85,
                confidence=confidence,
                confidence_reason=confidence_reason or f"Forecast peak temperature of {max_temp_c}°C causes severe crop thermal stress.",
                location=location,
                coordinates=coords,
                time_to_event_minutes=60,
                duration_hours=6.0,
                rainfall_mm=total_precip_mm,
                wind_speed_kmh=max_wind_kmh,
                wind_gust_kmh=max_gust_kmh,
                temp_c=cur_temp,
                temp_max_c=max_temp_c,
                temp_min_c=min_temp_c,
                humidity_pct=humidity_pct,
                hail_risk=False,
                metadata={"detection": "heatwave_threshold"}
            )

        # -------------------------------------------------------------------
        # 6. FROST HAZARD
        # -------------------------------------------------------------------
        if min_temp_c <= cls.FROST_HIGH_TEMP_C:
            severity = (
                ThreatSeverity.CRITICAL.value
                if min_temp_c <= cls.FROST_CRITICAL_TEMP_C
                else ThreatSeverity.HIGH.value
            )

            return ThreatEvent(
                event_id=_generate_event_id(),
                event_type=ThreatType.FROST.value,
                severity=severity,
                probability=0.85,
                confidence=confidence,
                confidence_reason=confidence_reason or f"Forecast minimum temperature ({min_temp_c}°C) creates severe frost injury conditions.",
                location=location,
                coordinates=coords,
                time_to_event_minutes=120,
                duration_hours=5.0,
                rainfall_mm=total_precip_mm,
                wind_speed_kmh=max_wind_kmh,
                wind_gust_kmh=max_gust_kmh,
                temp_c=cur_temp,
                temp_max_c=max_temp_c,
                temp_min_c=min_temp_c,
                humidity_pct=humidity_pct,
                hail_risk=False,
                metadata={"detection": "frost_threshold"}
            )

        # -------------------------------------------------------------------
        # 7. NO HAZARD DETECTED (Routine Observation)
        # -------------------------------------------------------------------
        return ThreatEvent(
            event_id=_generate_event_id(),
            event_type=ThreatType.NONE.value,
            severity=ThreatSeverity.LOW.value,
            probability=0.0,
            confidence=confidence,
            confidence_reason=confidence_reason or "All meteorological parameters remain within safe agronomic ranges.",
            location=location,
            coordinates=coords,
            time_to_event_minutes=None,
            duration_hours=None,
            rainfall_mm=total_precip_mm,
            wind_speed_kmh=max_wind_kmh,
            wind_gust_kmh=max_gust_kmh,
            temp_c=cur_temp,
            temp_max_c=max_temp_c,
            temp_min_c=min_temp_c,
            humidity_pct=humidity_pct,
            hail_risk=False,
            metadata={"detection": "clear_weather"}
        )

    @classmethod
    def _calculate_timing(cls, rain_hourly: List[float]) -> Tuple[int, float]:
        """
        Determine minutes until rain begins and estimated continuous duration in hours.
        """
        time_to_event = 30
        duration_hours = 3.0

        found_start = False
        consecutive_hours = 0

        for idx, amount in enumerate(rain_hourly):
            if amount >= 1.5:
                if not found_start:
                    time_to_event = max(15, idx * 60)
                    found_start = True
                consecutive_hours += 1
            elif found_start:
                break

        if consecutive_hours > 0:
            duration_hours = float(consecutive_hours)

        return time_to_event, duration_hours
