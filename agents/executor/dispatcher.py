"""
Executor Dispatcher Subsystem (agents/executor/dispatcher.py).

Handles:
1. Alert dispatch queueing (SMS, Radio-GPT telephony queue, Dashboard events)
2. Vonage SMS Provider live integration (when SMS_ENABLED=true and SMS_PROVIDER=vonage)
3. Localization of messages (English, Hindi, Punjabi)
4. Idempotency tracking to prevent duplicate alerts or operations on retries
"""

import os
import requests
from datetime import datetime, timezone
from typing import Dict, Any, List, Set, Optional

from .schemas import (
    DispatchChannel,
    TaskStatus,
    DispatchedAlert,
    DashboardEvent
)


class IdempotencyManager:
    """
    In-memory registry preventing duplicate execution of identical actions or alerts
    for a given threat event and farmer.
    """

    def __init__(self):
        self._seen_keys: Set[str] = set()

    def make_key(
        self,
        threat_id: str,
        farmer_id: str,
        action_type: str,
        item_id: Optional[str] = None
    ) -> str:
        return f"{threat_id}:{farmer_id}:{action_type}:{item_id or 'none'}"

    def is_duplicate(self, key: str) -> bool:
        return key in self._seen_keys

    def register(self, key: str) -> None:
        self._seen_keys.add(key)

    def clear(self) -> None:
        self._seen_keys.clear()


class VonageSMSProvider:
    """
    Vonage (formerly Nexmo) SMS Provider integration.

    Dispatches real SMS using the official Vonage REST API.

    Unicode messages are explicitly sent using UCS-2 encoding so
    Hindi and Punjabi characters are preserved correctly.
    """

    NEXMO_SMS_URL = "https://rest.nexmo.com/sms/json"

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        from_number: Optional[str] = None,
    ):
        self.api_key = api_key or os.getenv("VONAGE_API_KEY")
        self.api_secret = api_secret or os.getenv("VONAGE_API_SECRET")
        self.from_number = (
            from_number
            or os.getenv("VONAGE_FROM")
            or "WeatherGPT"
        )

    def send_sms(
        self,
        to_phone: str,
        message: str
    ) -> Dict[str, Any]:
        """
        Send SMS via Vonage REST API.

        Automatically uses Unicode/UCS-2 when the message contains
        non-ASCII characters such as Hindi or Punjabi.

        Returns:
            {
                "success": bool,
                "message_id": str | None,
                "error": str | None
            }
        """

        if not self.api_key or not self.api_secret:
            return {
                "success": False,
                "message_id": None,
                "error": (
                    "Missing Vonage credentials "
                    "(VONAGE_API_KEY / VONAGE_API_SECRET)."
                ),
            }

        if not to_phone:
            return {
                "success": False,
                "message_id": None,
                "error": "Destination phone number is missing.",
            }

        # Detect whether the SMS contains Unicode characters.
        is_unicode = any(ord(char) > 127 for char in message)

        payload = {
            "api_key": self.api_key,
            "api_secret": self.api_secret,
            "from": self.from_number,
            "to": to_phone,
            "text": message,
        }

        # Vonage requires Unicode type for Hindi, Punjabi,
        # and other non-GSM character sets.
        if is_unicode:
            payload["type"] = "unicode"

        try:
            response = requests.post(
                self.NEXMO_SMS_URL,
                data=payload,
                timeout=10,
            )

            response.raise_for_status()
            data = response.json()

            messages = data.get("messages", [])

            if messages:
                first_msg = messages[0]
                status = str(first_msg.get("status", "-1"))

                if status == "0":
                    return {
                        "success": True,
                        "message_id": first_msg.get("message-id"),
                        "error": None,
                    }

                error_detail = first_msg.get(
                    "error-text",
                    f"Vonage API status {status}"
                )

                return {
                    "success": False,
                    "message_id": None,
                    "error": error_detail,
                }

            return {
                "success": False,
                "message_id": None,
                "error": "Empty response from Vonage API.",
            }

        except Exception as exc:
            return {
                "success": False,
                "message_id": None,
                "error": f"HTTP dispatch failed: {str(exc)}",
            }


