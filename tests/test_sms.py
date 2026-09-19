"""
Unit and integration tests for Outbound Farmer SMS Integration with Vonage (tests/test_sms.py).

Covers:
1. Phone number cleaning and E.164 normalization (Indian numbers, +91, international, invalid strings).
2. MockSMSProvider (success, simulated failure, sent tracking).
3. VonageSMSProvider (missing API key/secret, invalid phone, network timeout, successful response, API error).
4. SMS_ENABLED flag safety (disabled by default, no outbound SMS sent).
5. AlertDispatcher SMS workflow with provider receipts.
6. Idempotency (preventing duplicate SMS sends).
7. Audit log persistence in SQLite (storing phone, provider, provider_message_id, error_message).
"""

import os
import unittest
from unittest.mock import patch, MagicMock

from tools.notifications.sms import (
    normalize_phone_e164,
    clean_indian_phone_number,
    MockSMSProvider,
    VonageSMSProvider,
    get_sms_provider,
    SMSDeliveryResult,
)
from agents.executor.dispatcher import AlertDispatcher, IdempotencyManager
from agents.executor.schemas import TaskStatus
from database.connection import init_db, log_alert, get_alert_logs


class TestPhoneValidation(unittest.TestCase):
    """Tests for international E.164 normalization and validation."""

    def test_normalize_valid_10_digit(self):
        self.assertEqual(normalize_phone_e164("9876543210"), "919876543210")
        self.assertEqual(normalize_phone_e164("8123456789"), "918123456789")
        self.assertEqual(normalize_phone_e164("7012345678"), "917012345678")
        self.assertEqual(normalize_phone_e164("6901234567"), "916901234567")

    def test_normalize_with_country_code_and_formatting(self):
        self.assertEqual(normalize_phone_e164("+91-9876543210"), "919876543210")
        self.assertEqual(normalize_phone_e164("+91 98765 43210"), "919876543210")
        self.assertEqual(normalize_phone_e164("09876543210"), "919876543210")
        self.assertEqual(normalize_phone_e164("919876543210"), "919876543210")

    def test_normalize_international_e164(self):
        self.assertEqual(normalize_phone_e164("+1-415-555-2671"), "14155552671")
        self.assertEqual(normalize_phone_e164("+44-7700-900077"), "447700900077")

    def test_clean_invalid_numbers(self):
        self.assertIsNone(normalize_phone_e164(None))
        self.assertIsNone(normalize_phone_e164(""))
        self.assertIsNone(normalize_phone_e164("12345"))  # too short
        self.assertIsNone(normalize_phone_e164("5876543210"))  # starts with 5 (invalid Indian mobile)
        self.assertIsNone(normalize_phone_e164("abcd9876543210"))  # non-digits


class TestMockSMSProvider(unittest.TestCase):
    """Tests for MockSMSProvider."""

    def setUp(self):
        self.provider = MockSMSProvider()

    def test_mock_send_success(self):
        res = self.provider.send_sms("+91-9876543210", "Test Advisory Message")
        self.assertTrue(res.success)
        self.assertEqual(res.status, "sent")
        self.assertEqual(res.provider, "mock")
        self.assertEqual(res.phone, "919876543210")
        self.assertTrue(res.message_id.startswith("MOCK-SMS-"))
        self.assertIsNone(res.error_message)
        self.assertEqual(len(self.provider.sent_messages), 1)

    def test_mock_simulated_failure(self):
        failing_provider = MockSMSProvider(simulate_failure=True)
        res = failing_provider.send_sms("9876543210", "Failing Test")
        self.assertFalse(res.success)
        self.assertEqual(res.status, "failed")
        self.assertIn("Simulated provider dispatch failure", res.error_message)

    def test_mock_invalid_phone(self):
        res = self.provider.send_sms("invalid-phone", "Hello")
        self.assertFalse(res.success)
        self.assertEqual(res.status, "failed")
        self.assertIn("Invalid phone number format", res.error_message)


