"""
Executor Dispatcher Subsystem (agents/executor/dispatcher.py).

Handles:
1. Alert dispatch queueing (SMS, Radio-GPT telephony queue, Dashboard events)
2. Localization of messages (English, Hindi, Punjabi)
3. Idempotency tracking to prevent duplicate alerts or operations on retries
"""

import os
from datetime import datetime, timezone
from typing import Dict, Any, List, Set, Optional
from .schemas import (
    DispatchChannel,
    TaskStatus,
    DispatchedAlert,
    DashboardEvent
)
from tools.notifications.sms import SMSProvider, get_sms_provider, SMSDeliveryResult


class IdempotencyManager:
    """
    In-memory registry preventing duplicate execution of identical actions or alerts
    for a given threat event and farmer.
    """

    def __init__(self):
        self._seen_keys: Set[str] = set()

    def make_key(self, threat_id: str, farmer_id: str, action_type: str, item_id: Optional[str] = None) -> str:
        return f"{threat_id}:{farmer_id}:{action_type}:{item_id or 'none'}"

    def is_duplicate(self, key: str) -> bool:
        return key in self._seen_keys

    def register(self, key: str) -> None:
        self._seen_keys.add(key)

    def clear(self) -> None:
        self._seen_keys.clear()


class AlertDispatcher:
    """
    Dispatches and queues multi-channel alerts across SMS, Radio-GPT, and Dashboard.
    SMS delivery attempts occur only when SMS is explicitly enabled; otherwise, alerts
    are queued/skipped using the safe default provider.
    """

    def __init__(
        self,
        idempotency_manager: Optional[IdempotencyManager] = None,
        sms_provider: Optional[SMSProvider] = None,
    ):
        self.idempotency = idempotency_manager or IdempotencyManager()
        self.sms_provider = sms_provider or get_sms_provider()
        self._dispatch_counter = 1

    def _next_dispatch_id(self) -> str:
        d_id = f"DISP-{self._dispatch_counter:04d}"
        self._dispatch_counter += 1
        return d_id

    def create_sms_alert(
        self,
        threat_id: str,
        farmer: Dict[str, Any],
        action_title: str,
        urgency: str = "high"
    ) -> Optional[DispatchedAlert]:
        """
        Create and dispatch a concise, localized SMS alert.
        Validates phone numbers, respects SMS_ENABLED configuration, records provider
        message IDs/errors, and prevents duplicate sends.
        """
        farmer_id = farmer.get("id") or farmer.get("farmer_id", "UNKNOWN")
        lang = str(farmer.get("language", "en")).lower()
        key = self.idempotency.make_key(threat_id, farmer_id, "sms_alert", action_title)

        if self.idempotency.is_duplicate(key):
            return None
        self.idempotency.register(key)

        name = farmer.get("name", "Farmer")
        crop = farmer.get("crop", "Crop")
        phone = farmer.get("phone")

        # Localized SMS template
        if lang == "pa":
            msg = f"ਵੈਦਰ-ਜੀਪੀਟੀ ਅਲਰਟ: {name} ਜੀ, ਤੁਹਾਡੀ {crop} ਫ਼ਸਲ ਲਈ ਜ਼ਰੂਰੀ ਸੂਚਨਾ: {action_title}। ਵੇਰਵਿਆਂ ਲਈ ਡੈਸ਼ਬੋਰਡ ਦੇਖੋ।"
        elif lang == "hi":
            msg = f"वेदरजीपीटी अलर्ट: {name} जी, आपकी {crop} फसल के लिए आवश्यक सूचना: {action_title}। विवरण हेतु डैशबोर्ड देखें।"
        else:
            msg = f"WeatherGPT Alert: {name} ji, urgent advisory for your {crop}: {action_title}. Check dashboard for details."

        dispatch_id = self._next_dispatch_id()
        sms_enabled_env = os.getenv("SMS_ENABLED", "false").strip().lower() in ("true", "1", "yes")

        provider_name = getattr(self.sms_provider, "name", "mock")
        provider_message_id = None
        error_message = None

        if not sms_enabled_env:
            # Safe default: SMS is globally disabled for dev/test
            status = TaskStatus.QUEUED
            error_message = "SMS delivery disabled via SMS_ENABLED=false."
        else:
            # SMS is enabled: attempt outbound dispatch through provider
            if not phone:
                status = TaskStatus.FAILED
                error_message = "Farmer profile does not have a phone number."
            else:
                delivery_result: SMSDeliveryResult = self.sms_provider.send_sms(
                    phone=phone,
                    message=msg,
                    sender_id=None
                )
                provider_name = delivery_result.provider
                provider_message_id = delivery_result.message_id
                error_message = delivery_result.error_message

                if delivery_result.success:
                    status = TaskStatus.SUCCESS
                else:
                    status = TaskStatus.FAILED

        return DispatchedAlert(
            dispatch_id=dispatch_id,
            farmer_id=farmer_id,
            farmer_name=name,
            phone=phone,
            channel=DispatchChannel.SMS,
            language=lang,
            urgency=urgency,
            message=msg,
            status=status,
            provider=provider_name,
            provider_message_id=provider_message_id,
            error_message=error_message,
            timestamp=datetime.now(timezone.utc).isoformat()
        )

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
        Queue outbound voice telephony broadcast job for Member 4 (Radio-GPT).
        """
        key = self.idempotency.make_key(threat_id, farmer_id, "radio_gpt_voice")
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
