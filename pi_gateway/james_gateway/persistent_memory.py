from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import re
import threading
import uuid


def _terms(text: str) -> set[str]:
    return {
        word for word in re.findall(r"[a-z0-9][a-z0-9_-]+", text.casefold()) if len(word) > 2
    }


class PersistentMemory:
    """Explicit, private facts with soft deletion and local-only retrieval."""

    def __init__(self, path: str, maximum_entries: int = 200):
        self.path = Path(path)
        self.maximum_entries = maximum_entries
        self._lock = threading.Lock()
        self.entries: list[dict[str, object]] = []
        try:
            loaded = json.loads(self.path.read_text(encoding="utf-8"))
            if isinstance(loaded, list):
                self.entries = [item for item in loaded if isinstance(item, dict)][-maximum_entries:]
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            pass

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".json.tmp")
        temporary.write_text(json.dumps(self.entries, indent=2) + "\n", encoding="utf-8")
        temporary.replace(self.path)

    def remember(self, fact: str, *, cloud_allowed: bool = False) -> dict[str, object]:
        fact = fact.strip()
        if not fact:
            raise ValueError("A fact is required")
        if len(fact) > 1000:
            raise ValueError("A remembered fact may not exceed 1000 characters")
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        with self._lock:
            for entry in self.entries:
                if not entry.get("deleted_at_utc") and str(entry.get("fact", "")).casefold() == fact.casefold():
                    return dict(entry)
            entry: dict[str, object] = {
                "id": str(uuid.uuid4()),
                "fact": fact,
                "created_at_utc": now,
                "deleted_at_utc": None,
                "cloud_allowed": bool(cloud_allowed),
            }
            self.entries.append(entry)
            self.entries = self.entries[-self.maximum_entries :]
            self._save()
            return dict(entry)

    def active(self) -> list[dict[str, object]]:
        with self._lock:
            return [dict(entry) for entry in self.entries if not entry.get("deleted_at_utc")]

    def forget(self, query: str) -> list[dict[str, object]]:
        query = query.strip()
        if not query:
            raise ValueError("Name the fact to forget")
        if query.casefold() in {"everything", "all", "all memories"}:
            raise ValueError("Bulk deletion requires the dedicated settings interface")
        wanted = _terms(query)
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        changed = []
        with self._lock:
            for entry in self.entries:
                if entry.get("deleted_at_utc"):
                    continue
                fact = str(entry.get("fact", ""))
                if query.casefold() in fact.casefold() or (wanted and wanted <= _terms(fact)):
                    entry["deleted_at_utc"] = now
                    changed.append(dict(entry))
            if changed:
                self._save()
        return changed

    def relevant_context(self, query: str, *, for_cloud: bool = False, limit: int = 4) -> str:
        query_terms = _terms(query)
        ranked = []
        for index, entry in enumerate(self.active()):
            if for_cloud and not entry.get("cloud_allowed"):
                continue
            overlap = len(query_terms & _terms(str(entry.get("fact", ""))))
            if overlap:
                ranked.append((overlap, index, entry))
        ranked.sort(key=lambda item: (item[0], item[1]), reverse=True)
        selected = [item[2] for item in ranked[:limit]]
        if not selected:
            return ""
        return "PRIVATE OPERATOR-APPROVED MEMORY:\n" + "\n".join(
            f"- {entry['fact']}" for entry in selected
        )

    def status(self) -> dict[str, object]:
        return {
            "active_count": len(self.active()),
            "maximum_entries": self.maximum_entries,
            "storage": "private Pi-local JSON",
            "deletion": "soft-delete; bulk deletion requires settings interface",
            "cloud_sharing_default": False,
        }
