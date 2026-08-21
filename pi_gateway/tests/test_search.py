from __future__ import annotations

import asyncio
import unittest

import httpx

from james_gateway.search import SearchResult, WikipediaSearchClient


class SearchTests(unittest.TestCase):
    def test_wikipedia_result_becomes_compact_grounding_context(self) -> None:
        async def run():
            async def handler(request: httpx.Request) -> httpx.Response:
                self.assertEqual(request.url.params["gsrsearch"], "current president")
                return httpx.Response(
                    200,
                    json={
                        "query": {
                            "pages": [
                                {
                                    "title": "President of South Africa",
                                    "extract": "The incumbent is Cyril Ramaphosa.",
                                    "fullurl": "https://example.test/president",
                                }
                            ]
                        }
                    },
                )

            async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
                return await WikipediaSearchClient(client).search("current president")

        result = asyncio.run(run())
        self.assertIsNotNone(result)
        context = result.grounding_context()
        self.assertIn("Cyril Ramaphosa", context)
        self.assertIn("https://example.test/president", context)

    def test_leadership_query_is_focused_on_the_role_page(self) -> None:
        self.assertEqual(
            WikipediaSearchClient.focused_query(
                "Who is the current president of South Africa? Answer in one sentence."
            ),
            "President of South Africa",
        )

    def test_wikipedia_result_has_bounded_spoken_fallback(self) -> None:
        result = SearchResult(
            title="Example",
            extract="First factual sentence. Second factual sentence. Third sentence.",
            url="https://example.test",
        )
        self.assertEqual(
            result.spoken_summary(),
            "Wikipedia currently reports: First factual sentence. Second factual sentence.",
        )

    def test_spoken_fallback_prioritizes_current_fact(self) -> None:
        result = SearchResult(
            title="President of South Africa",
            extract=(
                "The president is head of state. The office directs the executive. "
                "The current president is Cyril Ramaphosa. He was elected by Parliament."
            ),
            url="https://example.test/president",
        )
        self.assertEqual(
            result.spoken_summary(),
            "Wikipedia currently reports: The current president is Cyril Ramaphosa. He was elected by Parliament.",
        )
