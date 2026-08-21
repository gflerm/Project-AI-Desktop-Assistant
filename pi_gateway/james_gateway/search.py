from __future__ import annotations

from dataclasses import dataclass
import re

import httpx


@dataclass(frozen=True)
class SearchResult:
    title: str
    extract: str
    url: str

    def grounding_context(self) -> str:
        return f"Source: {self.title}\nURL: {self.url}\nRetrieved text:\n{self.extract}"

    def spoken_summary(self) -> str:
        """Return a bounded factual fallback without another slow LLM pass."""
        sentences = re.split(r"(?<=[.!?])\s+", self.extract.strip())
        priority = next(
            (
                index
                for index, sentence in enumerate(sentences)
                if re.search(r"\b(current|currently|incumbent)\b", sentence, re.IGNORECASE)
            ),
            0,
        )
        summary = " ".join(sentences[priority : priority + 2]).strip()
        if len(summary) > 600:
            summary = summary[:597].rsplit(" ", 1)[0] + "..."
        return f"Wikipedia currently reports: {summary}"


class WikipediaSearchClient:
    """Small, keyless factual fallback for when cloud search is unavailable."""

    def __init__(self, client: httpx.AsyncClient):
        self.client = client

    @staticmethod
    def focused_query(query: str) -> str:
        cleaned = re.sub(
            r"\banswer (?:in|with)\b.*$", "", query, flags=re.IGNORECASE
        ).strip(" .?!")
        leadership = re.match(
            r"who is (?:the )?current (president|prime minister) of (.+)",
            cleaned,
            flags=re.IGNORECASE,
        )
        if leadership:
            role, place = leadership.groups()
            return f"{role.title()} of {place.strip(' .?!')}"
        return cleaned

    async def search(self, query: str) -> SearchResult | None:
        query = self.focused_query(query)
        response = await self.client.get(
            "https://en.wikipedia.org/w/api.php",
            params={
                "action": "query",
                "format": "json",
                "formatversion": "2",
                "generator": "search",
                "gsrsearch": query,
                "gsrlimit": "1",
                "prop": "extracts|info",
                "exintro": "1",
                "explaintext": "1",
                "inprop": "url",
            },
            headers={"User-Agent": "Project-James/0.1 (local desktop assistant)"},
            timeout=8,
        )
        response.raise_for_status()
        pages = response.json().get("query", {}).get("pages", [])
        if not pages:
            return None
        page = pages[0]
        extract = str(page.get("extract", "")).strip()
        if not extract:
            return None
        return SearchResult(
            title=str(page.get("title", "Wikipedia")),
            extract=extract[:2400],
            url=str(page.get("fullurl", "https://en.wikipedia.org/")),
        )
