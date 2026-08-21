from __future__ import annotations

from dataclasses import dataclass
import os

from .personality import personality_prompt_from_environment


@dataclass(frozen=True)
class Settings:
    token: str
    whisper_url: str
    piper_url: str
    ollama_url: str
    ollama_model: str
    ollama_think: bool
    llm_provider: str
    llm_fallback_to_ollama: bool
    gemini_url: str
    gemini_model: str
    gemini_api_key: str
    gemini_google_search: bool
    weather_latitude: float
    weather_longitude: float
    weather_place: str
    tts_length_scale: float
    tts_noise_scale: float
    tts_noise_w_scale: float
    telemetry_enabled: bool
    telemetry_include_text: bool
    telemetry_path: str
    telemetry_max_bytes: int
    personality_path: str
    speech_adaptation_path: str
    local_learning_path: str
    persistent_memory_path: str
    searxng_url: str
    personality: str
    max_utterance_bytes: int
    session_max_turns: int
    session_idle_seconds: float

    @classmethod
    def from_environment(cls) -> "Settings":
        token = os.getenv("JAMES_TOKEN", "").strip()
        if len(token) < 24:
            raise RuntimeError("JAMES_TOKEN must contain at least 24 characters")
        provider = os.getenv("JAMES_LLM_PROVIDER", "auto").strip().lower()
        if provider not in {"auto", "gemini", "ollama"}:
            raise RuntimeError("JAMES_LLM_PROVIDER must be auto, gemini, or ollama")
        return cls(
            token=token,
            whisper_url=os.getenv("JAMES_WHISPER_URL", "http://127.0.0.1:8080").rstrip("/"),
            piper_url=os.getenv("JAMES_PIPER_URL", "http://127.0.0.1:5000").rstrip("/"),
            ollama_url=os.getenv("JAMES_OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/"),
            ollama_model=os.getenv("JAMES_OLLAMA_MODEL", "qwen3:1.7b").strip(),
            ollama_think=os.getenv("JAMES_OLLAMA_THINK", "false").strip().lower()
            in {"1", "true", "yes", "on"},
            llm_provider=provider,
            llm_fallback_to_ollama=os.getenv(
                "JAMES_LLM_FALLBACK_TO_OLLAMA", "true"
            ).strip().lower()
            in {"1", "true", "yes", "on"},
            gemini_url=os.getenv(
                "JAMES_GEMINI_URL", "https://generativelanguage.googleapis.com/v1beta"
            ).rstrip("/"),
            gemini_model=os.getenv(
                "JAMES_GEMINI_MODEL", "gemini-3.5-flash-lite"
            ).strip(),
            gemini_api_key=os.getenv("GEMINI_API_KEY", "").strip(),
            gemini_google_search=os.getenv(
                "JAMES_GEMINI_GOOGLE_SEARCH", "true"
            ).strip().lower()
            in {"1", "true", "yes", "on"},
            weather_latitude=float(os.getenv("JAMES_WEATHER_LAT", "-33.9249")),
            weather_longitude=float(os.getenv("JAMES_WEATHER_LON", "18.4241")),
            weather_place=os.getenv(
                "JAMES_WEATHER_PLACE", "Cape Town, Western Cape, South Africa"
            ).strip(),
            tts_length_scale=float(os.getenv("JAMES_TTS_LENGTH_SCALE", "0.94")),
            tts_noise_scale=float(os.getenv("JAMES_TTS_NOISE_SCALE", "0.76")),
            tts_noise_w_scale=float(os.getenv("JAMES_TTS_NOISE_W_SCALE", "0.90")),
            telemetry_enabled=os.getenv("JAMES_TELEMETRY_ENABLED", "true").strip().lower()
            in {"1", "true", "yes", "on"},
            telemetry_include_text=os.getenv(
                "JAMES_TELEMETRY_INCLUDE_TEXT", "false"
            ).strip().lower()
            in {"1", "true", "yes", "on"},
            telemetry_path=os.getenv(
                "JAMES_TELEMETRY_PATH", "/var/lib/james/telemetry.jsonl"
            ).strip(),
            telemetry_max_bytes=max(
                int(os.getenv("JAMES_TELEMETRY_MAX_BYTES", "10485760")), 65536
            ),
            personality_path=os.getenv(
                "JAMES_PERSONALITY_PATH", "/var/lib/james/personality.json"
            ).strip(),
            speech_adaptation_path=os.getenv(
                "JAMES_SPEECH_ADAPTATION_PATH", "/var/lib/james/speech-adaptation.json"
            ).strip(),
            local_learning_path=os.getenv(
                "JAMES_LOCAL_LEARNING_PATH", "/var/lib/james/local-lessons.json"
            ).strip(),
            persistent_memory_path=os.getenv(
                "JAMES_PERSISTENT_MEMORY_PATH", "/var/lib/james/persistent-memory.json"
            ).strip(),
            searxng_url=os.getenv(
                "JAMES_SEARXNG_URL", "http://127.0.0.1:8888"
            ).rstrip("/"),
            personality=os.getenv(
                "JAMES_PERSONALITY",
                personality_prompt_from_environment(),
            ).strip(),
            max_utterance_bytes=max(
                int(os.getenv("JAMES_MAX_UTTERANCE_BYTES", "1048576")), 3200
            ),
            session_max_turns=max(int(os.getenv("JAMES_SESSION_MAX_TURNS", "3")), 1),
            session_idle_seconds=max(
                float(os.getenv("JAMES_SESSION_IDLE_SECONDS", "1800")), 0.0
            ),
        )
