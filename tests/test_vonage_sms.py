import os
import unittest
from unittest.mock import patch, MagicMock

from agents.executor.dispatcher import AlertDispatcher, VonageSMSProvider
from agents.executor.schemas import TaskStatus, DispatchChannel


class TestVonageSMSIntegration(unittest.TestCase):
    def setUp(self):
        self.dispatcher = AlertDispatcher()
        self.sample_farmer = {
            "id": "F001",
            "name": "Gurpreet Singh",
            "crop": "Wheat",
            "phone": "+919876543210",
            "language": "en",
        }

    # 1. SMS_ENABLED=false -> no Vonage call, queued behavior preserved
    @patch.dict(
        os.environ,
        {
            "SMS_ENABLED": "false",
            "SMS_PROVIDER": "vonage"
        },
        clear=True
    )
    @patch("agents.executor.dispatcher.VonageSMSProvider.send_sms")
    def test_sms_disabled_preserves_queued_status(self, mock_send):
        alert = self.dispatcher.create_sms_alert(
            threat_id="EVT-TEST-001",
            farmer=self.sample_farmer,
            action_title="Postpone Scheduled Irrigation",
        )

        self.assertIsNotNone(alert)
        self.assertEqual(alert.status, TaskStatus.QUEUED)
        self.assertEqual(alert.channel, DispatchChannel.SMS)

        mock_send.assert_not_called()

    # 2. SMS_ENABLED=true + SMS_PROVIDER=vonage ->
    # provider receives message and destination
    @patch.dict(
        os.environ,
        {
            "SMS_ENABLED": "true",
            "SMS_PROVIDER": "vonage",
            "VONAGE_API_KEY": "dummy_key",
            "VONAGE_API_SECRET": "dummy_secret",
            "VONAGE_FROM": "WeatherGPT",
        },
        clear=True,
    )
    @patch("agents.executor.dispatcher.VonageSMSProvider.send_sms")
    def test_sms_enabled_calls_vonage_provider(self, mock_send):
        mock_send.return_value = {
            "success": True,
            "message_id": "VONAGE-MSG-123",
            "error": None
        }

        alert = self.dispatcher.create_sms_alert(
            threat_id="EVT-TEST-002",
            farmer=self.sample_farmer,
            action_title="Postpone Scheduled Irrigation",
        )

        self.assertIsNotNone(alert)

        mock_send.assert_called_once()

        call_kwargs = mock_send.call_args.kwargs

        self.assertEqual(
            call_kwargs["to_phone"],
            "+919876543210"
        )

        self.assertIn(
            "Gurpreet Singh",
            call_kwargs["message"]
        )

    # 3. Vonage success -> controlled SUCCESS result
    @patch.dict(
        os.environ,
        {
            "SMS_ENABLED": "true",
            "SMS_PROVIDER": "vonage",
            "VONAGE_API_KEY": "dummy_key",
            "VONAGE_API_SECRET": "dummy_secret",
        },
        clear=True,
    )
    @patch("agents.executor.dispatcher.VonageSMSProvider.send_sms")
    def test_vonage_success_returns_success_status(self, mock_send):
        mock_send.return_value = {
            "success": True,
            "message_id": "VONAGE-123",
            "error": None
        }

        alert = self.dispatcher.create_sms_alert(
            threat_id="EVT-TEST-003",
            farmer=self.sample_farmer,
            action_title="Halt Spraying due to Wind Drift",
        )

        self.assertEqual(
            alert.status,
            TaskStatus.SUCCESS
        )

    # 4. Vonage failure -> controlled FAILED result,
    # Executor continues safely
    @patch.dict(
        os.environ,
        {
            "SMS_ENABLED": "true",
            "SMS_PROVIDER": "vonage",
            "VONAGE_API_KEY": "dummy_key",
            "VONAGE_API_SECRET": "dummy_secret",
        },
        clear=True,
    )
    @patch("agents.executor.dispatcher.VonageSMSProvider.send_sms")
    def test_vonage_failure_handled_gracefully(self, mock_send):
        mock_send.return_value = {
            "success": False,
            "message_id": None,
            "error": "Insufficient balance",
        }

        alert = self.dispatcher.create_sms_alert(
            threat_id="EVT-TEST-004",
            farmer=self.sample_farmer,
            action_title="Clear Field Drainage Channels",
        )

        self.assertIsNotNone(alert)

        self.assertEqual(
            alert.status,
            TaskStatus.FAILED
        )

        self.assertIn(
            "Insufficient balance",
            alert.message
        )

    # 5. Missing Vonage credentials ->
    # configuration error, status FAILED, no crash
    @patch.dict(
        os.environ,
        {
            "SMS_ENABLED": "true",
            "SMS_PROVIDER": "vonage",
            "VONAGE_API_KEY": "",
            "VONAGE_API_SECRET": "",
        },
        clear=True,
    )
    def test_missing_credentials_fails_gracefully(self):
        alert = self.dispatcher.create_sms_alert(
            threat_id="EVT-TEST-005",
            farmer=self.sample_farmer,
            action_title="Clear Field Drainage Channels",
        )

        self.assertIsNotNone(alert)

        self.assertEqual(
            alert.status,
            TaskStatus.FAILED
        )

        self.assertIn(
            "Missing Vonage credentials",
            alert.message
        )

    # 6. Multilingual SMS templates
    #
    # Requirement:
    # English -> complete English
    # Hindi   -> complete Hindi
    # Punjabi -> complete Punjabi
    @patch.dict(
        os.environ,
        {
            "SMS_ENABLED": "false"
        },
        clear=True
    )
    def test_multilingual_templates_intact(self):
        # ---------------------------------------------------------
        # Hindi
        # ---------------------------------------------------------
        hi_farmer = {
            **self.sample_farmer,
            "language": "hi"
        }

        d1 = AlertDispatcher()

        hi_alert = d1.create_sms_alert(
            "EVT-HI",
            hi_farmer,
            "सिंचाई स्थगित करें"
        )

        self.assertIsNotNone(hi_alert)

        # Hindi WeatherGPT alert heading
        self.assertIn(
            "वेदरजीपीटी चेतावनी",
            hi_alert.message
        )

        # Hindi crop name
        self.assertIn(
            "गेहूं",
            hi_alert.message
        )

        # Hindi instruction
        self.assertIn(
            "सिंचाई स्थगित करें",
            hi_alert.message
        )

        # Make sure the English crop name is not present
        self.assertNotIn(
            "Wheat",
            hi_alert.message
        )

        # ---------------------------------------------------------
        # Punjabi
        # ---------------------------------------------------------
        pa_farmer = {
            **self.sample_farmer,
            "language": "pa"
        }

        d2 = AlertDispatcher()

        pa_alert = d2.create_sms_alert(
            "EVT-PA",
            pa_farmer,
            "ਸਿੰਚਾਈ ਮੁਲਤਵੀ ਕਰੋ"
        )

        self.assertIsNotNone(pa_alert)

        # Punjabi WeatherGPT alert heading
        self.assertIn(
            "ਵੇਦਰਜੀਪੀਟੀ ਚੇਤਾਵਨੀ",
            pa_alert.message
        )

        # Punjabi crop name
        self.assertIn(
            "ਕਣਕ",
            pa_alert.message
        )

        # Punjabi instruction
        self.assertIn(
            "ਸਿੰਚਾਈ ਮੁਲਤਵੀ ਕਰੋ",
            pa_alert.message
        )

        # Make sure the English crop name is not present
        self.assertNotIn(
            "Wheat",
            pa_alert.message
        )

    # 7. English SMS remains completely English
    @patch.dict(
        os.environ,
        {
            "SMS_ENABLED": "false"
        },
        clear=True
    )
    def test_english_template(self):
        en_farmer = {
            **self.sample_farmer,
            "language": "en"
        }

        dispatcher = AlertDispatcher()

        alert = dispatcher.create_sms_alert(
            "EVT-EN",
            en_farmer,
            "Postpone Scheduled Irrigation"
        )

        self.assertIsNotNone(alert)

        self.assertIn(
            "WeatherGPT Alert",
            alert.message
        )

        self.assertIn(
            "Wheat",
            alert.message
        )

        self.assertIn(
            "Postpone Scheduled Irrigation",
            alert.message
        )

        # English message should not contain Hindi/Punjabi text
        self.assertNotIn(
            "वेदरजीपीटी",
            alert.message
        )

        self.assertNotIn(
            "ਵੇਦਰਜੀਪੀਟੀ",
            alert.message
        )


if __name__ == "__main__":
    unittest.main()