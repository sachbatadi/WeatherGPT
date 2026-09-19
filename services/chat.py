from typing import Dict, Any, Optional, List


def detect_intent(message: str) -> str:
    """Detect agricultural query intent from message text."""
    msg = (message or "").lower().strip()
    if any(w in msg for w in ["why", "replan", "postpone", "reschedule", "cancelled"]):
        return "why_replan"
    if any(w in msg for w in ["spray", "pesticide", "fungicide", "insecticide"]):
        return "spraying_safety"
    if any(w in msg for w in ["irrigate", "irrigation", "water", "watering"]):
        return "irrigation"
    if any(w in msg for w in ["harvest", "harvesting"]):
        return "harvesting"
    return "general_advisory"


def build_grounded_reply(
    message: str,
    weather: Dict[str, Any],
    farmer: Optional[Dict[str, Any]] = None,
    language: str = "en",
) -> Dict[str, Any]:
    """
    Build a grounded advisory response directly from deterministic weather facts
    and farmer profile without invoking ungrounded LLM inference.
    """
    intent = detect_intent(message)
    lang = (language or "en").strip().lower()

    # Extract weather metrics (handling nested or flat structure)
    loc = weather.get("location", "Your field")
    current = weather.get("current", {})
    temp = weather.get("temperature_c", current.get("temperature_c", 25.0))
    precip = weather.get("precipitation_mm", current.get("precipitation_mm", 0.0))
    wind = weather.get("wind_speed_kmh", current.get("wind_speed_kmh", 10.0))
    threat_type = weather.get("threat_type") or weather.get("hazard_detected") or "heavy_rain"
    severity = weather.get("threat_severity") or weather.get("severity") or "moderate"

    # Farmer details
    farmer_name = farmer.get("name", "Farmer") if farmer else "Farmer"
    crop = farmer.get("crop", "Crops") if farmer else "Crops"

    # Multilingual response formulation
    if lang == "hi":
        if intent == "irrigation":
            reply = "सिंचाई तुरंत रोक दें और जल निकासी की व्यवस्था करें।"
        elif intent == "spraying_safety":
            reply = f"मौसम खराब होने के कारण ({temp}°C, वर्षा की संभावना) कीटनाशक छिड़काव स्थगित करें।"
        elif intent == "why_replan":
            reply = f"{farmer_name} जी, {threat_type} की चेतावनी के कारण आपकी {crop} की सिंचाई स्थगित की गई है।"
        else:
            reply = f"मौसम की जानकारी के अनुसार कृषि कार्य करें। {loc} में तापमान {temp}°C है।"
    elif lang == "pa":
        if intent == "irrigation":
            reply = "ਪਾਣੀ ਲਾਉਣਾ ਤੁਰੰਤ ਰੋਕ ਦਿਓ ਅਤੇ ਨਿਕਾਸੀ ਦਾ ਪ੍ਰਬੰਧ ਕਰੋ।"
        elif intent == "spraying_safety":
            reply = f"ਖਰਾਬ ਮੌਸਮ ({temp}°C) ਕਾਰਨ ਸਪਰੇਅ ਦਾ ਕੰਮ ਮੁਲਤਵੀ ਕਰੋ।"
        elif intent == "why_replan":
            reply = f"{farmer_name} ਜੀ, {threat_type} ਅਲਰਟ ਕਾਰਨ ਤੁਹਾਡੀ {crop} ਲਈ ਸਿੰਚਾਈ ਮੁਲਤਵੀ ਕੀਤੀ ਗਈ ਹੈ।"
        else:
            reply = f"ਮੌਸਮ ਦੇ ਅਨੁਸਾਰ ਖੇਤੀਬਾੜੀ ਕੰਮ ਕਰੋ। {loc} ਵਿੱਚ ਤਾਪਮਾਨ {temp}°C ਹੈ।"
    else:
        if intent == "spraying_safety":
            reply = f"Postpone spraying due to adverse weather conditions ({temp}°C, high risk)."
        elif intent == "irrigation":
            reply = "Postpone irrigation due to expected rainfall and saturated soil conditions."
        elif intent == "why_replan":
            reply = f"Your irrigation schedule for {crop} was postponed due to an incoming {threat_type} alert."
        elif intent == "harvesting":
            reply = f"Exercise caution with harvesting for {crop} under incoming weather conditions."
        else:
            reply = f"Current weather in {loc} is {temp}°C with {precip}mm rain and {wind}km/h wind."

    # Structured grounding facts
    facts_used = [
        f"Location: {loc}",
        f"Temperature: {temp}°C",
        f"Precipitation: {precip}mm",
        f"Threat: {threat_type} ({severity})",
    ]
    if farmer:
        facts_used.append(f"Farmer: {farmer_name} ({crop})")

    return {
        "intent": intent,
        "reply": reply,
        "grounding": {
            "facts_used": facts_used,
            "data_source": "deterministic_grounding",
            "farmer": farmer,
        },
        "llm_used": False,
    }