class AlertDispatcher:
    """
    Dispatches and queues multi-channel alerts across SMS, Radio-GPT,
    and Dashboard.

    When SMS_ENABLED=true and SMS_PROVIDER=vonage, dispatches live SMS
    through the Vonage REST API.
    """

    def __init__(
        self,
        idempotency_manager: Optional[IdempotencyManager] = None
    ):
        self.idempotency = (
            idempotency_manager or IdempotencyManager()
        )
        self._dispatch_counter = 1

    def _next_dispatch_id(self) -> str:
        d_id = f"DISP-{self._dispatch_counter:04d}"
        self._dispatch_counter += 1
        return d_id

    def _localize_crop(
        self,
        crop: str,
        language: str
    ) -> str:
        """
        Translate crop names according to the selected language.
        """

        crop_key = str(crop).strip().lower()

        crop_translations = {
            "wheat": {
                "en": "Wheat",
                "hi": "गेहूं",
                "pa": "ਕਣਕ",
            },
            "cotton": {
                "en": "Cotton",
                "hi": "कपास",
                "pa": "ਕਪਾਹ",
            },
            "tomato": {
                "en": "Tomato",
                "hi": "टमाटर",
                "pa": "ਟਮਾਟਰ",
            },
            "potato": {
                "en": "Potato",
                "hi": "आलू",
                "pa": "ਆਲੂ",
            },
        }

        if crop_key in crop_translations:
            return crop_translations[crop_key].get(
                language,
                crop
            )

        return crop

    def _localize_action(
        self,
        action_title: str,
        language: str
    ) -> str:
        """
        Translate Strategist action titles into the farmer's
        selected language.
        """

        action_key = str(action_title).strip().lower()

        action_translations = {
            "postpone scheduled irrigation": {
                "en": "Postpone Scheduled Irrigation",
                "hi": "निर्धारित सिंचाई स्थगित करें",
                "pa": "ਨਿਰਧਾਰਤ ਸਿੰਚਾਈ ਮੁਲਤਵੀ ਕਰੋ",
            },
            "delay fertilizer application": {
                "en": "Delay Fertilizer Application",
                "hi": "उर्वरक का प्रयोग टालें",
                "pa": "ਖਾਦ ਦੀ ਵਰਤੋਂ ਵਿੱਚ ਦੇਰੀ ਕਰੋ",
            },
            "clear field drainage channels": {
                "en": "Clear Field Drainage Channels",
                "hi": "खेत की जल निकासी नालियां साफ करें",
                "pa": "ਖੇਤ ਦੀ ਨਿਕਾਸੀ ਵਾਲੀਆਂ ਨਾਲੀਆਂ ਸਾਫ਼ ਕਰੋ",
            },
            "halt spraying due to wind drift": {
                "en": "Halt Spraying due to Wind Drift",
                "hi": "तेज हवा के कारण छिड़काव रोकें",
                "pa": "ਤੇਜ਼ ਹਵਾ ਕਾਰਨ ਛਿੜਕਾਅ ਰੋਕੋ",
            },
        }

        if action_key in action_translations:
            return action_translations[action_key].get(
                language,
                action_title
            )

        # If an unknown action is received, preserve it rather
        # than accidentally generating a misleading translation.
        return action_title

    def _build_localized_sms(
        self,
        name: str,
        crop: str,
        action_title: str,
        language: str
    ) -> str:
        """
        Build a complete SMS in exactly one language.

        Supported languages:
        - en = English
        - hi = Hindi
        - pa = Punjabi
        """

        # Normalize language.
        language = str(language).strip().lower()

        if language not in ("en", "hi", "pa"):
            language = "en"

        localized_crop = self._localize_crop(
            crop,
            language
        )

        localized_action = self._localize_action(
            action_title,
            language
        )

        # ---------------------------------------------------------
        # ENGLISH
        # ---------------------------------------------------------
        if language == "en":
            return (
                f"WeatherGPT Alert: {name} ji, "
                f"urgent advisory for your {localized_crop} crop: "
                f"{localized_action}. "
                f"Check the dashboard for details."
            )

        # ---------------------------------------------------------
        # HINDI
        # ---------------------------------------------------------
        if language == "hi":
            return (
                f"वेदरजीपीटी चेतावनी: {name} जी, "
                f"आपकी {localized_crop} की फसल के लिए जरूरी सलाह: "
                f"{localized_action}। "
                f"अधिक जानकारी के लिए डैशबोर्ड देखें।"
            )

        # ---------------------------------------------------------
        # PUNJABI
        # ---------------------------------------------------------
        return (
            f"ਵੇਦਰਜੀਪੀਟੀ ਚੇਤਾਵਨੀ: {name} ਜੀ, "
            f"ਤੁਹਾਡੀ {localized_crop} ਦੀ ਫ਼ਸਲ ਲਈ ਜ਼ਰੂਰੀ ਸਲਾਹ: "
            f"{localized_action}। "
            f"ਹੋਰ ਜਾਣਕਾਰੀ ਲਈ ਡੈਸ਼ਬੋਰਡ ਦੇਖੋ।"
        )

    def create_sms_alert(
        self,
        threat_id: str,
        farmer: Dict[str, Any],
        action_title: str,
        urgency: str = "high"
    ) -> Optional[DispatchedAlert]:
        """
        Create a concise SMS alert formatted completely in the
        farmer's preferred language.

        Supported languages:
        - English
        - Hindi
        - Punjabi

        If SMS_ENABLED is true and SMS_PROVIDER is vonage,
        dispatches via Vonage REST API.
        """

        farmer_id = (
            farmer.get("id")
            or farmer.get("farmer_id", "UNKNOWN")
        )

        lang = str(
            farmer.get("language", "en")
        ).strip().lower()

        # Only support the three explicitly implemented languages.
        if lang not in ("en", "hi", "pa"):
            lang = "en"

        key = self.idempotency.make_key(
            threat_id,
            farmer_id,
            "sms_alert",
            action_title
        )

        if self.idempotency.is_duplicate(key):
            return None

        self.idempotency.register(key)

        name = farmer.get("name", "Farmer")
        crop = farmer.get("crop", "Crop")

        # Build the entire SMS in one language.
        msg = self._build_localized_sms(
            name=name,
            crop=crop,
            action_title=action_title,
            language=lang
        )

        sms_enabled = (
            os.getenv("SMS_ENABLED", "false")
            .strip()
            .lower()
            in ("true", "1", "yes")
        )

        sms_provider = (
            os.getenv("SMS_PROVIDER", "simulated")
            .strip()
            .lower()
        )

        phone = (
            os.getenv("VONAGE_TO")
            or farmer.get("phone")
        )

        alert = DispatchedAlert(
            dispatch_id=self._next_dispatch_id(),
            farmer_id=farmer_id,
            farmer_name=name,
            phone=phone,
            channel=DispatchChannel.SMS,
            language=lang,
            urgency=urgency,
            message=msg,
            status=TaskStatus.QUEUED,
            timestamp=datetime.now(timezone.utc).isoformat()
        )

        # Live Vonage SMS
        if sms_enabled and sms_provider == "vonage":
            provider = VonageSMSProvider()

            result = provider.send_sms(
                to_phone=phone,
                message=msg
            )

            if result["success"]:
                alert.status = TaskStatus.SUCCESS

            else:
                alert.status = TaskStatus.FAILED
                alert.message = (
                    f"{msg} "
                    f"[Vonage Error: {result['error']}]"
                )

        return alert

    def queue_radio_gpt_broadcast(
        self,
        threat_id: str,
        farmer_id: str,
        farmer_name: str,
        phone: Optional[str],
        script: str,
        language: str = "en",
        urgency: str = "high"
    ) -> Optional[DispatchedAlert]:
        """
        Queue outbound voice telephony broadcast job for Member 4
        (Radio-GPT).
        """

        key = self.idempotency.make_key(
            threat_id,
            farmer_id,
            "radio_gpt_voice"
        )

        if self.idempotency.is_duplicate(key):
            return None

        self.idempotency.register(key)

        return DispatchedAlert(
            dispatch_id=self._next_dispatch_id(),
            farmer_id=farmer_id,
            farmer_name=farmer_name,
            phone=phone,
            channel=DispatchChannel.RADIO_GPT,
            language=language,
            urgency=urgency,
            message=script,
            status=TaskStatus.QUEUED,
            timestamp=datetime.now(timezone.utc).isoformat()
        )

    def create_dashboard_event(
        self,
        threat_id: str,
        farmer_id: str,
        farmer_name: str,
        risk_level: str,
        action_title: str,
        execution_status: str,
        calendar_status: str,
        details: Optional[Dict[str, Any]] = None
    ) -> DashboardEvent:
        """
        Create a telemetry event for Member 5 (Dashboard feed).
        """

        now_str = datetime.now(timezone.utc).isoformat()

        return DashboardEvent(
            event_id=f"DASH-EVT-{self._dispatch_counter:04d}",
            threat_event_id=threat_id,
            farmer_id=farmer_id,
            farmer_name=farmer_name,
            risk_level=risk_level,
            action_title=action_title,
            execution_status=execution_status,
            calendar_status=calendar_status,
            timestamp=now_str,
            details=details or {}
        )