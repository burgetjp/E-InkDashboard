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


_GOOGLE_WEATHER_URL: str = (
    f"{os.environ.get('GOOGLE_API', '')}&unitsSystem=IMPERIAL"
    if os.environ.get("GOOGLE_API")
    else ""
)
_last_good_weather: Optional[WeatherData] = None


async def fetch_weather(grid: str) -> WeatherData:
    global _last_good_weather

    # Tier 1: NOAA
    try:
        url = f"https://api.weather.gov/gridpoints/{grid}/forecast"
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url, headers={"User-Agent": "InkyDashboard/1.0"})
            resp.raise_for_status()
            period = resp.json()["properties"]["periods"][0]
        result = WeatherData(
            period_name=period["name"],
            temperature=period["temperature"],
            short_forecast=period["shortForecast"],
            detailed_forecast=period["detailedForecast"],
            precip_percent=period.get("probabilityOfPrecipitation", {}).get("value") or 0,
            source="primary",
        )
        _last_good_weather = result
        return result
    except Exception:
        pass

    # Tier 2: Google Weather
    last_exc: Optional[Exception] = None
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(_GOOGLE_WEATHER_URL)
            resp.raise_for_status()
            data = resp.json()
        desc = data["weatherCondition"]["description"]["text"]
        temp = round(data["currentConditionsHistory"]["maxTemperature"]["degrees"])
        wind = data["wind"]["speed"]["value"]
        result = WeatherData(
            period_name="Tonight" if not data["isDaytime"] else "Today",
            temperature=temp,
            short_forecast=desc,
            detailed_forecast=f"{desc}. High near {temp}°F. Wind {wind} mph.",
            precip_percent=data["precipitation"]["probability"]["percent"],
            source="fallback",
        )
        _last_good_weather = result
        return result
    except Exception as exc:
        last_exc = exc

    # Tier 3: module cache
    if _last_good_weather is not None:
        return WeatherData(
            period_name=_last_good_weather.period_name,
            temperature=_last_good_weather.temperature,
            short_forecast=_last_good_weather.short_forecast,
            detailed_forecast=_last_good_weather.detailed_forecast,
            precip_percent=_last_good_weather.precip_percent,
            source="cached",
        )

    raise last_exc  # type: ignore[misc]