class TestVonageSMSProvider(unittest.TestCase):
    """Tests for VonageSMSProvider with mocked network interactions."""

    def test_missing_credentials_fails_safely(self):
        provider = VonageSMSProvider(api_key="", api_secret="")
        res = provider.send_sms("+91-9876543210", "Advisory")
        self.assertFalse(res.success)
        self.assertEqual(res.status, "failed")
        self.assertIn("Vonage credentials not configured", res.error_message)

    def test_missing_secret_only_fails_safely(self):
        provider = VonageSMSProvider(api_key="valid_key", api_secret="")
        res = provider.send_sms("+91-9876543210", "Advisory")
        self.assertFalse(res.success)
        self.assertEqual(res.status, "failed")
        self.assertIn("Vonage credentials not configured", res.error_message)

    def test_invalid_phone_fails(self):
        provider = VonageSMSProvider(api_key="mock_key", api_secret="mock_secret")
        res = provider.send_sms("123", "Advisory")
        self.assertFalse(res.success)
        self.assertIn("Invalid phone number format", res.error_message)

    @patch("requests.post")
    def test_successful_vonage_dispatch(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "application/json"}
        mock_response.json.return_value = {
            "message-count": "1",
            "messages": [
                {
                    "to": "919876543210",
                    "message-id": "VONAGE-MSG-98765",
                    "status": "0",
                    "remaining-balance": "10.5000",
                    "message-price": "0.0333"
                }
            ]
        }
        mock_post.return_value = mock_response

        provider = VonageSMSProvider(api_key="my_key", api_secret="my_secret", sender_id="WeatherGPT")
        res = provider.send_sms("+91-9876543210", "Frost warning tonight")

        self.assertTrue(res.success)
        self.assertEqual(res.status, "sent")
        self.assertEqual(res.provider, "vonage")
        self.assertEqual(res.message_id, "VONAGE-MSG-98765")
        self.assertIsNone(res.error_message)

        # Verify POST payload
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertEqual(kwargs["json"]["api_key"], "my_key")
        self.assertEqual(kwargs["json"]["api_secret"], "my_secret")
        self.assertEqual(kwargs["json"]["to"], "919876543210")
        self.assertEqual(kwargs["json"]["from"], "WeatherGPT")
        self.assertEqual(kwargs["json"]["text"], "Frost warning tonight")

    @patch("requests.post")
    def test_vonage_api_error_response(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "application/json"}
        mock_response.json.return_value = {
            "message-count": "1",
            "messages": [
                {
                    "status": "4",
                    "error-text": "Bad Credentials"
                }
            ]
        }
        mock_post.return_value = mock_response

        provider = VonageSMSProvider(api_key="bad_key", api_secret="bad_secret")
        res = provider.send_sms("9876543210", "Alert")

        self.assertFalse(res.success)
        self.assertEqual(res.status, "failed")
        self.assertIn("Bad Credentials", res.error_message)

    @patch("requests.post")
    def test_vonage_network_timeout(self, mock_post):
        import requests
        mock_post.side_effect = requests.exceptions.Timeout("Connection timed out")

        provider = VonageSMSProvider(api_key="valid_key", api_secret="valid_secret", timeout=3.0)
        res = provider.send_sms("9876543210", "Advisory")

        self.assertFalse(res.success)
        self.assertEqual(res.status, "failed")
        self.assertIn("timed out after 3.0s", res.error_message)


class TestAlertDispatcherSMSWorkflow(unittest.TestCase):
    """Tests for AlertDispatcher integrating with SMSProvider, idempotency, and settings."""

    def setUp(self):
        self.mock_provider = MockSMSProvider()
        self.idempotency = IdempotencyManager()
        self.dispatcher = AlertDispatcher(
            idempotency_manager=self.idempotency,
            sms_provider=self.mock_provider,
        )
        self.sample_farmer = {
            "farmer_id": "F001",
            "name": "Harpreet Singh",
            "phone": "+91-9876543210",
            "crop": "Wheat",
            "language": "pa",
        }

    def test_sms_disabled_by_default(self):
        """When SMS_ENABLED is false (or not set), alerts are queued safely with no real dispatch."""
        with patch.dict(os.environ, {"SMS_ENABLED": "false"}):
            alert = self.dispatcher.create_sms_alert(
                threat_id="EVT-001",
                farmer=self.sample_farmer,
                action_title="Halt Irrigation",
            )
            self.assertIsNotNone(alert)
            self.assertEqual(alert.status, TaskStatus.QUEUED)
            self.assertEqual(alert.provider, "mock")
            self.assertIn("SMS delivery disabled", alert.error_message)
            self.assertEqual(len(self.mock_provider.sent_messages), 0)

    def test_sms_enabled_mock_dispatch_success(self):
        """When SMS_ENABLED is true, outbound delivery occurs through the configured provider."""
        with patch.dict(os.environ, {"SMS_ENABLED": "true"}):
            alert = self.dispatcher.create_sms_alert(
                threat_id="EVT-002",
                farmer=self.sample_farmer,
                action_title="Postpone spraying",
            )
            self.assertIsNotNone(alert)
            self.assertEqual(alert.status, TaskStatus.SUCCESS)
            self.assertEqual(alert.provider, "mock")
            self.assertTrue(alert.provider_message_id.startswith("MOCK-SMS-"))
            self.assertIsNone(alert.error_message)
            self.assertEqual(len(self.mock_provider.sent_messages), 1)

    def test_duplicate_send_prevention(self):
        """Identical alert dispatches are caught by idempotency manager."""
        with patch.dict(os.environ, {"SMS_ENABLED": "true"}):
            alert1 = self.dispatcher.create_sms_alert(
                threat_id="EVT-DUPE",
                farmer=self.sample_farmer,
                action_title="Drain field",
            )
            self.assertIsNotNone(alert1)

            # Second identical call should return None (duplicate prevented)
            alert2 = self.dispatcher.create_sms_alert(
                threat_id="EVT-DUPE",
                farmer=self.sample_farmer,
                action_title="Drain field",
            )
            self.assertIsNone(alert2)
            self.assertEqual(len(self.mock_provider.sent_messages), 1)


