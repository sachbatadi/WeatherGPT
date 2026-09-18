import unittest
from fastapi.testclient import TestClient
from backend.app import app


class TestBackendAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_api_health(self):
        res = self.client.get("/health")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data.get("status"), "healthy")

    def test_api_chat_weather_query(self):
        payload = {
            "message": "What is the weather in Jalandhar?",
            "location": "Jalandhar",
            "mode": "mock",
        }
        res = self.client.post("/api/chat", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data.get("intent"), "weather")
        self.assertEqual(data.get("location"), "Jalandhar")
        self.assertIn("reply", data)
        self.assertIn("Jalandhar", data.get("reply"))

    def test_api_chat_forecast_query(self):
        payload = {
            "message": "Will it rain tomorrow?",
            "location": "Jalandhar",
            "mode": "mock",
        }
        res = self.client.post("/api/chat", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data.get("intent"), "forecast")
        self.assertEqual(data.get("location"), "Jalandhar")

    def test_api_chat_agriculture_query(self):
        payload = {
            "message": "Should I irrigate my wheat today?",
            "location": "Jalandhar",
            "farmer_id": "F001",
            "crop": "wheat",
            "mode": "mock",
            "scenario": "heavy_rain",
        }
        res = self.client.post("/api/chat", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data.get("intent"), "agriculture")
        self.assertEqual(data.get("agent_used"), "Strategist")
        self.assertTrue(len(data.get("actions", [])) > 0)

    def test_api_chat_explanation_query(self):
        payload = {
            "message": "Why was my irrigation postponed?",
            "farmer_id": "F001",
            "mode": "mock",
            "scenario": "heavy_rain",
        }
        res = self.client.post("/api/chat", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data.get("intent"), "agriculture_explanation")
        self.assertIn("Gurpreet Singh", data.get("reply"))

    def test_api_chat_multi_turn_context(self):
        session_id = "api_session_turn_123"

        t1_payload = {
            "message": "What is the weather in Jalandhar?",
            "conversation_id": session_id,
        }
        res1 = self.client.post("/api/chat", json=t1_payload)
        self.assertEqual(res1.status_code, 200)
        data1 = res1.json()
        self.assertEqual(data1.get("location"), "Jalandhar")

        t2_payload = {
            "message": "What about tomorrow?",
            "conversation_id": session_id,
        }
        res2 = self.client.post("/api/chat", json=t2_payload)
        self.assertEqual(res2.status_code, 200)
        data2 = res2.json()
        self.assertEqual(data2.get("location"), "Jalandhar")
        self.assertEqual(data2.get("intent"), "forecast")

    def test_api_chat_hindi(self):
        payload = {
            "message": "आज जालंधर में मौसम कैसा है?",
            "conversation_id": "hi_session",
        }
        res = self.client.post("/api/chat", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data.get("language"), "hi")
        self.assertIn("तापमान", data.get("reply"))

    def test_api_chat_punjabi(self):
        payload = {
            "message": "ਜਲੰਧਰ ਵਿੱਚ ਅੱਜ ਮੌਸਮ ਕਿਹੋ ਜਿਹਾ ਹੈ?",
            "conversation_id": "pa_session",
        }
        res = self.client.post("/api/chat", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data.get("language"), "pa")
        self.assertIn("ਤਾਪਮਾਨ", data.get("reply"))


if __name__ == "__main__":
    unittest.main()
