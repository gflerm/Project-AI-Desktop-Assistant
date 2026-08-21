from __future__ import annotations

import json
from pathlib import Path
import re


class SpeechAdaptation:
    def __init__(self, path: str):
        self.path = Path(path)
        self.hints = "James, Project TARS, ESP32-P4, Raspberry Pi 5, FreeRTOS, Ollama, Gemini"
        self.phrases: dict[str, str] = {}
        self.words: dict[str, str] = {}
        try:
            saved = json.loads(self.path.read_text(encoding="utf-8"))
            self.hints = str(saved.get("hints", self.hints))[:1000]
            self.phrases = {str(k): str(v) for k, v in saved.get("phrases", {}).items()}
            self.words = {str(k): str(v) for k, v in saved.get("words", {}).items()}
        except (OSError, TypeError, ValueError, json.JSONDecodeError):
            pass

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(
                {"hints": self.hints, "phrases": self.phrases, "words": self.words},
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

    def prompt(self) -> str:
        learned = ", ".join(dict.fromkeys(self.words.values()))
        return ". ".join(part for part in (self.hints.strip(), learned) if part)[:1200]

    def apply(self, transcript: str) -> str:
        exact = self.phrases.get(transcript.casefold())
        if exact:
            return exact
        corrected = transcript
        for heard, intended in sorted(self.words.items(), key=lambda item: -len(item[0])):
            corrected = re.sub(rf"\b{re.escape(heard)}\b", intended, corrected, flags=re.IGNORECASE)
        return corrected

    def teach(self, observed: str, corrected: str) -> None:
        observed, corrected = observed.strip(), corrected.strip()
        if not observed or not corrected:
            raise ValueError("Both observed and corrected transcripts are required")
        self.phrases[observed.casefold()] = corrected
        observed_words = re.findall(r"[\w'-]+", observed)
        corrected_words = re.findall(r"[\w'-]+", corrected)
        if len(observed_words) == len(corrected_words):
            for heard, intended in zip(observed_words, corrected_words):
                if heard.casefold() != intended.casefold():
                    self.words[heard.casefold()] = intended
        self._save()

    def set_hints(self, hints: str) -> None:
        self.hints = hints.strip()[:1000]
        self._save()

    def status(self) -> dict[str, object]:
        return {
            "hints": self.hints,
            "phrase_corrections": len(self.phrases),
            "word_corrections": len(self.words),
            "learned_words": sorted(set(self.words.values())),
        }