class TestSQLiteAlertAuditLog(unittest.TestCase):
    """Tests verifying SQLite alert_logs audit persistence with SMS provider receipts."""

    def setUp(self):
        import tempfile
        import shutil
        self.temp_dir = tempfile.mkdtemp()
        self.db_file = os.path.join(self.temp_dir, "test_alert_audit.db")
        self.db_url = f"sqlite:///{self.db_file}"
        init_db(self.db_url)

    def tearDown(self):
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_audit_log_stores_provider_fields(self):
        alert_payload = {
            "dispatch_id": "DISP-TEST-001",
            "threat_event_id": "EVT-RAIN-99",
            "farmer_id": "F002",
            "farmer_name": "Gurpreet Kaur",
            "phone": "+91-9876543211",
            "channel": "sms",
            "language": "pa",
            "urgency": "critical",
            "message": "Heavy Rain Alert",
            "status": "success",
            "provider": "vonage",
            "provider_message_id": "VONAGE-MSG-12345",
            "error_message": None,
            "dispatched_at": "2026-09-17T12:00:00Z"
        }

        disp_id = log_alert(alert_payload, db_url=self.db_url)
        self.assertEqual(disp_id, "DISP-TEST-001")

        logs = get_alert_logs(farmer_id="F002", db_url=self.db_url)
        self.assertEqual(len(logs), 1)
        row = logs[0]
        self.assertEqual(row["phone"], "+91-9876543211")
        self.assertEqual(row["provider"], "vonage")
        self.assertEqual(row["provider_message_id"], "VONAGE-MSG-12345")
        self.assertEqual(row["status"], "success")
        self.assertIsNone(row["error_message"])


