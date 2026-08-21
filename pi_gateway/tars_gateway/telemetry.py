from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import threading
from typing import Any


class TelemetryRecorder:
    def __init__(
        self,
        path: str,
        enabled: bool = True,
        include_text: bool = False,
        max_bytes: int = 10 * 1024 * 1024,
        backups: int = 3,
    ):
        self.path = Path(path)
        self.enabled = enabled
        self.include_text = include_text
        self.max_bytes = max(max_bytes, 64 * 1024)
        self.backups = max(backups, 1)
        self._lock = threading.Lock()

    def _rotate(self) -> None:
        if not self.path.exists() or self.path.stat().st_size < self.max_bytes:
            return
        oldest = self.path.with_suffix(self.path.suffix + f".{self.backups}")
        if oldest.exists():
            oldest.unlink()
        for number in range(self.backups - 1, 0, -1):
            source = self.path.with_suffix(self.path.suffix + f".{number}")
            if source.exists():
                source.replace(self.path.with_suffix(self.path.suffix + f".{number + 1}"))
        self.path.replace(self.path.with_suffix(self.path.suffix + ".1"))

    def record(self, event: str, **fields: Any) -> None:
        if not self.enabled:
            return
        payload = {
            "schema": 1,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
            "event": event,
            **{key: value for key, value in fields.items() if value is not None},
        }
        if not self.include_text:
            payload.pop("transcript", None)
            payload.pop("response_text", None)
        encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n"
        with self._lock:
            try:
                self.path.parent.mkdir(parents=True, exist_ok=True)
                self._rotate()
                with self.path.open("a", encoding="utf-8") as stream:
                    stream.write(encoded)
            except OSError:
                return

    def _records(self) -> list[dict[str, Any]]:
        paths = [
            self.path.with_suffix(self.path.suffix + f".{number}")
            for number in range(self.backups, 0, -1)
        ] + [self.path]
        records: list[dict[str, Any]] = []
        with self._lock:
            for path in paths:
                if not path.is_file():
                    continue
                try:
                    for line in path.read_text(encoding="utf-8").splitlines():
                        try:
                            records.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue
                except OSError:
                    continue
        return records

    @staticmethod
    def _distribution(values: list[float]) -> dict[str, float | int]:
        ordered = sorted(values)
        if not ordered:
            return {"count": 0}
        percentile = lambda fraction: ordered[max(0, math.ceil(len(ordered) * fraction) - 1)]
        return {
            "count": len(ordered),
            "min": round(ordered[0], 1),
            "average": round(sum(ordered) / len(ordered), 1),
            "p50": round(percentile(0.50), 1),
            "p95": round(percentile(0.95), 1),
            "max": round(ordered[-1], 1),
        }

    def summary(self) -> dict[str, Any]:
        records = self._records()
        timing_values: dict[str, list[float]] = {}
        events = Counter()
        routes = Counter()
        providers = Counter()
        grounding_sources = Counter()
        errors = 0
        fallbacks = 0
        grounded = 0
        for record in records:
            events[str(record.get("event", "unknown"))] += 1
            if record.get("route"):
                routes[str(record["route"])] += 1
            if record.get("provider"):
                providers[str(record["provider"])] += 1
            if record.get("grounding_source"):
                grounding_sources[str(record["grounding_source"])] += 1
            errors += int(record.get("status") == "error")
            fallbacks += int(bool(record.get("fallback_used")))
            grounded += int(bool(record.get("google_search_used")))
            for key, value in record.items():
                if key.endswith("_ms") and isinstance(value, (int, float)):
                    timing_values.setdefault(key, []).append(float(value))
        return {
            "enabled": self.enabled,
            "include_text": self.include_text,
            "path": str(self.path),
            "total_events": len(records),
            "first_timestamp_utc": records[0].get("timestamp_utc") if records else None,
            "last_timestamp_utc": records[-1].get("timestamp_utc") if records else None,
            "event_counts": dict(events),
            "routes": dict(routes),
            "providers": dict(providers),
            "grounding_sources": dict(grounding_sources),
            "fallback_count": fallbacks,
            "google_search_count": grounded,
            "error_count": errors,
            "timing_ms": {
                key: self._distribution(values) for key, values in sorted(timing_values.items())
            },
        }
