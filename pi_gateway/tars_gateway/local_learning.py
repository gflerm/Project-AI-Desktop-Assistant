from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import re


def _terms(text: str) -> set[str]:
    return {
        word
        for word in re.findall(r"[a-z0-9][a-z0-9_-]+", text.casefold())
        if len(word) > 2
    }


class LocalLearning:
    """Explicit operator-taught lessons retrieved locally for Ollama only."""

    def __init__(self, path: str, maximum_lessons: int = 500):
        self.path = Path(path)
        self.maximum_lessons = maximum_lessons
        self.lessons: list[dict[str, object]] = []
        try:
            loaded = json.loads(self.path.read_text(encoding="utf-8"))
            if isinstance(loaded, list):
                self.lessons = [item for item in loaded if isinstance(item, dict)][-maximum_lessons:]
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            pass

    def add(self, prompt: str, response: str, guidance: str) -> dict[str, object]:
        guidance = guidance.strip()
        if not guidance:
            raise ValueError("Local guidance is required")
        lesson = {
            "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "prompt": prompt.strip()[:4000],
            "bad_response": response.strip()[:4000],
            "guidance": guidance[:4000],
        }
        self.lessons = [
            existing
            for existing in self.lessons
            if not (
                existing.get("prompt") == lesson["prompt"]
                and existing.get("guidance") == lesson["guidance"]
            )
        ]
        self.lessons.append(lesson)
        self.lessons = self.lessons[-self.maximum_lessons:]
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.lessons, indent=2) + "\n", encoding="utf-8")
        return lesson

    def relevant_context(self, query: str, limit: int = 4) -> str:
        query_terms = _terms(query)
        ranked = []
        for index, lesson in enumerate(self.lessons):
            lesson_terms = _terms(str(lesson.get("prompt", "")) + " " + str(lesson.get("guidance", "")))
            overlap = len(query_terms & lesson_terms)
            if overlap:
                ranked.append((overlap, index, lesson))
        ranked.sort(key=lambda item: (item[0], item[1]), reverse=True)
        selected = [item[2] for item in ranked[:limit]]
        if not selected:
            return ""
        lines = [
            "LOCAL OPERATOR-TAUGHT LESSONS: Apply relevant guidance, but never claim an "
            "action succeeded without an implemented tool result. These lessons are private "
            "local context, not new capabilities."
        ]
        for lesson in selected:
            lines.append(
                f"- Earlier request: {lesson.get('prompt', '')}\n"
                f"  Operator guidance: {lesson.get('guidance', '')}"
            )
        return "\n".join(lines)

    def status(self) -> dict[str, object]:
        return {
            "lesson_count": len(self.lessons),
            "storage": "private Pi-local JSON",
            "used_by": "ollama only",
        }
