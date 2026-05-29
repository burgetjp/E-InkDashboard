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

GOOGLE_MOCK_URL = "https://weather.googleapis.com/v1/fake"

GOOGLE_RESPONSE = {
    "isDaytime": True,
    "weatherCondition": {
        "description": {"text": "Sunny"},
    },
    "currentConditionsHistory": {
        "maxTemperature": {"degrees": 90.3, "unit": "FAHRENHEIT"},
    },
    "precipitation": {
        "probability": {"percent": 5},
    },
    "wind": {
        "speed": {"value": 11, "unit": "MILES_PER_HOUR"},
    },
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
async def test_fetch_weather_http_error(monkeypatch):
    import app.weather as weather_module
    monkeypatch.setattr(weather_module, "_last_good_weather", None)
    monkeypatch.setattr(weather_module, "_GOOGLE_WEATHER_URL", "https://weather.googleapis.com/v1/fake")
    respx.get("https://api.weather.gov/gridpoints/PSR/166,61/forecast").mock(
        return_value=httpx.Response(503)
    )
    respx.get("https://weather.googleapis.com/v1/fake").mock(
        return_value=httpx.Response(503)
    )
    with pytest.raises(httpx.HTTPStatusError):
        await fetch_weather("PSR/166,61")


def test_weather_data_default_source_is_primary():
    w = WeatherData(
        period_name="Today",
        temperature=91,
        short_forecast="Sunny",
        detailed_forecast="Sunny. High near 91.",
        precip_percent=0,
    )
    assert w.source == "primary"


def test_weather_data_accepts_fallback_source():
    w = WeatherData(
        period_name="Today",
        temperature=91,
        short_forecast="Sunny",
        detailed_forecast="Sunny.",
        precip_percent=0,
        source="fallback",
    )
    assert w.source == "fallback"


def test_weather_data_accepts_cached_source():
    w = WeatherData(
        period_name="Today",
        temperature=91,
        short_forecast="Sunny",
        detailed_forecast="Sunny.",
        precip_percent=0,
        source="cached",
    )
    assert w.source == "cached"


@respx.mock
async def test_fetch_weather_uses_fallback_on_noaa_failure(monkeypatch):
    import app.weather as weather_module
    monkeypatch.setattr(weather_module, "_last_good_weather", None)
    monkeypatch.setattr(weather_module, "_GOOGLE_WEATHER_URL", GOOGLE_MOCK_URL)
    respx.get("https://api.weather.gov/gridpoints/PSR/166,61/forecast").mock(
        return_value=httpx.Response(503)
    )
    respx.get(GOOGLE_MOCK_URL).mock(
        return_value=httpx.Response(200, json=GOOGLE_RESPONSE)
    )
    result = await fetch_weather("PSR/166,61")
    assert result.source == "fallback"
    assert result.temperature == 90
    assert result.short_forecast == "Sunny"
    assert result.period_name == "Today"
    assert result.precip_percent == 5
    assert "High near 90°F" in result.detailed_forecast


@respx.mock
async def test_fetch_weather_uses_cache_when_both_apis_fail(monkeypatch):
    import app.weather as weather_module
    cached = WeatherData(
        period_name="Today",
        temperature=88,
        short_forecast="Cloudy",
        detailed_forecast="Cloudy.",
        precip_percent=10,
        source="primary",
    )
    monkeypatch.setattr(weather_module, "_last_good_weather", cached)
    monkeypatch.setattr(weather_module, "_GOOGLE_WEATHER_URL", GOOGLE_MOCK_URL)
    respx.get("https://api.weather.gov/gridpoints/PSR/166,61/forecast").mock(
        return_value=httpx.Response(503)
    )
    respx.get(GOOGLE_MOCK_URL).mock(return_value=httpx.Response(503))
    result = await fetch_weather("PSR/166,61")
    assert result.source == "cached"
    assert result.temperature == 88
    assert result.short_forecast == "Cloudy"


@respx.mock
async def test_fetch_weather_raises_when_all_fail_and_no_cache(monkeypatch):
    import app.weather as weather_module
    monkeypatch.setattr(weather_module, "_last_good_weather", None)
    monkeypatch.setattr(weather_module, "_GOOGLE_WEATHER_URL", GOOGLE_MOCK_URL)
    respx.get("https://api.weather.gov/gridpoints/PSR/166,61/forecast").mock(
        return_value=httpx.Response(503)
    )
    respx.get(GOOGLE_MOCK_URL).mock(return_value=httpx.Response(503))
    with pytest.raises(httpx.HTTPStatusError):
        await fetch_weather("PSR/166,61")


@respx.mock
async def test_fetch_weather_fallback_tonight_when_not_daytime(monkeypatch):
    import app.weather as weather_module
    monkeypatch.setattr(weather_module, "_last_good_weather", None)
    monkeypatch.setattr(weather_module, "_GOOGLE_WEATHER_URL", GOOGLE_MOCK_URL)
    night_response = {**GOOGLE_RESPONSE, "isDaytime": False}
    respx.get("https://api.weather.gov/gridpoints/PSR/166,61/forecast").mock(
        return_value=httpx.Response(503)
    )
    respx.get(GOOGLE_MOCK_URL).mock(
        return_value=httpx.Response(200, json=night_response)
    )
    result = await fetch_weather("PSR/166,61")
    assert result.period_name == "Tonight"
