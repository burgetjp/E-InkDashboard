import pytest
import respx
import httpx
from unittest.mock import patch, MagicMock
from PIL import Image

from app.cache import DashboardCache
from app.scheduler import refresh_dashboard

NOAA_RESP = {
    "properties": {
        "periods": [
            {
                "name": "Today",
                "temperature": 85,
                "shortForecast": "Sunny",
                "detailedForecast": "Sunny skies.",
                "probabilityOfPrecipitation": {"value": 0},
            }
        ]
    }
}

QUOTE_RESP = [{"q": "Test quote.", "a": "Test Author"}]


def _blank_icons():
    img = Image.new("RGBA", (120, 120), (200, 200, 200, 255))
    return {name: img for name in ["clear-day", "clear-night"]}


@respx.mock
async def test_refresh_dashboard_populates_cache():
    respx.get("https://api.weather.gov/gridpoints/PSR/166,61/forecast").mock(
        return_value=httpx.Response(200, json=NOAA_RESP)
    )
    respx.get("https://zenquotes.io/api/random").mock(
        return_value=httpx.Response(200, json=QUOTE_RESP)
    )
    c = DashboardCache()
    with patch("app.scheduler.load_all_icons", return_value=_blank_icons()):
        await refresh_dashboard(cache=c, noaa_grid="PSR/166,61")

    assert c.joe_png is not None
    assert c.sam_png is not None
    assert c.noaa_ok is True
    assert c.quotes_ok is True
    assert c.last_refresh is not None


@respx.mock
async def test_refresh_dashboard_keeps_previous_on_noaa_failure():
    import io
    from PIL import Image as PILImage

    def _png():
        buf = io.BytesIO()
        PILImage.new("RGB", (10, 10), "blue").save(buf, format="PNG")
        return buf.getvalue()

    c = DashboardCache()
    old_joe, old_sam = _png(), _png()
    c.store(old_joe, old_sam, noaa_ok=True, quotes_ok=True)

    respx.get("https://api.weather.gov/gridpoints/PSR/166,61/forecast").mock(
        return_value=httpx.Response(503)
    )
    respx.get("https://zenquotes.io/api/random").mock(
        return_value=httpx.Response(200, json=QUOTE_RESP)
    )
    with patch("app.scheduler.load_all_icons", return_value=_blank_icons()):
        await refresh_dashboard(cache=c, noaa_grid="PSR/166,61")

    assert c.joe_png == old_joe
    assert c.sam_png == old_sam
    assert c.noaa_ok is False


@respx.mock
async def test_refresh_dashboard_populates_almanac_sam():
    respx.get("https://api.weather.gov/gridpoints/PSR/166,61/forecast").mock(
        return_value=httpx.Response(200, json=NOAA_RESP)
    )
    respx.get("https://zenquotes.io/api/random").mock(
        return_value=httpx.Response(200, json=QUOTE_RESP)
    )
    c = DashboardCache()
    with patch("app.scheduler.load_all_icons", return_value=_blank_icons()):
        await refresh_dashboard(cache=c, noaa_grid="PSR/166,61")

    assert c.almanac_sam is not None
