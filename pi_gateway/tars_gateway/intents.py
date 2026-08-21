from __future__ import annotations

from dataclasses import dataclass
import re

from .system_status import system_status_requested
from .weather import current_weather_place


TIME_QUERY = re.compile(
    r"\b(current time|local time|time now|what(?:'s| is) the time|tell me the time|"
    r"check the time|time in south africa|time for south africa)\b",
    re.IGNORECASE,
)
IDENTITY_QUERY = re.compile(
    r"\b(who are you|what(?:'s| is) your name|tell me your name|"
    r"identify yourself|what do you do|tell me about yourself)\b",
    re.IGNORECASE,
)
CAPABILITY_QUERY = re.compile(
    r"\b(what can you do|your capabilities|tools (?:do you|can you) (?:use|access)|"
    r"what (?:offline )?(?:tools|sensors|apis) can you access|"
    r"how are you storing (?:your )?(?:memory|chat history)|"
    r"are you able to (?:do|set) (?:reminders?|timers?|alarms?)|"
    r"can you run a self-diagnostic|loaded weights|"
    r"how much (?:ram|vram) are you using)\b",
    re.IGNORECASE,
)
NETWORK_QUERY = re.compile(
    r"\b(network|internet|dns|lan)\b.*\b(status|health|check|working|available|reachable|latency|connection|connectivity)\b|"
    r"\b(status|health|check)\b.*\b(network|internet|dns|lan)\b",
    re.IGNORECASE,
)
REPEAT_POINT = re.compile(r"\b(?:repeat|restate|say again|generate)\s+(?:point|item|number)\s+(\d+)\b", re.IGNORECASE)
REMEMBER = re.compile(r"^\s*remember\s+(?:that\s+)?(.+?)\s*[.?!]*$", re.IGNORECASE)
FORGET = re.compile(r"^\s*forget\s+(?:that\s+)?(.+?)\s*[.?!]*$", re.IGNORECASE)
SHOW_MEMORY = re.compile(
    r"\b(what do you remember|show (?:me )?(?:your )?memories|list (?:your )?memories|"
    r"what have you remembered)\b",
    re.IGNORECASE,
)
STATUS_CONTINUATION = re.compile(
    r"\b(?:its|the)?\s*(?:memory|ram|disk|storage|load|uptime|fan|temperature|cpu|usage)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class ToolIntent:
    kind: str
    text: str
    argument: str | int | None = None


@dataclass(frozen=True)
class IntentPlan:
    tools: tuple[ToolIntent, ...]
    residual: str


def split_clauses(text: str) -> list[str]:
    sentences = [part.strip() for part in re.findall(r"[^?.!]+[?.!]?", text) if part.strip()]
    clauses: list[str] = []
    for sentence in sentences:
        pieces = re.split(
            r"\s+(?:and|also)\s+(?=(?:what|when|where|how|tell|give|show|check|provide|do we)\b)",
            sentence,
            flags=re.IGNORECASE,
        )
        clauses.extend(piece.strip() for piece in pieces if piece.strip())
    return clauses or [text.strip()]


def classify_clause(clause: str) -> ToolIntent | None:
    if IDENTITY_QUERY.search(clause):
        return ToolIntent("system.identity", clause)
    match = REMEMBER.match(clause)
    if match:
        return ToolIntent("memory.remember", clause, match.group(1).strip(" .?!"))
    match = FORGET.match(clause)
    if match:
        return ToolIntent("memory.forget", clause, match.group(1).strip(" .?!"))
    if SHOW_MEMORY.search(clause):
        return ToolIntent("memory.list", clause)
    match = REPEAT_POINT.search(clause)
    if match:
        return ToolIntent("conversation.repeat-item", clause, int(match.group(1)))
    if CAPABILITY_QUERY.search(clause):
        return ToolIntent("system.capabilities", clause)
    if NETWORK_QUERY.search(clause):
        return ToolIntent("system.network.readonly", clause)
    if system_status_requested(clause):
        return ToolIntent("system.status.readonly", clause)
    if TIME_QUERY.search(clause):
        return ToolIntent("time.system-clock", clause)
    is_weather, place = current_weather_place(clause)
    if is_weather:
        return ToolIntent("weather.current", clause, place)
    return None


def plan_intents(text: str) -> IntentPlan:
    tools = []
    residual = []
    for clause in split_clauses(text):
        intent = classify_clause(clause)
        if intent:
            if intent.kind != "system.identity" or not any(
                item.kind == "system.identity" for item in tools
            ):
                tools.append(intent)
        elif (
            tools
            and tools[-1].kind == "system.status.readonly"
            and STATUS_CONTINUATION.search(clause)
        ):
            previous = tools[-1]
            tools[-1] = ToolIntent(previous.kind, f"{previous.text} {clause}")
        else:
            residual.append(clause)
    return IntentPlan(tuple(tools), " ".join(residual).strip())
