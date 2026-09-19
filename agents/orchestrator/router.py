import sys

from .state import WeatherState


def _safe_print(text: str) -> None:
    """Safe print helper for Windows console encoding."""
    try:
        print(text)
    except (UnicodeEncodeError, UnicodeError):
        enc = getattr(sys.stdout, "encoding", None) or "utf-8"
        print(text.encode(enc, errors="replace").decode(enc))


def threat_router(state: WeatherState) -> str:
    """
    Routes the workflow based on Sentinel's threat detection.

    Threat detected:
        Sentinel → Strategist

    No threat:
        Sentinel → Monitor/END
    """

    if state.get("threat_detected", False):
        return "strategist"

    return "monitor"