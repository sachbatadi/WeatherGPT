"""Background-monitoring primitives for scheduled or manual execution."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable, Dict, List


def run_monitoring_cycle(
    farmers: List[Dict[str, Any]],
    pipeline_runner: Callable[[Dict[str, Any]], Dict[str, Any]],
    mode: str = "mock",
) -> Dict[str, Any]:
    """Run deterministic weather checks for registered farmers.

    The caller owns scheduling. This function deliberately makes no autonomous
    external side effects beyond the already-audited pipeline runner.
    """
    results = []
    for farmer in farmers:
        result = pipeline_runner({"location": farmer["location"], "mode": mode})
        results.append({
            "farmer_id": farmer["farmer_id"],
            "location": farmer["location"],
            "threat_detected": result.get("threat_detected", False),
            "risk_level": result.get("risk_level"),
        })
    return {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "mode": mode,
        "farmers_checked": len(results),
        "threats_detected": sum(1 for result in results if result["threat_detected"]),
        "results": results,
    }
