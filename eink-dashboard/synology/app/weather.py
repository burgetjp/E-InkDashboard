from dataclasses import dataclass

import httpx


@dataclass
class WeatherData:
    period_name: str
    temperature: int
    short_forecast: str
    detailed_forecast: str
    precip_percent: int


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
