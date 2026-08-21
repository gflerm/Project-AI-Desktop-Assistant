from __future__ import annotations

import os
from pathlib import Path
from types import SimpleNamespace
import unittest

os.environ.setdefault("TARS_TOKEN", "test-token-that-is-at-least-24-characters")
os.environ.setdefault("TARS_TELEMETRY_ENABLED", "false")

from fastapi.testclient import TestClient

from tars_gateway import main
from tars_gateway.persistent_memory import PersistentMemory
from tars_gateway.protocol import (
    BYTES_PER_FRAME,
    KIND_MICROPHONE,
    KIND_TTS,
    decode_audio_chunk,
    encode_audio_chunk,
)


class FakeServices:
    async def health(self):
        return {"whisper": True, "piper": True, "ollama": True}

    async def transcribe(self, pcm: bytes, prompt: str = "") -> str:
        return "hello tars"

    async def converse(
        self, device_id: str, transcript: str, provider_override: str | None = None
    ) -> str:
        self.provider_override = provider_override
        return "Hello. I am ready."

    async def converse_result(
        self, device_id: str, transcript: str, provider_override: str | None = None,
        *, remember: bool = True,
    ):
        self.provider_override = provider_override
        self.last_transcript = transcript
        return SimpleNamespace(
            text="Hello. I am ready.", provider="gemini",
            fallback_used=False, google_search_used=False, grounding_source=None,
            routing_reason="test-route", finish_reason="STOP", answer_complete=True,
        )

    async def synthesize(self, text: str) -> bytes:
        return bytes(BYTES_PER_FRAME)

    def inference_status(self):
        return {"active": 0, "waiting": 0, "maximum_parallel": 1}


class FakeWeatherResult:
    def describe(self) -> str:
        return "It is clear in Cape Town, around 21 degrees Celsius."


class FakeWeather:
    async def current(self, place: str | None = None):
        self.place = place
        return FakeWeatherResult()


class FakeSystemSnapshot:
    def as_dict(self):
        return {"temperature_c": 50.0, "memory_total_gib": 7.9}

    def describe(self, components):
        return "The Pi is at 50.0 degrees Celsius. All measured services are healthy."


class FakeSystemStatus:
    def snapshot(self):
        return FakeSystemSnapshot()


