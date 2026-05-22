import io
import pytest
import respx
import httpx
from unittest.mock import patch, AsyncMock
from PIL import Image

from fastapi.testclient import TestClient


def _blank_icons():
    img = Image.new("RGBA", (120, 120), (200, 200, 200, 255))
    return {"clear-day": img, "clear-night": img}


NOAA_RESP = {
    "properties": {
        "periods": [
            {
                "name": "Today",
                "temperature": 85,
                "shortForecast": "Sunny",
                "detailedForecast": "Sunny.",
                "probabilityOfPrecipitation": {"value": 0},
            }
        ]
    }
}

QUOTE_RESP = [{"q": "Test.", "a": "Author"}]


@pytest.fixture
def client():
    with (
        patch("app.scheduler.load_all_icons", return_value=_blank_icons()),
        respx.mock,
    ):
        respx.get("https://api.weather.gov/gridpoints/PSR/166,61/forecast").mock(
            return_value=httpx.Response(200, json=NOAA_RESP)
        )
        respx.get("https://zenquotes.io/api/random").mock(
            return_value=httpx.Response(200, json=QUOTE_RESP)
        )
        from app.main import app
        with TestClient(app) as c:
            yield c


def test_joe_endpoint_returns_png(client):
    resp = client.get("/dashboard/joe.png")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "image/png"
    img = Image.open(io.BytesIO(resp.content))
    assert img.size == (800, 480)


def test_sam_endpoint_returns_png(client):
    resp = client.get("/dashboard/sam.png")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "image/png"
    img = Image.open(io.BytesIO(resp.content))
    assert img.size == (600, 400)


def test_health_endpoint(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert "last_refresh" in data
    assert "noaa_ok" in data
    assert "quotes_ok" in data


def test_almanac_classic_endpoint_returns_png(client):
    resp = client.get("/proto/almanac-classic.png")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "image/png"
    img = Image.open(io.BytesIO(resp.content))
    assert img.size == (800, 480)


def test_almanac_classic_inv_endpoint_returns_png(client):
    resp = client.get("/proto/almanac-classic-inv.png")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "image/png"


def test_almanac_modern_endpoint_returns_png(client):
    resp = client.get("/proto/almanac-modern.png")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "image/png"


def test_almanac_modern_inv_endpoint_returns_png(client):
    resp = client.get("/proto/almanac-modern-inv.png")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "image/png"
