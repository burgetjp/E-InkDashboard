from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Literal, Optional

import httpx

WeatherSource = Literal["primary", "fallback", "cached"]


@dataclass
class WeatherData:
    period_name: str
    temperature: int
    short_forecast: str
    detailed_forecast: str
    precip_percent: int
    source: WeatherSource = "primary"


_google_api = os.environ.get("GOOGLE_API", "")
_GOOGLE_WEATHER_URL: str = f"{_google_api}&unitsSystem=IMPERIAL" if _google_api else ""
_last_good_weather: Optional[WeatherData] = None


async def fetch_weather(grid: str) -> WeatherData:
    url = f"https://api.weather.gov/gridpoints/{grid}/forecast"
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(url, headers={"User-Agent": "InkyDashboard/1.0"})
        resp.raise_for_status()
        period = resp.json()["properties"]["periods"][0]
    return WeatherData(
        period_name=period["name"],
        temperature=period["temperature"],
        short_forecast=period["shortForecast"],
        detailed_forecast=period["detailedForecast"],
        precip_percent=period.get("probabilityOfPrecipitation", {}).get("value") or 0,
    )