class WebSocketProtocolTests(unittest.TestCase):
    def setUp(self) -> None:
        import tempfile

        main.services = FakeServices()
        main.weather = FakeWeather()
        main.pi_status = FakeSystemStatus()
        self.memory_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.memory_directory.cleanup)
        main.persistent_memory = PersistentMemory(
            str(Path(self.memory_directory.name) / "memory.json")
        )
        self.client = TestClient(main.app)
        self.headers = {"X-Tars-Token": os.environ["TARS_TOKEN"]}

    def test_complete_turn(self) -> None:
        with self.client.websocket_connect("/ws/v1", headers=self.headers) as websocket:
            websocket.send_json(
                {
                    "v": 1,
                    "type": "hello",
                    "session_id": "session-a",
                    "message_id": 1,
                    "device_id": "p4-test",
                }
            )
            self.assertEqual(websocket.receive_json()["type"], "hello.ack")

            websocket.send_json(
                {
                    "v": 1,
                    "type": "audio.start",
                    "session_id": "session-a",
                    "message_id": 2,
                    "utterance_id": 4,
                    "sample_rate_hz": 16000,
                    "sample_bits": 16,
                    "channels": 1,
                }
            )
            websocket.send_bytes(
                encode_audio_chunk(
                    kind=KIND_MICROPHONE,
                    utterance_id=4,
                    sequence=0,
                    timestamp_ms=0,
                    payload=bytes(BYTES_PER_FRAME),
                )
            )
            ack = websocket.receive_json()
            self.assertEqual(ack["type"], "ack")
            self.assertEqual(ack["highest_contiguous_sequence"], 0)

            websocket.send_json(
                {
                    "v": 1,
                    "type": "audio.end",
                    "session_id": "session-a",
                    "message_id": 3,
                    "utterance_id": 4,
                    "last_sequence": 0,
                    "dropped_frames": 0,
                }
            )
            self.assertEqual(websocket.receive_json()["type"], "stt.final")
            self.assertEqual(websocket.receive_json()["type"], "assistant.text")
            self.assertEqual(websocket.receive_json()["type"], "tts.start")
            tts = decode_audio_chunk(websocket.receive_bytes(), expected_kind=KIND_TTS)
            self.assertEqual(tts.utterance_id, 4)
            self.assertEqual(websocket.receive_json()["type"], "tts.end")

    def test_south_africa_time_uses_system_clock_without_llm(self) -> None:
        reply = main.south_africa_time_reply("What is the current time?")
        self.assertIn("South African Standard Time", reply)
        self.assertIsNone(main.south_africa_time_reply("Explain clock synchronization"))

    def test_identity_is_james_without_model_routing(self) -> None:
        response = self.client.post(
            "/v1/test/chat",
            headers=self.headers,
            json={"text": "Who are you and what do you do?", "device_id": "identity-test"},
        )
        payload = response.json()
        self.assertEqual(payload["route"], "system:identity")
        self.assertEqual(payload["provider"], "identity-registry")
        self.assertIn("My name is James", payload["text"])
        self.assertNotIn("My name is TARS", payload["text"])

    def test_sequence_gap_cancels_turn(self) -> None:
        with self.client.websocket_connect("/ws/v1", headers=self.headers) as websocket:
            websocket.send_json(
                {"v": 1, "type": "hello", "session_id": "session-b", "message_id": 1}
            )
            websocket.receive_json()
            websocket.send_json(
                {
                    "v": 1,
                    "type": "audio.start",
                    "session_id": "session-b",
                    "message_id": 2,
                    "utterance_id": 1,
                    "sample_rate_hz": 16000,
                    "sample_bits": 16,
                    "channels": 1,
                }
            )
            websocket.send_bytes(
                encode_audio_chunk(
                    kind=KIND_MICROPHONE,
                    utterance_id=1,
                    sequence=1,
                    timestamp_ms=0,
                    payload=bytes(BYTES_PER_FRAME),
                )
            )
            error = websocket.receive_json()
            self.assertEqual(error["type"], "error")
            self.assertEqual(error["code"], "sequence_gap")

    def test_authenticated_windows_test_endpoints(self) -> None:
        stt = self.client.post(
            "/v1/test/stt",
            headers={**self.headers, "Content-Type": "application/octet-stream"},
            content=bytes(BYTES_PER_FRAME),
        )
        self.assertEqual(stt.status_code, 200)
        self.assertEqual(stt.json()["transcript"], "hello tars")
        chat = self.client.post(
            "/v1/test/chat",
            headers=self.headers,
            json={"text": "Status?", "device_id": "windows-test"},
        )
        self.assertEqual(chat.status_code, 200)
        self.assertEqual(chat.json()["text"], "Hello. I am ready.")
        self.assertEqual(chat.json()["route"], "auto")
        speech = self.client.post(
            "/v1/test/speech",
            headers=self.headers,
            json={"text": chat.json()["text"]},
        )
        self.assertEqual(speech.status_code, 200)
        self.assertEqual(speech.headers["content-type"], "audio/wav")
        self.assertTrue(speech.content.startswith(b"RIFF"))

    def test_test_endpoints_require_token(self) -> None:
        response = self.client.post("/v1/test/chat", json={"text": "Status?"})
        self.assertEqual(response.status_code, 401)

    def test_stt_rejects_empty_audio(self) -> None:
        response = self.client.post("/v1/test/stt", headers=self.headers, content=b"")
        self.assertEqual(response.status_code, 400)

    def test_weather_query_uses_live_tool_before_llm(self) -> None:
        response = self.client.post(
            "/v1/test/chat",
            headers=self.headers,
            json={"text": "What is the weather in Cape Town right now?"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["route"], "weather:open-meteo")
        self.assertEqual(main.weather.place, "Cape Town")
        self.assertIn("server_ms", response.json())

    def test_pi_status_query_uses_read_only_tool_before_llm(self) -> None:
        response = self.client.post(
            "/v1/test/chat",
            headers=self.headers,
            json={"text": "How hot is the Pi and what is its memory usage?"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["route"], "system:pi-status")
        self.assertEqual(response.json()["provider"], "system-status")
        self.assertIn("50.0 degrees Celsius", response.json()["text"])

    def test_authenticated_direct_system_status_endpoint(self) -> None:
        response = self.client.get("/v1/system/status", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["metrics"]["temperature_c"], 50.0)
        self.assertTrue(response.json()["components"]["whisper"])

    def test_temperature_settings_do_not_misroute_to_weather(self) -> None:
        response = self.client.post(
            "/v1/test/chat",
            headers=self.headers,
            json={"text": "How can we tweak your temperature settings?"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["route"], "auto")
        self.assertIn("temperature settings", main.services.last_transcript)

    def test_multi_intent_composes_tools_and_model_answer(self) -> None:
        response = self.client.post(
            "/v1/test/chat",
            headers=self.headers,
            json={
                "text": "What is the weather in Cape Town? What is the current time? Explain nuclear power."
            },
        )
        payload = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(payload["route"].startswith("multi:"))
        self.assertIn("weather:open-meteo", payload["route_components"])
        self.assertIn("time:system-clock", payload["route_components"])
        self.assertIn("Hello. I am ready.", payload["text"])

    def test_explicit_memory_persists_and_lists(self) -> None:
        remembered = self.client.post(
            "/v1/test/chat",
            headers=self.headers,
            json={"text": "Remember that my preferred unit is Celsius."},
        )
        self.assertEqual(remembered.json()["route"], "memory:remember")
        listed = self.client.post(
            "/v1/test/chat",
            headers=self.headers,
            json={"text": "What do you remember?"},
        )
        self.assertIn("preferred unit is Celsius", listed.json()["text"])

    def test_capability_question_uses_registry_not_model_guess(self) -> None:
        response = self.client.post(
            "/v1/test/chat",
            headers=self.headers,
            json={"text": "What offline tools can you access right now?"},
        )
        self.assertEqual(response.json()["route"], "system:capabilities")
        self.assertIn("system.status.readonly", response.json()["text"])


if __name__ == "__main__":
    unittest.main()
