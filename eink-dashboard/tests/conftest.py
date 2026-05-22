import pytest
from PIL import Image

from app.weather import WeatherData
from app.quotes import QuoteData


@pytest.fixture
def sample_weather():
    return WeatherData(
        period_name="Today",
        temperature=91,
        short_forecast="Sunny",
        detailed_forecast="Sunny. High near 91. Southwest wind around 5 mph.",
        precip_percent=3,
    )


@pytest.fixture
def sample_quote():
    return QuoteData(
        text="The divine is not something high above us.",
        author="Morihei Ueshiba",
    )


@pytest.fixture
def blank_icon():
    return Image.new("RGBA", (120, 120), (255, 200, 0, 255))
