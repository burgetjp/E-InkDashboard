import pytest
from unittest.mock import patch, MagicMock
from PIL import Image

from app.icons import select_icon_name, load_all_icons


@pytest.mark.parametrize("short_forecast,period_name,expected_day,expected_night", [
    ("Sunny", "Today", "clear-day", "clear-night"),
    ("Mostly Sunny", "Today", "partly-cloudy-day", "partly-cloudy-night"),
    ("Partly Cloudy", "Today", "partly-cloudy-day", "partly-cloudy-night"),
    ("Mostly Cloudy", "Today", "overcast-day", "overcast-night"),
    ("Cloudy", "Today", "cloudy", "cloudy"),
    ("Showers", "Today", "partly-cloudy-day-rain", "partly-cloudy-night-rain"),
    ("Heavy Rain", "Today", "extreme-day-rain", "extreme-night-rain"),
    ("Rain", "Today", "overcast-day-rain", "overcast-night-rain"),
    ("Snow", "Today", "overcast-day-snow", "overcast-night-snow"),
    ("Blizzard", "Today", "extreme-day-snow", "extreme-night-snow"),
    ("Thunder", "Today", "thunderstorms-day", "thunderstorms-night"),
    ("Fog", "Today", "fog-day", "fog-night"),
    ("Wind", "Today", "wind", "wind"),
    ("Unknown condition XYZ", "Today", "clear-day", "clear-night"),
])
def test_select_icon_name_day(short_forecast, period_name, expected_day, expected_night):
    assert select_icon_name(short_forecast, period_name) == expected_day


def test_select_icon_name_night():
    assert select_icon_name("Sunny", "Tonight") == "clear-night"
    assert select_icon_name("Rain", "Overnight") == "overcast-night-rain"
    assert select_icon_name("Cloudy", "Tonight") == "cloudy"


def test_load_all_icons_returns_dict():
    with patch("app.icons.rasterize_svg") as mock_raster:
        mock_raster.return_value = Image.new("RGBA", (120, 120))
        icons = load_all_icons(size=120)
    assert isinstance(icons, dict)
    assert "clear-day" in icons
    assert "clear-night" in icons
    assert isinstance(icons["clear-day"], Image.Image)
