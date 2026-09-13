import sys
from .state import WeatherState


def _safe_print(text: str) -> None:
    try:
        print(text)
    except (UnicodeEncodeError, UnicodeError):
        enc = getattr(sys.stdout, "encoding", None) or "utf-8"
        print(text.encode(enc, errors="replace").decode(enc))


def threat_router(state: WeatherState) -> str:
    """
    Decide what the Orchestrator should do after Sentinel runs.
    """

    if state.get("threat_detected", False):
        _safe_print("\n🚨 Threat detected → Sending to Strategist")
        return "strategist"

    _safe_print("\n✅ No significant threat → Continue monitoring")
    return "monitor"