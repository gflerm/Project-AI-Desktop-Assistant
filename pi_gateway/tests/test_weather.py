from __future__ import annotations

import asyncio
import unittest

import httpx

from tars_gateway.weather import WeatherClient, current_weather_place
from tars_gateway.services import needs_live_grounding


class WeatherTests(unittest.TestCase):
    def test_current_query_extracts_place(self) -> None:
        matched, place = current_weather_place("What is the weather in Cape Town right now?")
        self.assertTrue(matched)
        self.assertEqual(place, "Cape Town")

    def test_future_forecast_stays_with_grounded_llm(self) -> None:
        self.assertEqual(current_weather_place("Weather forecast for tomorrow"), (False, None))

    def test_code_and_settings_requests_do_not_trigger_weather_tool(self) -> None:
        self.assertEqual(
            current_weather_place("Write a Python script for current weather conditions"),
            (False, None),
        )
        self.assertEqual(
            current_weather_place("How can we tweak your temperature settings?"),
            (False, None),
        )

    def test_live_grounding_intent(self) -> None:
        self.assertTrue(needs_live_grounding("Who is the current president of South Africa?"))
        self.assertTrue(needs_live_grounding("Give me the latest project news"))
        self.assertFalse(needs_live_grounding("Explain Ohm's law"))

    def test_geocode_and_current_conditions(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            if "geocoding-api" in request.url.host:
                return httpx.Response(
                    200,
                    json={"results": [{
                        "name": "Cape Town", "admin1": "Western Cape",
                        "country": "South Africa", "latitude": -33.925,
                        "longitude": 18.424,
                    }]},
                )
            return httpx.Response(
                200,
                json={"current": {
                    "temperature_2m": 21.2, "apparent_temperature": 20.7,
                    "weather_code": 1, "wind_speed_10m": 14.0,
                }},
            )

        client = WeatherClient(
            -33.9249, 18.4241, "Cape Town", transport=httpx.MockTransport(handler)
        )
        result = asyncio.run(client.current("Cape Town"))
        self.assertIn("mainly clear", result.describe())
        self.assertIn("14 kilometres", result.describe())
        asyncio.run(client.close())


if __name__ == "__main__":
    unittest.main()
