from __future__ import annotations

from dataclasses import dataclass
import re

import httpx


WEB_QUERY_PATTERN = re.compile(
    r"\b(search|look up|find online|on the internet|on the web|latest|current|"
    r"today|tonight|news|price|score|schedule|who is|what happened)\b",
    re.IGNORECASE,
)


def needs_web_research(text: str) -> bool:
    return bool(WEB_QUERY_PATTERN.search(text))


@dataclass(frozen=True)
class WebSearchResult:
    title: str
    url: str
    snippet: str
    engine: str


class SearXNGClient:
    def __init__(self, base_url: str, timeout: float = 12.0):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(timeout=timeout)

    async def close(self) -> None:
        await self.client.aclose()

    async def search(self, query: str, limit: int = 5) -> list[WebSearchResult]:
        response = await self.client.get(
            f"{self.base_url}/search",
            params={
                "q": query,
                "format": "json",
                "language": "en",
                "safesearch": 1,
                "categories": "general",
            },
        )
        response.raise_for_status()
        results = []
        for item in response.json().get("results", []):
            title = str(item.get("title", "")).strip()
            url = str(item.get("url", "")).strip()
            snippet = re.sub(r"\s+", " ", str(item.get("content", ""))).strip()
            if title and url and snippet:
                results.append(
                    WebSearchResult(title, url, snippet[:700], str(item.get("engine", "")))
                )
            if len(results) >= limit:
                break
        return results

    @staticmethod
    def grounding_context(results: list[WebSearchResult]) -> str:
        lines = ["Fresh local metasearch results:"]
        for number, result in enumerate(results, 1):
            lines.append(f"{number}. {result.title}\nURL: {result.url}\nSnippet: {result.snippet}")
        return "\n\n".join(lines)
