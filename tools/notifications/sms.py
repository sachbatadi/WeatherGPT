import os
import re
import hmac
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
import requests


def normalize_phone_e164(phone: Optional[str]) -> Optional[str]:
    """
    Normalize phone number to international E.164 format without leading '+'.
    Standardizes Indian 10-digit mobile numbers (starting with 6-9) to 91XXXXXXXXXX.
    Returns None if the phone number is invalid, empty, or non-numeric.
    """
    if not phone or not isinstance(phone, str):
        return None

    cleaned = re.sub(r"[\s\-\(\)\.]", "", phone.strip())
    if cleaned.startswith("+"):
        cleaned = cleaned[1:]

    # Must contain only digits
    if not cleaned.isdigit() or len(cleaned) < 10 or len(cleaned) > 15:
        return None

    # Standard Indian 10-digit format
    if len(cleaned) == 10:
        if cleaned[0] in ("6", "7", "8", "9"):
            return "91" + cleaned
        return None

    # Indian 11-digit format starting with 0
    if len(cleaned) == 11 and cleaned.startswith("0"):
        if cleaned[1] in ("6", "7", "8", "9"):
            return "91" + cleaned[1:]
        return None

    # Indian 12-digit format starting with 91
    if len(cleaned) == 12 and cleaned.startswith("91"):
        if cleaned[2] in ("6", "7", "8", "9"):
            return cleaned
        return None

    # International numbers (e.g. US +1, UK +44)
    if len(cleaned) >= 11:
        return cleaned

    return None


def clean_indian_phone_number(phone: Optional[str]) -> Optional[str]:
    """Alias for normalizing phone number."""
    return normalize_phone_e164(phone)


class SMSDeliveryResult:
    """Receipt object returned by SMS providers."""

    def __init__(
        self,
        success: bool,
        status: str,
        provider: str,
        phone: str,
        message_id: Optional[str] = None,
        error_message: Optional[str] = None,
    ):
        self.success = success
        self.status = status
        self.provider = provider
        self.phone = phone
        self.message_id = message_id
        self.error_message = error_message


class BaseSMSProvider:
    name: str = "base"

    def send_sms(self, to_phone: str, message: str) -> SMSDeliveryResult:
        raise NotImplementedError


class MockSMSProvider(BaseSMSProvider):
    name: str = "mock"

    def __init__(self, simulate_failure: bool = False):
        self.simulate_failure = simulate_failure
        self.sent_messages: List[Dict[str, Any]] = []
        self._counter = 1

    def send_sms(self, to_phone: str, message: str) -> SMSDeliveryResult:
        norm = normalize_phone_e164(to_phone)
        if not norm:
            return SMSDeliveryResult(
                success=False,
                status="failed",
                provider=self.name,
                phone=str(to_phone),
                error_message="Invalid phone number format",
            )

        if self.simulate_failure:
            return SMSDeliveryResult(
                success=False,
                status="failed",
                provider=self.name,
                phone=norm,
                error_message="Simulated provider dispatch failure",
            )

        msg_id = f"MOCK-SMS-{self._counter:05d}"
        self._counter += 1
        self.sent_messages.append({"to": norm, "message": message, "message_id": msg_id})

        return SMSDeliveryResult(
            success=True,
            status="sent",
            provider=self.name,
            phone=norm,
            message_id=msg_id,
        )


