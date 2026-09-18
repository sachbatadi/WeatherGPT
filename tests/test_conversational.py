import os
import unittest
from agents.conversational import (
    ChatRequest,
    ConversationalQuery,
    ConversationalService,
    ContextManager,
    IntentType,
    QueryRouter,
    QueryUnderstanding,
    ResponseGenerator,
)


class TestConversationalLayer(unittest.TestCase):
    def setUp(self):
        os.environ["WEATHER_MODE"] = "mock"
        self.service = ConversationalService()
        self.understanding = QueryUnderstanding()
        self.router = QueryRouter()
        self.context = ContextManager()

    # 1. Current weather query
    def test_current_weather_query(self):
        req = ChatRequest(message="What is the weather in Jalandhar?")
        res = self.service.process_query(req)
        self.assertEqual(res.intent, IntentType.WEATHER)
        self.assertEqual(res.location, "Jalandhar")
        self.assertIn("Jalandhar", res.response)

    # 2. Forecast query (mock mode without timestamps)
    def test_forecast_query(self):
        req = ChatRequest(message="Will it rain tomorrow in Ludhiana?")
        res = self.service.process_query(req)
        self.assertEqual(res.intent, IntentType.FORECAST)
        self.assertEqual(res.location, "Ludhiana")
        self.assertIn("does not include a timestamped forecast", res.response)

    # 3. Forecast query with future timestamped dataset
    def test_timestamped_forecast(self):
        mock_timestamped_weather = {
            "source": "open-meteo",
            "location": "Jalandhar",
            "current": {
                "temperature_c": 25.0,
                "humidity_pct": 70.0,
                "wind_speed_kmh": 10.0,
            },
            "hourly": {
                "time": [
                    "2026-09-18T00:00",
                    "2026-09-18T06:00",
                    "2026-09-18T12:00",
                    "2026-09-19T00:00",
                    "2026-09-19T06:00",
                    "2026-09-19T12:00",
                ],
                "temperature_c": [
                    22.0,
                    25.0,
                    30.0,
                    23.0,
                    26.0,
                    29.0,
                ],
                "precipitation_mm": [
                    5.0,
                    10.0,
                    0.0,
                    8.0,
                    12.0,
                    3.0,
                ],
                "precipitation_probability_pct": [
                    60.0,
                    80.0,
                    10.0,
                    70.0,
                    85.0,
                    40.0,
                ],
            },
        }

        class MockTimestampedRouter(QueryRouter):
            def _get_weather(self, location: str):
                return mock_timestamped_weather

        custom_service = ConversationalService(
            query_router=MockTimestampedRouter()
        )

        req = ChatRequest(
            message="Will it rain tomorrow in Jalandhar?"
        )

        res = custom_service.process_query(req)

        self.assertEqual(res.intent, IntentType.FORECAST)
        self.assertTrue(
            res.raw_data.get("has_tomorrow_forecast")
        )
        self.assertIn(
            "Tomorrow's forecast for Jalandhar",
            res.response
        )
        self.assertIn("85", res.response)

    # 4. Warning query
    def test_warning_query(self):
        req = ChatRequest(
            message="Is there any heavy rain warning in Jalandhar?"
        )
        res = self.service.process_query(req)
        self.assertEqual(res.intent, IntentType.WARNING)
        self.assertIn("Sentinel", res.agent_used)

    # 5. Agriculture query
    def test_agriculture_query(self):
        req = ChatRequest(
            message="Should I irrigate my wheat today in Jalandhar?"
        )
        res = self.service.process_query(req)
        self.assertEqual(res.intent, IntentType.AGRICULTURE)
        self.assertIn("Strategist", res.agent_used)
        self.assertTrue(len(res.actions) > 0)

    # 6. Agriculture explanation
    def test_agriculture_explanation(self):
        req = ChatRequest(
            message="Why was my irrigation postponed?",
            farmer_id="F001"
        )
        res = self.service.process_query(req)
        self.assertEqual(
            res.intent,
            IntentType.AGRICULTURE_EXPLANATION
        )
        self.assertTrue(
            any(
                w in res.response.lower()
                for w in [
                    "adjusted",
                    "postponed",
                    "rain",
                    "irrigation"
                ]
            )
        )

    # 7. Climate query
    def test_climate_query(self):
        req = ChatRequest(
            message="How has rainfall changed over the years in Punjab?"
        )
        res = self.service.process_query(req)
        self.assertEqual(res.intent, IntentType.CLIMATE)
        self.assertIn("not currently connected", res.response)

    # 8. Emergency query
    def test_emergency_query(self):
        req = ChatRequest(
            message="Emergency in my area in Jalandhar"
        )
        res = self.service.process_query(req)
        self.assertEqual(res.intent, IntentType.EMERGENCY)
        self.assertIn("EMERGENCY", res.response)

    # 9. Unknown query
    def test_unknown_query(self):
        req = ChatRequest(
            message="xyz abc 123 456"
        )
        res = self.service.process_query(req)
        self.assertEqual(res.intent, IntentType.UNKNOWN)
        self.assertIn("WeatherGPT", res.response)

    # 10. Location extraction
    def test_location_extraction(self):
        parsed = self.understanding.parse(
            "What is the temperature in Patiala?"
        )
        self.assertEqual(parsed.location, "Patiala")

    # 11. Relative time extraction
    def test_relative_time_extraction(self):
        parsed = self.understanding.parse(
            "Weather forecast for tomorrow in Bathinda"
        )
        self.assertEqual(
            parsed.time_reference,
            "tomorrow"
        )

    # 12. Crop extraction
    def test_crop_extraction(self):
        parsed = self.understanding.parse(
            "Should I spray my paddy crop today?"
        )
        self.assertEqual(parsed.crop, "paddy")

    # 13. Conversation context
    def test_conversation_context(self):
        session_id = "test_session_123"

        req1 = ChatRequest(
            message="What is the weather in Jalandhar?",
            conversation_id=session_id
        )

        res1 = self.service.process_query(req1)

        self.assertEqual(
            res1.location,
            "Jalandhar"
        )

        req2 = ChatRequest(
            message="What about tomorrow?",
            conversation_id=session_id
        )

        res2 = self.service.process_query(req2)

        self.assertEqual(
            res2.location,
            "Jalandhar"
        )

        self.assertEqual(
            res2.intent,
            IntentType.FORECAST
        )

        self.assertIn(
            "does not include a timestamped forecast",
            res2.response
        )

    # 14. Hindi query
    def test_hindi_query(self):
        req = ChatRequest(
            message="आज जालंधर में मौसम कैसा है?"
        )
        res = self.service.process_query(req)

        self.assertEqual(
            res.language,
            "hi"
        )

        self.assertIn(
            "तापमान",
            res.response
        )

    # 15. Punjabi query
    def test_punjabi_query(self):
        req = ChatRequest(
            message="ਜਲੰਧਰ ਵਿੱਚ ਅੱਜ ਮੌਸਮ ਕਿਹੋ ਜਿਹਾ ਹੈ?"
        )
        res = self.service.process_query(req)

        self.assertEqual(
            res.language,
            "pa"
        )

        self.assertIn(
            "ਤਾਪਮਾਨ",
            res.response
        )

    # 16. No hallucinated weather values
    def test_no_hallucinated_weather_values(self):
        req = ChatRequest(
            message="What is the weather in Jalandhar?"
        )
        res = self.service.process_query(req)

        raw = res.raw_data or {}
        cur = raw.get("current", {})
        temp = cur.get("temperature_c")

        if temp is not None:
            self.assertIn(
                str(temp),
                res.response
            )

    # 17. Existing weather tool integration
    def test_existing_weather_tool_integration(self):
        parsed = self.understanding.parse(
            "Weather in Jalandhar"
        )

        grounded = self.router.route(parsed)

        self.assertIsNotNone(
            grounded.raw_data
        )

        self.assertIn(
            "current",
            grounded.raw_data
        )

    # 18. Existing Strategist integration
    def test_existing_strategist_integration(self):
        parsed = self.understanding.parse(
            "Should I irrigate my wheat today in Jalandhar?"
        )

        grounded = self.router.route(parsed)

        self.assertEqual(
            grounded.agent_used,
            "Strategist"
        )

    # 19. Existing Executor explanation integration
    def test_existing_executor_explanation_integration(self):
        parsed = self.understanding.parse(
            "Why was my irrigation postponed?",
            override_farmer_id="F001"
        )

        grounded = self.router.route(parsed)

        self.assertIn(
            "Farmer",
            grounded.text
        )

    # 20. Mock weather mode
    def test_mock_weather_mode(self):
        os.environ["WEATHER_MODE"] = "mock"

        req = ChatRequest(
            message="What is the weather in Jalandhar?"
        )

        res = self.service.process_query(req)

        self.assertEqual(
            res.raw_data.get("source"),
            "mock"
        )


if __name__ == "__main__":
    unittest.main()