class TestVonageDeliveryReceiptWebhook(unittest.TestCase):
    """
    Unit tests for Vonage Delivery Receipt (DLR) webhook handling:
    - Valid delivery receipts updating alert record to 'delivered'
    - Failed, rejected, expired, and unknown statuses
    - Cryptographic signature validation & rejection of invalid signatures
    - Unknown message ID handling
    - Idempotency / duplicate callback handling
    """

    def setUp(self):
        import tempfile
        import shutil
        self.temp_dir = tempfile.mkdtemp()
        self.db_file = os.path.join(self.temp_dir, "test_dlr.db")
        self.db_url = f"sqlite:///{self.db_file}"
        init_db(self.db_url)

        # Seed an initial dispatched alert record in 'success' status
        self.test_message_id = "VONAGE-DLR-MSG-001"
        self.seed_alert = {
            "dispatch_id": "DISP-DLR-001",
            "threat_event_id": "EVT-STORM-01",
            "farmer_id": "F001",
            "farmer_name": "Harpreet Singh",
            "phone": "+91-9876543210",
            "channel": "sms",
            "language": "en",
            "urgency": "high",
            "message": "Storm Warning",
            "status": "success",
            "provider": "vonage",
            "provider_message_id": self.test_message_id,
            "error_message": None,
            "dispatched_at": "2026-09-17T10:00:00Z"
        }
        log_alert(self.seed_alert, db_url=self.db_url)

    def tearDown(self):
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_valid_delivered_dlr_updates_audit_record(self):
        from backend.app import handle_vonage_delivery_receipt
        from database.connection import get_alert_log_by_provider_message_id

        dlr_payload = {
            "msisdn": "919876543210",
            "to": "WeatherGPT",
            "messageId": self.test_message_id,
            "price": "0.0333",
            "status": "delivered",
            "scts": "2609171200",
            "err-code": "0",
            "message-timestamp": "2026-09-17 12:00:00"
        }

        # In production unsigned callbacks are rejected; test allow_unsigned_when_no_secret=True
        with patch("backend.app.settings.credentials.vonage_signature_secret", None):
            res = handle_vonage_delivery_receipt(
                dlr_payload,
                db_url=self.db_url,
                allow_unsigned_when_no_secret=True,
            )

        self.assertEqual(res["status"], "updated")
        self.assertEqual(res["delivery_status"], "delivered")
        self.assertTrue(res["matched"])

        # Check DB directly
        updated = get_alert_log_by_provider_message_id(self.test_message_id, db_url=self.db_url)
        self.assertIsNotNone(updated)
        self.assertEqual(updated["status"], "delivered")

    def test_failed_dlr_records_error_message(self):
        from tools.notifications.sms import parse_vonage_delivery_receipt

        dlr_payload = {
            "messageId": self.test_message_id,
            "status": "failed",
            "err-code": "1",
            "message-timestamp": "2026-09-17 12:05:00"
        }
        parsed = parse_vonage_delivery_receipt(dlr_payload)
        self.assertEqual(parsed["status"], "failed")
        self.assertEqual(parsed["error_code"], "1")
        self.assertIn("Unknown subscriber", parsed["error_message"])

    def test_rejected_and_expired_statuses(self):
        from tools.notifications.sms import parse_vonage_delivery_receipt

        parsed_rej = parse_vonage_delivery_receipt({"messageId": "M1", "status": "rejected", "err-code": "3"})
        self.assertEqual(parsed_rej["status"], "rejected")
        self.assertIn("Call barred", parsed_rej["error_message"])

        parsed_exp = parse_vonage_delivery_receipt({"messageId": "M2", "status": "expired", "err-code": "2"})
        self.assertEqual(parsed_exp["status"], "expired")
        self.assertIn("Absent subscriber", parsed_exp["error_message"])

    def test_unknown_status_fallback(self):
        from tools.notifications.sms import parse_vonage_delivery_receipt

        parsed = parse_vonage_delivery_receipt({"messageId": "M3", "status": "nonexistent_status"})
        self.assertEqual(parsed["status"], "unknown")

    def test_signature_validation_success_and_failure(self):
        from tools.notifications.sms import verify_vonage_signature
        import hmac
        import hashlib

        secret = "test_webhook_signing_secret"
        params = {
            "messageId": "0A0000000123",
            "msisdn": "919876543210",
            "status": "delivered",
            "err-code": "0",
            "note": "a=1&b=2"  # test & and = replacement with _
        }

        # Build official signature: leading &, sorted keys, & and = replaced with _
        sorted_pairs = sorted([(k, v) for k, v in params.items()])
        sanitized = [f"{k}={str(v).replace('&', '_').replace('=', '_')}" for k, v in sorted_pairs]
        sig_base = "&" + "&".join(sanitized)
        valid_sig = hmac.new(secret.encode("utf-8"), sig_base.encode("utf-8"), hashlib.sha256).hexdigest()

        params_with_valid_sig = dict(params)
        params_with_valid_sig["sig"] = valid_sig
        self.assertTrue(verify_vonage_signature(params_with_valid_sig, signature_secret=secret, method="sha256"))

        # Invalid signature
        params_with_bad_sig = dict(params)
        params_with_bad_sig["sig"] = "bad_signature_hash"
        self.assertFalse(verify_vonage_signature(params_with_bad_sig, signature_secret=secret, method="sha256"))

    def test_signature_validation_methods_supported(self):
        from tools.notifications.sms import verify_vonage_signature
        import hmac
        import hashlib

        secret = "multi_method_secret"
        params = {"messageId": "M001", "status": "delivered"}
        sorted_pairs = sorted([(k, v) for k, v in params.items()])
        sig_base = "&" + "&".join(f"{k}={v}" for k, v in sorted_pairs)

        # sha512
        sig_sha512 = hmac.new(secret.encode("utf-8"), sig_base.encode("utf-8"), hashlib.sha512).hexdigest()
        p512 = dict(params, sig=sig_sha512)
        self.assertTrue(verify_vonage_signature(p512, signature_secret=secret, method="sha512"))

        # md5hmac
        sig_md5 = hmac.new(secret.encode("utf-8"), sig_base.encode("utf-8"), hashlib.md5).hexdigest()
        pmd5 = dict(params, sig=sig_md5)
        self.assertTrue(verify_vonage_signature(pmd5, signature_secret=secret, method="md5hmac"))

    def test_webhook_handler_rejects_invalid_signature(self):
        from backend.app import handle_vonage_delivery_receipt

        payload = {
            "messageId": self.test_message_id,
            "status": "delivered",
            "sig": "invalid_signature_string"
        }
        with self.assertRaises(PermissionError):
            handle_vonage_delivery_receipt(payload, signature_secret="enforced_secret")

    def test_webhook_handler_rejects_unsigned_callback_in_production(self):
        from backend.app import handle_vonage_delivery_receipt

        payload = {
            "messageId": self.test_message_id,
            "status": "delivered",
            "err-code": "0"
        }
        # In production (when allow_unsigned_when_no_secret=False), rejecting unsigned callbacks
        with self.assertRaises(PermissionError):
            handle_vonage_delivery_receipt(payload, signature_secret="required_secret", allow_unsigned_when_no_secret=False)

    def test_unknown_message_id_returns_unmatched(self):
        from backend.app import handle_vonage_delivery_receipt

        payload = {
            "messageId": "NONEXISTENT-MESSAGE-ID-9999",
            "status": "delivered",
            "err-code": "0"
        }
        res = handle_vonage_delivery_receipt(
            payload,
            signature_secret=None,
            db_url=self.db_url,
            allow_unsigned_when_no_secret=True,
        )
        self.assertEqual(res["status"], "unmatched")
        self.assertFalse(res["matched"])
        self.assertIn("No alert record found", res["detail"])

    def test_duplicate_delivery_receipt_is_ignored_idempotently(self):
        from backend.app import handle_vonage_delivery_receipt
        from database.connection import log_alert

        test_msg_id = "MSG-IDEMPOTENT-001"
        log_alert({
            "dispatch_id": "DISP-IDEM-001",
            "threat_event_id": "EVT-1",
            "farmer_id": "F001",
            "farmer_name": "Farmer 1",
            "phone": "+91-9876543210",
            "channel": "sms",
            "language": "en",
            "urgency": "high",
            "message": "Test",
            "status": "delivered",
            "provider": "vonage",
            "provider_message_id": test_msg_id,
            "error_message": None,
        }, db_url=self.db_url)

        # Sending another 'delivered' DLR for the same message ID
        payload = {
            "messageId": test_msg_id,
            "status": "delivered",
            "err-code": "0"
        }
        res = handle_vonage_delivery_receipt(
            payload,
            signature_secret=None,
            db_url=self.db_url,
            allow_unsigned_when_no_secret=True,
        )
        self.assertEqual(res["status"], "ignored")
        self.assertTrue(res["matched"])
        self.assertIn("already in status 'delivered'", res["detail"])

    def test_webhook_http_endpoint_invalid_signature_returns_401(self):
        from fastapi.testclient import TestClient
        from backend.app import app

        client = TestClient(app)
        with patch("backend.app.settings.credentials.vonage_signature_secret", "my_secret"):
            response = client.post(
                "/api/webhooks/vonage/delivery-receipt",
                json={"messageId": self.test_message_id, "status": "delivered", "sig": "bad_sig"}
            )
            self.assertEqual(response.status_code, 401)
            self.assertIn("Invalid webhook signature", response.json()["detail"])

    def test_webhook_http_endpoint_valid_json(self):
        from fastapi.testclient import TestClient
        from backend.app import app
        import hmac
        import hashlib

        client = TestClient(app)
        secret = "test_endpoint_secret"
        payload = {
            "messageId": "NONEXISTENT-MSG",
            "status": "delivered",
            "msisdn": "919934768317"
        }
        sorted_pairs = sorted([(k, v) for k, v in payload.items()])
        sig_base = "&" + "&".join(f"{k}={v}" for k, v in sorted_pairs)
        valid_sig = hmac.new(secret.encode("utf-8"), sig_base.encode("utf-8"), hashlib.sha256).hexdigest()
        payload["sig"] = valid_sig

        with patch("backend.app.settings.credentials.vonage_signature_secret", secret):
            response = client.post(
                "/api/webhooks/vonage/delivery-receipt",
                json=payload
            )
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data["status"], "unmatched")
            self.assertFalse(data["matched"])


if __name__ == "__main__":
    unittest.main()
