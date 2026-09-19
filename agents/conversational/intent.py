import re
from typing import Any, Dict, Optional, Tuple

from .schemas import ConversationalQuery, ExtractedEntities, IntentType


class QueryUnderstanding:
    """
    Component for extracting intent, entities, language, and confidence from user queries.
    Uses pattern matching and entity detection, designed to be robust and deterministic.
    """

    KNOWN_LOCATIONS = [
        "jalandhar", "patiala", "ludhiana", "amritsar", "bathinda",
        "mohali", "chandigarh", "punjab", "delhi", "mumbai", "haryana",
        "pathankot", "hoshiarpur", "gurdaspur", "ferozepur", "sangrur"
    ]

    KNOWN_CROPS = {
        "wheat": "wheat",
        "gehu": "wheat",
        "गेहूं": "wheat",
        "ਕਣਕ": "wheat",
        "paddy": "paddy",
        "rice": "paddy",
        "chawal": "paddy",
        "चावल": "paddy",
        "ਚੌਲ": "paddy",
        "potato": "potato",
        "aalu": "potato",
        "आलू": "potato",
        "ਆਲੂ": "potato",
        "cotton": "cotton",
        "kapas": "cotton",
        "कपास": "cotton",
        "sugarcane": "sugarcane",
        "ganna": "sugarcane",
        "गन्ना": "sugarcane",
        "maize": "maize",
        "makki": "maize",
        "मक्का": "maize",
        "ਮੱਕੀ": "maize",
    }

    TIME_PATTERNS = [
        (r"\btomorrow\b", "tomorrow"),
        (r"\btoday\b", "today"),
        (r"\bnow\b", "today"),
        (r"\bright now\b", "today"),
        (r"\bnext (\d+) days?\b", r"next \1 days"),
        (r"\bthis week\b", "this week"),
        (r"\bआज\b", "today"),
        (r"\bकल\b", "tomorrow"),
        (r"\bਅੱਜ\b", "today"),
        (r"\bਕੱਲ੍ਹ\b", "tomorrow"),
    ]

    def detect_language(self, text: str) -> str:
        """Detect language: English (en), Hindi (hi), or Punjabi (pa)."""
        # Check Gurmukhi script (Punjabi)
        if re.search(r"[\u0A00-\u0A7F]", text):
            return "pa"
        # Check Devanagari script (Hindi)
        if re.search(r"[\u0900-\u097F]", text):
            return "hi"
        return "en"

    def extract_entities(self, query: str) -> ExtractedEntities:
        """Extract location, time reference, crop, farmer ID, and language from text."""
        query_lower = query.lower()
        language = self.detect_language(query)

        # 1. Location extraction
        location: Optional[str] = None
        for loc in self.KNOWN_LOCATIONS:
            if re.search(rf"\b{loc}\b", query_lower):
                location = loc.capitalize()
                break

        if not location:
            # Match "in <City>" or "at <City>"
            match = re.search(r"\b(?:in|at|for|near|में|ਵਿੱਚ)\s+([A-Za-z]+)\b", query, re.IGNORECASE)
            if match:
                extracted = match.group(1).capitalize()
                if extracted.lower() not in ["the", "my", "this", "today", "tomorrow"]:
                    location = extracted

        # 2. Crop extraction
        crop: Optional[str] = None
        for key, normalized in self.KNOWN_CROPS.items():
            if key in query_lower:
                crop = normalized
                break

        # 3. Time reference extraction
        time_reference: Optional[str] = None
        for pattern, replacement in self.TIME_PATTERNS:
            match = re.search(pattern, query_lower)
            if match:
                time_reference = re.sub(pattern, replacement, match.group(0))
                break

        # 4. Farmer ID extraction
        farmer_id: Optional[str] = None
        farmer_match = re.search(r"\b(F\d{3})\b", query, re.IGNORECASE)
        if farmer_match:
            farmer_id = farmer_match.group(1).upper()

        return ExtractedEntities(
            location=location,
            time_reference=time_reference,
            crop=crop,
            farmer_id=farmer_id,
            language=language,
            confidence=0.95 if (location or crop or time_reference) else 0.85,
        )

    def classify_intent(self, query: str, entities: ExtractedEntities) -> Tuple[IntentType, float]:
        """Classify user intent deterministically with confidence score."""
        q = query.lower()

        # EMERGENCY
        if any(w in q for w in ["emergency", "sos", "danger", "disaster", "help me", "आपातकाल", "ਖ਼ਤਰਾ", "ਇਮਰਜੈਂਸੀ"]):
            return IntentType.EMERGENCY, 0.99

        # AGRICULTURE_EXPLANATION
        if any(phrase in q for phrase in [
            "why did you postpone", "why was my", "why postponed", "why spray rescheduled",
            "why farm plan changed", "irrigation postponed", "why was irrigation",
            "क्यों स्थगित", "ਕਿਉਂ ਮੁਲਤਵੀ"
        ]):
            return IntentType.AGRICULTURE_EXPLANATION, 0.95

        # AGRICULTURE
        if any(word in q for word in [
            "irrigate", "irrigation", "spray", "crop", "harvest", "fertilizer",
            "should i", "farmers do today", "what should farmers", "farm plan",
            "सिंचाई", "फसल", "ਖੇਤੀ", "ਫ਼ਸਲ", "ਸਿੰਚਾਈ", "ਛਿੜਕਾਅ"
        ]) or entities.crop is not None:
            return IntentType.AGRICULTURE, 0.92

        # CLIMATE
        if any(phrase in q for phrase in [
            "trend", "climate", "over the years", "historical", "20 years ago",
            "past 10 years", "past years", "changed over", "जलवायु", "ਜਲਵਾਯੂ"
        ]):
            return IntentType.CLIMATE, 0.90

        # WARNING
        if any(word in q for word in [
            "warning", "alert", "cyclone", "severe weather", "heavy rain warning",
            "storm warning", "चेतावनी", "ਚੇਤਾਵਨੀ", "ਖ਼ਤਰਾ"
        ]):
            return IntentType.WARNING, 0.92

        # FORECAST
        if (
            entities.time_reference in ["tomorrow", "next 3 days", "this week"]
            or any(word in q for word in ["forecast", "tomorrow", "will it rain", "upcoming weather", "अगले", "ਭਵਿੱਖਬਾਣੀ"])
        ):
            return IntentType.FORECAST, 0.94

        # WEATHER
        if any(word in q for word in [
            "weather", "temperature", "temp", "humidity", "rain right now",
            "is it raining", "current weather", "weather in", "मौसम", "ਮੌਸਮ"
        ]):
            return IntentType.WEATHER, 0.95

        # GENERAL_WEATHER
        if any(phrase in q for phrase in ["how is weather", "weather report", "climate condition"]):
            return IntentType.GENERAL_WEATHER, 0.85

        return IntentType.UNKNOWN, 0.50

    def parse(
        self,
        query: str,
        override_location: Optional[str] = None,
        override_farmer_id: Optional[str] = None,
        override_crop: Optional[str] = None,
        override_language: Optional[str] = None,
    ) -> ConversationalQuery:
        """
        Parse a raw query string into a structured ConversationalQuery schema.
        """
        entities = self.extract_entities(query)

        # Apply overrides if explicitly passed
        location = override_location or entities.location
        farmer_id = override_farmer_id or entities.farmer_id
        crop = override_crop or entities.crop
        language = override_language or entities.language

        intent, confidence = self.classify_intent(query, entities)

        requires_agent = intent in [
            IntentType.AGRICULTURE,
            IntentType.AGRICULTURE_EXPLANATION,
            IntentType.WARNING,
            IntentType.EMERGENCY,
        ]

        requires_weather_data = intent in [
            IntentType.WEATHER,
            IntentType.FORECAST,
            IntentType.WARNING,
            IntentType.AGRICULTURE,
        ]

        requires_historical_data = intent == IntentType.CLIMATE

        return ConversationalQuery(
            query=query,
            intent=intent,
            location=location,
            time_reference=entities.time_reference,
            crop=crop,
            farmer_id=farmer_id,
            language=language,
            confidence=confidence,
            entities={
                "location": location,
                "crop": crop,
                "time_reference": entities.time_reference,
                "farmer_id": farmer_id,
                "language": language,
            },
            requires_agent=requires_agent,
            requires_weather_data=requires_weather_data,
            requires_historical_data=requires_historical_data,
        )
