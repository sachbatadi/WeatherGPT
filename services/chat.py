"""Grounded, deterministic conversational response construction.

This module parses user intents and grounds responses strictly in structured
weather and risk facts. When GEMINI_API_KEY is configured, an optional
fact-constrained generation call can format natural explanations, but it is
never permitted to invent numerical values. Without an API key or upon failure,
it falls back transparently to deterministic templates.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional
import requests


def detect_intent(message: str) -> str:
    text = message.lower()
    if any(word in text for word in (
        "why postpone", "why delay", "why cancel", "why reschedul",
        "why change", "why did you", "kyun roka", "kyun tala", "kyun",
        "reason for", "explain plan", "explain my plan"
    )):
        return "why_replan"
    if any(word in text for word in ("spray", "pesticide", "fungicide", "keetnashak")):
        return "spraying_safety"
    if any(word in text for word in ("irrigat", "water crop", "sinchai", "paani")):
        return "irrigation"
    if any(word in text for word in ("rain", "weather", "forecast", "temperature", "wind", "mausam")):
        return "weather_status"
    return "general_advisory"


def _format_facts(
    weather: Dict[str, Any],
    farmer: Optional[Dict[str, Any]] = None
) -> List[str]:
    """Compile structured fact strings from verified data only."""
    threat = weather.get("threat_type", "none")
    severity = weather.get("threat_severity", "low")
    temp = weather.get("temperature_c")
    rain = weather.get("precipitation_mm")
    wind = weather.get("wind_speed_kmh")
    location = weather.get("location", "the selected location")

    facts: List[str] = [f"Location: {location}"]
    if temp is not None:
        facts.append(f"Temperature: {temp}°C")
    if rain is not None:
        facts.append(f"Precipitation: {rain} mm")
    if wind is not None:
        facts.append(f"Wind: {wind} km/h")
    facts.append(f"Verified threat: {threat} ({severity})")

    if farmer:
        facts.append(f"Farmer: {farmer.get('name', 'Registered Farmer')}")
        if farmer.get("crop"):
            stage = f" ({farmer.get('crop_stage')})" if farmer.get("crop_stage") else ""
            facts.append(f"Crop: {farmer.get('crop')}{stage}")
        if farmer.get("soil_type"):
            facts.append(f"Soil type: {farmer.get('soil_type')}")

    return facts


def _format_deterministic_reply(
    intent: str,
    threat: str,
    facts: List[str],
    farmer: Optional[Dict[str, Any]] = None,
    language: str = "en"
) -> str:
    """Generate deterministic, grounded text based on intent and language."""
    if language == "hi":
        if intent == "spraying_safety":
            recommendation = (
                "कीटनाशक छिड़काव तुरंत टालें।"
                if threat in {"heavy_rain", "high_wind", "cyclone"}
                else "वर्तमान मौसम के अनुसार छिड़काव में कोई अतिरिक्त जोखिम नहीं है।"
            )
        elif intent == "irrigation":
            recommendation = (
                "सिंचाई तुरंत रोक दें।"
                if threat in {"heavy_rain", "cyclone"}
                else "सिंचाई से पहले मिट्टी की नमी जांचें; वर्तमान डेटा में बारिश का कोई अलर्ट नहीं है।"
            )
        elif intent == "why_replan":
            recommendation = (
                f"सत्यापित खतरे ({threat}) के कारण आपका शेड्यूल बदला गया ताकि फसल को नुकसान न हो।"
            )
        elif intent == "weather_status":
            recommendation = "अपने निर्णय के लिए नीचे दिए गए सत्यापित मौसम डेटा का उपयोग करें।"
        else:
            recommendation = "यह सलाह केवल नीचे दी गई सत्यापित मौसम जानकारी पर आधारित है।"
        return f"{recommendation} " + "; ".join(facts) + "।"

    elif language == "pa":
        if intent == "spraying_safety":
            recommendation = (
                "ਸਪਰੇਅ ਦਾ ਕੰਮ ਤੁਰੰਤ ਮੁਲਤਵੀ ਕਰੋ।"
                if threat in {"heavy_rain", "high_wind", "cyclone"}
                else "ਮੌਜੂਦਾ ਮੌਸਮ ਅਨੁਸਾਰ ਸਪਰੇਅ ਲਈ ਕੋਈ ਵਾਧੂ ਖ਼ਤਰਾ ਨਹੀਂ ਹੈ।"
            )
        elif intent == "irrigation":
            recommendation = (
                "ਪਾਣੀ ਲਾਉਣਾ ਤੁਰੰਤ ਰੋਕ ਦਿਓ।"
                if threat in {"heavy_rain", "cyclone"}
                else "ਪਾਣੀ ਲਾਉਣ ਤੋਂ ਪਹਿਲਾਂ ਮਿੱਟੀ ਦੀ ਨਮੀ ਦੀ ਜਾਂਚ ਕਰੋ।"
            )
        elif intent == "why_replan":
            recommendation = (
                f"ਸੂਚਿਤ ਖ਼ਤਰੇ ({threat}) ਕਾਰਨ ਤੁਹਾਡਾ ਸ਼ਡਿਊਲ ਬਦਲਿਆ ਗਿਆ ਹੈ ਤਾਂ ਜੋ ਫ਼ਸਲ ਦਾ ਨੁਕਸਾਨ ਨਾ ਹੋਵੇ।"
            )
        elif intent == "weather_status":
            recommendation = "ਆਪਣੇ ਫੈਸਲੇ ਲਈ ਹੇਠਾਂ ਦਿੱਤੇ ਸਹੀ ਮੌਸਮ ਡੇਟਾ ਦੀ ਵਰਤੋਂ ਕਰੋ ਜੀ।"
        else:
            recommendation = "ਇਹ ਸਲਾਹ ਹੇਠਾਂ ਦਿੱਤੀ ਗਈ ਸਹੀ ਮੌਸਮ ਜਾਣਕਾਰੀ 'ਤੇ ਆਧਾਰਿਤ ਹੈ।"
        return f"{recommendation} " + "; ".join(facts) + "।"

    # Default: English
    if intent == "spraying_safety":
        recommendation = (
            "Postpone spraying"
            if threat in {"heavy_rain", "high_wind", "cyclone"}
            else "Spraying risk is not elevated by the current structured result."
        )
    elif intent == "irrigation":
        recommendation = (
            "Postpone irrigation"
            if threat in {"heavy_rain", "cyclone"}
            else "Check soil moisture before irrigating; no rainfall-based stop is present in this result."
        )
    elif intent == "why_replan":
        crop_info = f" for your {farmer.get('crop')}" if farmer and farmer.get("crop") else ""
        recommendation = f"Schedule was adjusted{crop_info} to avoid operational damage from incoming {threat}."
    elif intent == "weather_status":
        recommendation = "Use the structured weather values below for your decision."
    else:
        recommendation = "This advisory is based only on the verified weather and risk fields below."

    return f"{recommendation} " + "; ".join(facts) + "."


def _call_gemini_grounded(
    message: str,
    facts: List[str],
    recommendation: str,
    language: str,
    api_key: str
) -> Optional[str]:
    """Optional fact-constrained LLM rephrasing via Google Gemini REST API."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    system_instruction = (
        "You are WeatherGPT Assistant, an agricultural decision support system for Indian farmers. "
        "Strict Rule: You must ONLY use the provided facts. Never invent, guess, or extrapolate any "
        "numerical weather values (temperatures, rainfall, wind speeds, dates) or risks. "
        f"Respond in language: {language}. Be clear, polite, and concise."
    )
    prompt = (
        f"Farmer Query: {message}\n\n"
        f"Verified Facts:\n- " + "\n- ".join(facts) + "\n\n"
        f"Core Recommendation: {recommendation}\n\n"
        "Provide a concise, grounded explanation based ONLY on these facts."
    )
    payload = {
        "system_instruction": {"parts": [{"text": system_instruction}]},
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.2, "maxOutputTokens": 200},
    }
    try:
        resp = requests.post(url, json=payload, timeout=4)
        if resp.status_code == 200:
            candidates = resp.json().get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts and parts[0].get("text"):
                    return parts[0]["text"].strip()
    except Exception:
        pass
    return None


def build_grounded_reply(
    message: str,
    weather: Dict[str, Any],
    farmer: Optional[Dict[str, Any]] = None,
    language: str = "en"
) -> Dict[str, Any]:
    """Return a concise reply strictly grounded in fields present in ``weather`` and ``farmer``."""
    intent = detect_intent(message)
    threat = weather.get("threat_type", "none")
    facts = _format_facts(weather, farmer)

    deterministic_reply = _format_deterministic_reply(
        intent=intent,
        threat=threat,
        facts=facts,
        farmer=farmer,
        language=language
    )

    llm_used = False
    final_reply = deterministic_reply

    # Check for optional GEMINI_API_KEY
    gemini_key = os.getenv("GEMINI_API_KEY")
    if gemini_key and gemini_key.strip():
        gemini_text = _call_gemini_grounded(
            message=message,
            facts=facts,
            recommendation=deterministic_reply,
            language=language,
            api_key=gemini_key.strip()
        )
        if gemini_text:
            final_reply = gemini_text
            llm_used = True

    return {
        "intent": intent,
        "reply": final_reply,
        "grounding": {
            "weather": weather,
            "farmer": farmer,
            "facts_used": facts
        },
        "llm_used": llm_used,
    }
