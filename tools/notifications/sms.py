"""
SMS Notification Provider Layer (tools/notifications/sms.py).

Provides:
- Abstract SMSProvider interface
- Safe MockSMSProvider for tests/local development (no real SMS sent)
- VonageSMSProvider for international SMS delivery via Vonage SMS API (https://rest.nexmo.com/sms/json)
- SMS delivery result schema with status, provider message IDs, timestamps, safe errors
- Phone number normalization (E.164-compatible with Indian mobile defaults)
"""

from __future__ import annotations

import os
import re
import requests
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Dict, Any


@dataclass
class SMSDeliveryResult:
    """Standardized delivery result emitted by any SMSProvider."""
    success: bool
    status: str                     # "sent", "queued", "disabled", "failed", "skipped"
    provider: str                   # "mock", "vonage", etc.
    phone: str
    message: str
    message_id: Optional[str] = None
    error_message: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    raw_response: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "status": self.status,
            "provider": self.provider,
            "phone": self.phone,
            "message": self.message,
            "message_id": self.message_id,
            "error_message": self.error_message,
            "timestamp": self.timestamp,
            "raw_response": self.raw_response,
        }


def normalize_phone_e164(raw_phone: Optional[str], default_country_code: str = "91") -> Optional[str]:
    """
    Validate and normalize phone numbers into international E.164-compatible format (digits only).
    Accepts:
      - 10-digit Indian numbers: "9876543210" -> "919876543210"
      - With leading 0: "09876543210" -> "919876543210"
      - With +91 / 91: "+91-9876543210", "+91 98765 43210" -> "919876543210"
      - International numbers: "+1-415-555-2671" -> "14155552671"

    Returns:
      Digits-only E.164 string (without leading +) if valid, else None.
    """
    if not raw_phone:
        return None

    raw_str = str(raw_phone).strip()
    if re.search(r"[a-zA-Z]", raw_str):
        return None

    digits = re.sub(r"\D", "", raw_str)

    # 10-digit standard Indian mobile starting with 6, 7, 8, 9
    if len(digits) == 10 and digits[0] in "6789":
        return f"{default_country_code}{digits}"
    # 11-digit with leading zero
    elif len(digits) == 11 and digits.startswith("0") and digits[1] in "6789":
        return f"{default_country_code}{digits[1:]}"
    # 11-15 digit international numbers (E.164 range)
    elif 11 <= len(digits) <= 15:
        return digits

    return None


def clean_indian_phone_number(raw_phone: Optional[str]) -> Optional[str]:
    """
    Backwards-compatible helper returning normalized 10-digit Indian numbers or E.164 string.
    """
    e164 = normalize_phone_e164(raw_phone)
    if not e164:
        return None
    if e164.startswith("91") and len(e164) == 12:
        return e164[2:]
    return e164


class SMSProvider(ABC):
    """Abstract SMS delivery provider interface."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider identifier name."""
        pass

    @abstractmethod
    def send_sms(self, phone: str, message: str, sender_id: Optional[str] = None) -> SMSDeliveryResult:
        """Attempt to deliver an SMS message to the given phone number."""
        pass


class MockSMSProvider(SMSProvider):
    """
    Safe in-memory mock provider.
    Never connects to external gateways. Used for offline testing and default local dev.
    """

    def __init__(self, simulate_failure: bool = False, failure_reason: Optional[str] = None):
        self.simulate_failure = simulate_failure
        self.failure_reason = failure_reason or "Simulated provider dispatch failure"
        self.sent_messages: list[SMSDeliveryResult] = []

    @property
    def name(self) -> str:
        return "mock"

    def send_sms(self, phone: str, message: str, sender_id: Optional[str] = None) -> SMSDeliveryResult:
        normalized_phone = normalize_phone_e164(phone)
        now_str = datetime.now(timezone.utc).isoformat()

        if not normalized_phone:
            res = SMSDeliveryResult(
                success=False,
                status="failed",
                provider=self.name,
                phone=phone or "",
                message=message,
                message_id=None,
                error_message=f"Invalid phone number format: '{phone}'",
                timestamp=now_str,
            )
            self.sent_messages.append(res)
            return res

        if self.simulate_failure:
            res = SMSDeliveryResult(
                success=False,
                status="failed",
                provider=self.name,
                phone=normalized_phone,
                message=message,
                message_id=None,
                error_message=self.failure_reason,
                timestamp=now_str,
            )
            self.sent_messages.append(res)
            return res

        msg_id = f"MOCK-SMS-{len(self.sent_messages) + 1:04d}"
        res = SMSDeliveryResult(
            success=True,
            status="sent",
            provider=self.name,
            phone=normalized_phone,
            message=message,
            message_id=msg_id,
            error_message=None,
            timestamp=now_str,
            raw_response={"mock_status": "delivered", "message_id": msg_id},
        )
        self.sent_messages.append(res)
        return res


