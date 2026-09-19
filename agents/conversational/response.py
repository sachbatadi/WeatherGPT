from typing import Any, Dict, Optional

from .schemas import ChatResponse, ConversationalQuery, GroundedResponse, IntentType


class ResponseGenerator:
    """
    Response Generator component.
    Takes grounded tool/agent data and formats clean, multi-lingual natural responses.
    Guarantees zero hallucinated weather values.
    """

    HINDI_TEMPLATES = {
        IntentType.WEATHER: "स्थान: {location}। वर्तमान तापमान {temp}°C, नमी {humidity}% और हवा की गति {wind} km/h है।",
        IntentType.WARNING: "चेतावनी: {location} के लिए गंभीर मौसम चेतावनी जारी की गई है ({event})। कृपया सुरक्षित स्थान पर रहें।",
        IntentType.AGRICULTURE: "कृषि सलाह ({location}): जोखिम स्तर - {risk}। अनुशंसित कार्य: {actions}",
        IntentType.CLIMATE: "ऐतिहासिक जलवायु रुझान डेटा वर्तमान में कनेक्टेड डेटा स्रोत के माध्यम से उपलब्ध नहीं है।",
        IntentType.EMERGENCY: "आपातकालीन चेतावनी! कृपया खेत के काम रोकें और सुरक्षित स्थान पर रहें।",
        IntentType.UNKNOWN: "मैं WeatherGPT हूँ। कृपया अपना स्थान बताएं या मौसम/कृषि संबंधी प्रश्न पूछें।",
    }

    PUNJABI_TEMPLATES = {
        IntentType.WEATHER: "ਸਥਾਨ: {location}। ਮੌਜੂਦਾ ਤਾਪਮਾਨ {temp}°C, ਨਮੀ {humidity}% ਅਤੇ ਹਵਾ ਦੀ ਰਫ਼ਤਾਰ {wind} km/h ਹੈ।",
        IntentType.WARNING: "ਚੇਤਾਵਨੀ: {location} ਲਈ ਗੰਭੀਰ ਮੌਸਮ ਚੇਤਾਵਨੀ ਜਾਰੀ ਕੀਤੀ ਗਈ ਹੈ ({event})। ਕਿਰਪਾ ਕਰਕੇ ਸੁਰੱਖਿਅਤ ਰਹੋ।",
        IntentType.AGRICULTURE: "ਖੇਤੀਬਾੜੀ ਸਲਾਹ ({location}): ਜੋਖਮ ਪੱਧਰ - {risk}। ਸਿਫਾਰਸ਼ ਕੀਤੇ ਕੰਮ: {actions}",
        IntentType.CLIMATE: "ਇਤਿਹਾਸਕ ਜਲਵਾਯੂ ਰੁਝਾਨ ਡੇਟਾ ਮੌਜੂਦਾ ਕਨੈਕਟ ਕੀਤੇ ਡੇਟਾ ਸਰੋਤ ਰਾਹੀਂ ਉਪਲਬਧ ਨਹੀਂ ਹੈ।",
        IntentType.EMERGENCY: "ਐਮਰਜੈਂਸੀ ਚੇਤਾਵਨੀ! ਕਿਰਪਾ ਕਰਕੇ ਖੇਤ ਦੇ ਕੰਮ ਰੋਕੋ ਅਤੇ ਸੁਰੱਖਿਅਤ ਸਥਾਨ 'ਤੇ ਰਹੋ।",
        IntentType.UNKNOWN: "ਮੈਂ WeatherGPT ਹਾਂ। ਕਿਰਪਾ ਕਰਕੇ ਆਪਣਾ ਸਥਾਨ ਦੱਸੋ ਜਾਂ ਮੌਸਮ/ਖੇਤੀਬਾੜੀ ਬਾਰੇ ਸਵਾਲ ਪੁੱਛੋ।",
    }

    def generate(
        self,
        grounded: GroundedResponse,
        query: ConversationalQuery,
    ) -> ChatResponse:
        """
        Formulate a ChatResponse grounded in official tool/agent data.
        """
        lang = query.language
        intent = query.intent
        raw = grounded.raw_data or {}
        location = query.location or "Jalandhar"

        if intent == IntentType.FORECAST:
            has_tomorrow = raw.get("has_tomorrow_forecast", False)
            if not has_tomorrow:
                if lang == "hi":
                    text = f"वर्तमान SIH मॉका मौसम परिदृश्य में {location} के लिए निकट-अवधि के खतरे का डेटा है, लेकिन कल के लिए समय-स्टाम्प वाला पूर्वानुमान शामिल नहीं है।"
                elif lang == "pa":
                    text = f"ਮੌਜੂਦਾ SIH ਮੌਕ ਮੌਸਮ ਦ੍ਰਿਸ਼ ਵਿੱਚ {location} ਲਈ ਨੇੜਲੇ ਭਵਿੱਖ ਦੇ ਖਤਰੇ ਦਾ ਡੇਟਾ ਹੈ, ਪਰ ਕੱਲ੍ਹ ਲਈ ਸਮਾਂ-ਸਟੈਂਪ ਵਾਲੀ ਭਵਿੱਖਬਾਣੀ ਸ਼ਾਮਲ ਨਹੀਂ ਹੈ।"
                else:
                    text = grounded.text
            else:
                text = grounded.text

        # Multi-lingual template generation if Hindi/Punjabi requested
        elif lang == "hi" and intent in self.HINDI_TEMPLATES:
            cur = raw.get("current", {})
            hly = raw.get("hourly", {})
            text = self.HINDI_TEMPLATES[intent].format(
                location=location,
                temp=cur.get("temperature_c", "N/A"),
                humidity=cur.get("humidity_pct", "N/A"),
                wind=cur.get("wind_speed_kmh", "N/A"),
                event=raw.get("event_type", "मौसम का खतरा"),
                risk=raw.get("overall_risk_level", {}).get("value", "उच्च") if isinstance(raw.get("overall_risk_level"), dict) else str(raw.get("overall_risk_level", "उच्च")),
                actions=", ".join(grounded.actions) if grounded.actions else "सामान्य खेती करें",
            )
        elif lang == "pa" and intent in self.PUNJABI_TEMPLATES:
            cur = raw.get("current", {})
            hly = raw.get("hourly", {})
            text = self.PUNJABI_TEMPLATES[intent].format(
                location=location,
                temp=cur.get("temperature_c", "N/A"),
                humidity=cur.get("humidity_pct", "N/A"),
                wind=cur.get("wind_speed_kmh", "N/A"),
                event=raw.get("event_type", "ਮੌਸਮ ਦਾ ਖ਼ਤਰਾ"),
                risk=raw.get("overall_risk_level", {}).get("value", "ਉੱਚ") if isinstance(raw.get("overall_risk_level"), dict) else str(raw.get("overall_risk_level", "ਉੱਚ")),
                actions=", ".join(grounded.actions) if grounded.actions else "ਸਧਾਰਨ ਖੇਤੀ ਕਰੋ",
            )
        else:
            text = grounded.text

        return ChatResponse(
            response=text,
            intent=intent,
            location=location,
            data_source=grounded.data_source,
            agent_used=grounded.agent_used,
            actions=grounded.actions,
            confidence=query.confidence,
            language=lang,
            raw_data=raw,
        )
