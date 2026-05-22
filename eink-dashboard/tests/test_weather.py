import pytest
import respx
import httpx

from app.weather import fetch_weather, WeatherData

NOAA_RESPONSE = {
    "properties": {
        "periods": [
            {
                "name": "Today",
                "temperature": 91,
                "shortForecast": "Sunny",
                "detailedForecast": "Sunny. High near 91. Southwest wind around 5 mph.",
                "probabilityOfPrecipitation": {"value": 3},
            }
        ]
    }
}


@respx.mock
async def test_fetch_weather_success():
    respx.get("https://api.weather.gov/gridpoints/PSR/166,61/forecast").mock(
        return_value=httpx.Response(200, json=NOAA_RESPONSE)
    )
    result = await fetch_weather("PSR/166,61")
    assert isinstance(result, WeatherData)
    assert result.temperature == 91
    assert result.short_forecast == "Sunny"
    assert result.precip_percent == 3
    assert result.period_name == "Today"


@respx.mock
async def test_fetch_weather_null_precip():
    payload = {
        "properties": {
            "periods": [
                {
                    "name": "Tonight",
                    "temperature": 72,
                    "shortForecast": "Clear",
                    "detailedForecast": "Clear.",
                    "probabilityOfPrecipitation": {"value": None},
                }
            ]
        }
    }
    respx.get("https://api.weather.gov/gridpoints/PSR/166,61/forecast").mock(
        return_value=httpx.Response(200, json=payload)
    )
    result = await fetch_weather("PSR/166,61")
    assert result.precip_percent == 0


@respx.mock
async def test_fetch_weather_http_error():
    respx.get("https://api.weather.gov/gridpoints/PSR/166,61/forecast").mock(
        return_value=httpx.Response(503)
    )
    with pytest.raises(httpx.HTTPStatusError):
        await fetch_weather("PSR/166,61")