class VonageSMSProvider(SMSProvider):
    """
    Vonage (formerly Nexmo) SMS Provider using the documented HTTP REST API.
    API documentation: https://developer.vonage.com/en/api/sms

    Requires:
      VONAGE_API_KEY environment variable.
      VONAGE_API_SECRET environment variable.
      Optional SMS_SENDER_ID (defaults to 'WeatherGPT' or registered sender).
    """

    DEFAULT_ENDPOINT = "https://rest.nexmo.com/sms/json"

    # Known Vonage response status code descriptions
    STATUS_DESCRIPTIONS: Dict[str, str] = {
        "0": "Delivered",
        "1": "Throttled: message rejected by rate limiter",
        "2": "Missing required parameter",
        "3": "Invalid parameter value",
        "4": "Invalid credentials (bad api_key or api_secret)",
        "5": "Internal error in Vonage gateway",
        "6": "Unroutable message to destination network",
        "7": "Invalid message recipient",
        "8": "Number barred by carrier or recipient list",
        "9": "Partner account out of quota / balance exhausted",
        "11": "Account not enabled for REST SMS",
        "12": "Message length exceeds carrier threshold",
        "15": "Invalid sender ID (DLT / carrier registration required)",
        "29": "Non-routable network prefix",
    }

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        sender_id: Optional[str] = None,
        timeout: int = 10,
        endpoint: Optional[str] = None,
    ):
        self.api_key = (api_key if api_key is not None else os.getenv("VONAGE_API_KEY", "")).strip()
        self.api_secret = (api_secret if api_secret is not None else os.getenv("VONAGE_API_SECRET", "")).strip()
        self.sender_id = (sender_id if sender_id is not None else os.getenv("SMS_SENDER_ID", "WeatherGPT")).strip() or "WeatherGPT"
        self.timeout = timeout
        self.endpoint = endpoint or os.getenv("VONAGE_ENDPOINT", self.DEFAULT_ENDPOINT)

    @property
    def name(self) -> str:
        return "vonage"

    def send_sms(self, phone: str, message: str, sender_id: Optional[str] = None) -> SMSDeliveryResult:
        now_str = datetime.now(timezone.utc).isoformat()

        # 1. Check Configuration
        if not self.api_key or not self.api_secret:
            return SMSDeliveryResult(
                success=False,
                status="failed",
                provider=self.name,
                phone=phone or "",
                message=message,
                message_id=None,
                error_message="Vonage credentials not configured (VONAGE_API_KEY or VONAGE_API_SECRET is missing).",
                timestamp=now_str,
            )

        # 2. Validate Phone Number (E.164 without leading +)
        normalized_phone = normalize_phone_e164(phone)
        if not normalized_phone:
            return SMSDeliveryResult(
                success=False,
                status="failed",
                provider=self.name,
                phone=phone or "",
                message=message,
                message_id=None,
                error_message=f"Invalid phone number format: '{phone}'.",
                timestamp=now_str,
            )

        # 3. Build Payload
        effective_sender = (sender_id or self.sender_id)
        payload: Dict[str, Any] = {
            "api_key": self.api_key,
            "api_secret": self.api_secret,
            "to": normalized_phone,
            "from": effective_sender,
            "text": message,
        }

        headers = {
            "Content-Type": "application/json",
            "User-Agent": "WeatherGPT-SMS-Service/1.0",
        }

        # 4. HTTP Request with strict timeout and safe error handling
        try:
            response = requests.post(
                self.endpoint,
                json=payload,
                headers=headers,
                timeout=self.timeout,
            )
            response_data = response.json() if "application/json" in response.headers.get("content-type", "") else {}
        except requests.exceptions.Timeout:
            return SMSDeliveryResult(
                success=False,
                status="failed",
                provider=self.name,
                phone=normalized_phone,
                message=message,
                message_id=None,
                error_message=f"Vonage request timed out after {self.timeout}s.",
                timestamp=now_str,
            )
        except requests.exceptions.RequestException as exc:
            return SMSDeliveryResult(
                success=False,
                status="failed",
                provider=self.name,
                phone=normalized_phone,
                message=message,
                message_id=None,
                error_message=f"Vonage network connection failed: {exc.__class__.__name__}",
                timestamp=now_str,
            )
        except Exception as exc:
            return SMSDeliveryResult(
                success=False,
                status="failed",
                provider=self.name,
                phone=normalized_phone,
                message=message,
                message_id=None,
                error_message=f"Unexpected Vonage error: {exc}",
                timestamp=now_str,
            )

        # 5. Evaluate Vonage Response
        # Vonage SMS returns: {"message-count": "1", "messages": [{"to": "...", "message-id": "...", "status": "0", "remaining-balance": "...", "message-price": "..."}]}
        messages = response_data.get("messages", [])
        if not messages or not isinstance(messages, list):
            return SMSDeliveryResult(
                success=False,
                status="failed",
                provider=self.name,
                phone=normalized_phone,
                message=message,
                message_id=None,
                error_message=f"Malformed Vonage response (HTTP {response.status_code})",
                timestamp=now_str,
                raw_response=response_data,
            )

        first_msg = messages[0]
        status_code = str(first_msg.get("status", "-1"))
        message_id = first_msg.get("message-id")
        api_error_text = first_msg.get("error-text")

        if response.status_code == 200 and status_code == "0":
            return SMSDeliveryResult(
                success=True,
                status="sent",
                provider=self.name,
                phone=normalized_phone,
                message=message,
                message_id=message_id,
                error_message=None,
                timestamp=now_str,
                raw_response=response_data,
            )
        else:
            status_desc = self.STATUS_DESCRIPTIONS.get(status_code, f"Status code {status_code}")
            detail = api_error_text or status_desc
            return SMSDeliveryResult(
                success=False,
                status="failed",
                provider=self.name,
                phone=normalized_phone,
                message=message,
                message_id=message_id,
                error_message=f"Vonage delivery error: {detail}",
                timestamp=now_str,
                raw_response=response_data,
            )