class VonageSMSProvider(BaseSMSProvider):
    name: str = "vonage"

    def __init__(
        self,
        api_key: str = "",
        api_secret: str = "",
        sender_id: str = "WeatherGPT",
        timeout: float = 5.0,
    ):
        self.api_key = api_key or os.environ.get("VONAGE_API_KEY", "")
        self.api_secret = api_secret or os.environ.get("VONAGE_API_SECRET", "")
        self.sender_id = sender_id or os.environ.get("VONAGE_FROM", "WeatherGPT")
        self.timeout = timeout

    def send_sms(self, to_phone: str, message: str) -> SMSDeliveryResult:
        if not self.api_key or not self.api_secret:
            return SMSDeliveryResult(
                success=False,
                status="failed",
                provider=self.name,
                phone=str(to_phone),
                error_message="Vonage credentials not configured",
            )

        norm = normalize_phone_e164(to_phone)
        if not norm:
            return SMSDeliveryResult(
                success=False,
                status="failed",
                provider=self.name,
                phone=str(to_phone),
                error_message="Invalid phone number format",
            )

        endpoint = "https://rest.nexmo.com/sms/json"
        payload = {
            "api_key": self.api_key,
            "api_secret": self.api_secret,
            "to": norm,
            "from": self.sender_id,
            "text": message,
        }

        try:
            resp = requests.post(endpoint, json=payload, timeout=self.timeout)
            data = resp.json()
            messages = data.get("messages", [])
            if messages:
                first = messages[0]
                status = str(first.get("status", "1"))
                if status == "0":
                    return SMSDeliveryResult(
                        success=True,
                        status="sent",
                        provider=self.name,
                        phone=norm,
                        message_id=first.get("message-id"),
                    )
                else:
                    err = first.get("error-text", "Vonage dispatch error")
                    return SMSDeliveryResult(
                        success=False,
                        status="failed",
                        provider=self.name,
                        phone=norm,
                        error_message=err,
                    )
            return SMSDeliveryResult(
                success=False,
                status="failed",
                provider=self.name,
                phone=norm,
                error_message="No response message received from Vonage",
            )
        except requests.exceptions.Timeout:
            return SMSDeliveryResult(
                success=False,
                status="failed",
                provider=self.name,
                phone=norm,
                error_message=f"Request to Vonage timed out after {self.timeout}s",
            )
        except Exception as exc:
            return SMSDeliveryResult(
                success=False,
                status="failed",
                provider=self.name,
                phone=norm,
                error_message=str(exc),
            )


def get_sms_provider() -> BaseSMSProvider:
    provider_type = os.environ.get("SMS_PROVIDER", "mock").strip().lower()
    if provider_type == "vonage":
        key = os.environ.get("VONAGE_API_KEY", "")
        secret = os.environ.get("VONAGE_API_SECRET", "")
        sender = os.environ.get("VONAGE_FROM", "WeatherGPT")
        return VonageSMSProvider(api_key=key, api_secret=secret, sender_id=sender)
    return MockSMSProvider()


def verify_vonage_signature(
    params: Dict[str, Any],
    signature_secret: Optional[str] = None,
    method: str = "sha256",
    allow_unsigned_when_no_secret: bool = False,
) -> bool:
    """
    Verify incoming Vonage Delivery Receipt webhook signature according to Vonage specifications:
    - Exclude 'sig' param
    - Sort keys alphabetically
    - Replace '&' and '=' with '_' in values
    - Prepend '&' to the query string
    - Compute HMAC digest with signature_secret
    """
    if not signature_secret:
        return allow_unsigned_when_no_secret

    sig = params.get("sig")
    if not sig:
        return False

    sorted_pairs = sorted([(k, v) for k, v in params.items() if k != "sig"])
    sanitized = [f"{k}={str(v).replace('&', '_').replace('=', '_')}" for k, v in sorted_pairs]
    sig_base = "&" + "&".join(sanitized)

    method_clean = method.lower()
    if "512" in method_clean:
        algo = hashlib.sha512
    elif "md5" in method_clean:
        algo = hashlib.md5
    else:
        algo = hashlib.sha256

    computed = hmac.new(signature_secret.encode("utf-8"), sig_base.encode("utf-8"), algo).hexdigest()
    return hmac.compare_digest(computed.lower(), str(sig).lower())


def parse_vonage_delivery_receipt(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Parse Vonage delivery receipt payload into normalized fields."""
    msg_id = payload.get("messageId") or payload.get("message-id")
    raw_status = str(payload.get("status", "unknown")).lower()
    valid_statuses = {"delivered", "failed", "rejected", "expired", "buffered", "accepted"}
    status = raw_status if raw_status in valid_statuses else "unknown"

    err_code = str(payload.get("err-code", "0"))
    error_map = {
        "0": None,
        "1": "Unknown subscriber",
        "2": "Absent subscriber",
        "3": "Call barred",
        "4": "Bad Credentials",
        "5": "Other error",
    }
    error_message = error_map.get(err_code, f"Error code {err_code}")

    return {
        "message_id": msg_id,
        "status": status,
        "error_code": err_code,
        "error_message": error_message,
        "timestamp": payload.get("message-timestamp") or datetime.now(timezone.utc).isoformat(),
    }
