from __future__ import annotations

from typing import Any


def capability_snapshot(settings, components: dict[str, bool], memory_status: dict[str, Any], inference: dict[str, Any]) -> dict[str, Any]:
    tools = [
        {"id": "time.system-clock", "mode": "read-only", "available": True},
        {"id": "weather.current", "mode": "read-only internet", "available": True},
        {"id": "system.status.readonly", "mode": "read-only", "available": True},
        {"id": "system.network.readonly", "mode": "read-only", "available": True},
        {"id": "memory.explicit", "mode": "operator-controlled local storage", "available": True},
        {"id": "ollama.local_lessons", "mode": "private local retrieval", "available": True},
        {
            "id": "google_search",
            "mode": "cloud grounding",
            "available": bool(settings.gemini_google_search and settings.gemini_api_key),
        },
        {"id": "wikipedia.factual_fallback", "mode": "read-only internet", "available": True},
    ]
    return {
        "tools": tools,
        "components": dict(components),
        "memory": memory_status,
        "inference": inference,
        "providers": {
            "automatic": settings.llm_provider == "auto",
            "gemini_configured": bool(settings.gemini_api_key),
            "gemini_model": settings.gemini_model if settings.gemini_api_key else None,
            "ollama_model": settings.ollama_model,
        },
    }


def describe_capabilities(snapshot: dict[str, Any], query: str = "") -> str:
    lower = query.casefold()
    if "remind" in lower or "timer" in lower or "alarm" in lower:
        return "Timers, alarms and reminder notifications are not implemented yet. I will not claim one was set until a permissioned scheduler confirms it."
    if "memory" in lower or "history" in lower or "reboot" in lower:
        count = snapshot["memory"]["active_count"]
        return f"I keep short conversation context in memory and {count} explicit operator-approved persistent memories in a private Pi-local file. Persistent memory is changed only by remember or forget commands."
    if "diagnostic" in lower or "weights" in lower or "configuration" in lower:
        return "I can read the Pi's health, services, local-model queue and bounded network status. I cannot inspect neural weights for corruption or modify configuration through the conversational tool."
    available = [item["id"] for item in snapshot["tools"] if item.get("available")]
    provider = snapshot["providers"]
    return (
        "I can read the South African system clock, current weather, Raspberry Pi health, "
        "and bounded network health; keep explicit private memories; use local Ollama; and "
        + ("escalate suitable current or complex questions to Gemini. " if provider["gemini_configured"] else "operate without a configured cloud model. ")
        + "Enabled tools are: " + ", ".join(available) + "."
    )