# ---------------------------------------------------------------------------
# Vonage Delivery Receipt (DLR) Webhook Verification & Processing
# ---------------------------------------------------------------------------

VONAGE_DLR_STATUS_MAP: Dict[str, str] = {
    "delivered": "delivered",
    "failed": "failed",
    "rejected": "rejected",
    "expired": "expired",
    "buffered": "pending",
    "accepted": "pending",
    "unknown": "unknown",
}


def verify_vonage_signature(
    params: Dict[str, Any],
    signature_secret: Optional[str] = None,
    method: str = "sha256",
    allow_unsigned_when_no_secret: bool = False,
) -> bool:
    """
    Verify the cryptographic signature of an inbound Vonage webhook callback
    using Vonage's official signing algorithm specification:
    1. Check presence of signature secret (reject callback if missing in production).
    2. Check presence of 'sig' parameter (reject unsigned callbacks).
    3. Remove 'sig' from parameter mapping.
    4. Sort parameters alphabetically by key.
    5. For each parameter value, replace all instances of '&' and '=' with '_'.
    6. Construct the string by prepending a leading '&' and concatenating '&key=value'.
    7. Hash using HMAC (or MD5/SHA hash) with the configured secret and compare in constant time.
    """
    import hmac
    import hashlib

    secret = (signature_secret if signature_secret is not None else os.getenv("VONAGE_SIGNATURE_SECRET", "")).strip()
    if not secret:
        # In production, signature secret is required. Unsigned callbacks are rejected.
        # Only allow bypassing if explicitly flagged for local dev/testing without secrets.
        return allow_unsigned_when_no_secret

    provided_sig = str(params.get("sig", "")).strip().lower()
    if not provided_sig:
        return False

    # 1. Remove 'sig' and sort parameters alphabetically by key name
    sorted_items = sorted(
        [(str(k), str(v)) for k, v in params.items() if str(k).lower() != "sig"],
        key=lambda pair: pair[0]
    )

    # 2. Sanitize values: replace '&' and '=' with '_'
    # 3. Construct signing base string starting with a leading '&': '&key1=val1&key2=val2'
    sanitized_parts = []
    for k, v in sorted_items:
        v_sanitized = str(v).replace("&", "_").replace("=", "_")
        sanitized_parts.append(f"{k}={v_sanitized}")

    sig_base = "&" + "&".join(sanitized_parts)

    # 4. Determine digest algorithm
    norm_method = method.strip().lower()
    if norm_method in ("sha512", "sha-512", "sha512hmac", "hmac-sha512"):
        digestmod = hashlib.sha512
    elif norm_method in ("sha1", "sha-1", "sha1hmac", "hmac-sha1"):
        digestmod = hashlib.sha1
    elif norm_method in ("md5", "md5hash"):
        # MD5 hash mode: md5(sig_base + secret)
        computed_sig = hashlib.md5((sig_base + secret).encode("utf-8")).hexdigest().lower()
        return hmac.compare_digest(provided_sig, computed_sig)
    elif norm_method in ("md5hmac", "hmac-md5"):
        digestmod = hashlib.md5
    else:
        # Default: sha256 / sha256hmac / hmac-sha256
        digestmod = hashlib.sha256

    computed_sig = hmac.new(
        secret.encode("utf-8"),
        sig_base.encode("utf-8"),
        digestmod
    ).hexdigest().lower()

    return hmac.compare_digest(provided_sig, computed_sig)



