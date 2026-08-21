from __future__ import annotations

from dataclasses import dataclass
import re

import httpx


WMO_CODES = {
    0: "clear", 1: "mainly clear", 2: "partly cloudy", 3: "overcast",
    45: "foggy", 48: "icy fog", 51: "light drizzle", 53: "drizzle",
    55: "heavy drizzle", 61: "light rain", 63: "rain", 65: "heavy rain",
    71: "light snow", 73: "snow", 75: "heavy snow", 80: "light showers",
    81: "showers", 82: "heavy showers", 95: "thunderstorm",
    96: "thunderstorm with hail", 99: "thunderstorm with hail",
}
WEATHER_WORDS = re.compile(
    r"\b(weather|temperature|raining|rain|sunny|cloudy|hot|cold|outside)\b",
    re.IGNORECASE,
)
FUTURE_WORDS = re.compile(r"\b(tomorrow|next week|forecast|later this week)\b", re.IGNORECASE)
NON_LOOKUP_WORDS = re.compile(
    r"\b(script|code|program|function|write|generate|settings?|parameter|sampling|"
    r"model temperature|creativity|tweak|configure)\b",
    re.IGNORECASE,
)
LOOKUP_CONTEXT = re.compile(
    r"\b(current|currently|right now|now|today|conditions?|what(?:'s| is)|how(?:'s| is)|"
    r"check|tell|give|show|weather in|weather for|temperature in|temperature for)\b",
    re.IGNORECASE,
)


class WeatherUnavailable(Exception):
    pass


@dataclass(frozen=True)
class CurrentWeather:
    place: str
    temperature_c: float
    apparent_c: float
    wind_kmh: float
    condition: str

    def describe(self) -> str:
        text = f"It is {self.condition} in {self.place}, around {self.temperature_c:.0f} degrees Celsius"
        if abs(self.apparent_c - self.temperature_c) >= 2:
            text += f", feeling like {self.apparent_c:.0f}"
        if self.wind_kmh >= 10:
            text += f", with wind around {self.wind_kmh:.0f} kilometres per hour"
        return text + "."


def current_weather_place(text: str) -> tuple[bool, str | None]:
    """Return whether this is a current-weather query and its optional place."""
    if (
        not WEATHER_WORDS.search(text)
        or FUTURE_WORDS.search(text)
        or NON_LOOKUP_WORDS.search(text)
        or not LOOKUP_CONTEXT.search(text)
    ):
        return False, None
    match = re.search(r"\b(?:in|for|at)\s+([a-z][a-z' ,.-]+)", text, re.IGNORECASE)
    if not match:
        return True, None
    place = re.sub(
        r"\b(right now|currently|today|now|please)\b.*$", "", match.group(1), flags=re.IGNORECASE
    ).strip(" ,.?-")
    return True, place or None


class WeatherClient:
    def __init__(
        self,
        default_latitude: float,
        default_longitude: float,
        default_place: str,
        timeout: float = 10.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ):
        self.default_latitude = default_latitude
        self.default_longitude = default_longitude
        self.default_place = default_place
        self.timeout = timeout
        self.transport = transport
        self.client = httpx.AsyncClient(timeout=timeout, transport=transport)

    async def close(self) -> None:
        await self.client.aclose()

    async def _location(self, place: str | None) -> tuple[float, float, str]:
        if not place:
            return self.default_latitude, self.default_longitude, self.default_place
        response = await self.client.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": place, "count": 1, "language": "en", "format": "json"},
        )
        response.raise_for_status()
        results = response.json().get("results") or []
        if not results:
            raise WeatherUnavailable(f"I could not find a weather location named {place}.")
        result = results[0]
        label = ", ".join(
            str(value) for value in (result.get("name"), result.get("admin1"), result.get("country")) if value
        )
        return float(result["latitude"]), float(result["longitude"]), label

    async def current(self, place: str | None = None) -> CurrentWeather:
        latitude, longitude, label = await self._location(place)
        response = await self.client.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": latitude,
                "longitude": longitude,
                "current": "temperature_2m,apparent_temperature,weather_code,wind_speed_10m",
                "timezone": "auto",
            },
        )
        response.raise_for_status()
        current = response.json().get("current") or {}
        try:
            code = int(current["weather_code"])
            return CurrentWeather(
                place=label,
                temperature_c=float(current["temperature_2m"]),
                apparent_c=float(current["apparent_temperature"]),
                wind_kmh=float(current["wind_speed_10m"]),
                condition=WMO_CODES.get(code, "unclassified conditions"),
            )
        except (KeyError, TypeError, ValueError) as error:
            raise WeatherUnavailable("The weather service returned an unreadable result.") from error