def parse_vonage_delivery_receipt(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse a Vonage SMS Delivery Receipt into standard fields.
    Extracts messageId, normalized status, error code / description, and timestamp.
    """
    message_id = (
        payload.get("messageId")
        or payload.get("message-id")
        or payload.get("message_id")
    )
    raw_status = str(payload.get("status", "unknown")).strip().lower()
    mapped_status = VONAGE_DLR_STATUS_MAP.get(raw_status, "unknown")

    err_code = str(payload.get("err-code", payload.get("err_code", "0"))).strip()
    error_desc = None
    if err_code != "0" or mapped_status in ("failed", "rejected", "expired"):
        # Map common Vonage DLR error codes
        dlr_errors = {
            "1": "Unknown subscriber",
            "2": "Absent subscriber / unreachable",
            "3": "Call barred by user or network",
            "4": "Other error in network",
            "5": "Handset memory capacity exceeded",
            "6": "Mobile equipment error",
            "7": "Network timeout",
            "9": "Illegal number",
            "99": "General network delivery failure",
        }
        err_detail = dlr_errors.get(err_code, f"Error code {err_code}")
        error_desc = f"Vonage DLR: {raw_status} ({err_detail})"

    ts = (
        payload.get("message-timestamp")
        or payload.get("message_timestamp")
        or datetime.now(timezone.utc).isoformat()
    )

    return {
        "message_id": str(message_id).strip() if message_id else None,
        "raw_status": raw_status,
        "status": mapped_status,
        "error_code": err_code,
        "error_message": error_desc,
        "timestamp": ts,
        "to": payload.get("to") or payload.get("msisdn"),
        "network_code": payload.get("network-code") or payload.get("network_code"),
    }


def get_sms_provider(
    provider_name: Optional[str] = None,
    api_key: Optional[str] = None,
    api_secret: Optional[str] = None,
    sender_id: Optional[str] = None,
) -> SMSProvider:
    """
    Factory function returning the configured SMSProvider.
    Safe default is always MockSMSProvider.
    """
    name = (provider_name or os.getenv("SMS_PROVIDER", "mock")).strip().lower()

    if name == "vonage":
        return VonageSMSProvider(
            api_key=api_key,
            api_secret=api_secret,
            sender_id=sender_id,
        )
    return MockSMSProvider()
