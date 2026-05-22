import pytest
from app.accent import select_accent


@pytest.mark.parametrize("forecast,expected_temp,expected_bg", [
    ("Sunny", "#ffe900", "#ffe900"),
    ("Mostly Sunny", "#ffe900", "#ffe900"),
    ("Partly Cloudy", "#aaaaaa", "#2a2a2a"),
    ("Cloudy", "#aaaaaa", "#2a2a2a"),
    ("Rain", "#5b9bd5", "#00439c"),
    ("Showers", "#5b9bd5", "#00439c"),
    ("Heavy Rain", "#5b9bd5", "#00439c"),
    ("Thunderstorms", "#ff7201", "#333333"),
    ("Snow", "#cce8ff", "#1a3a5c"),
    ("Blizzard", "#cce8ff", "#1a3a5c"),
    ("Fog", "#888888", "#222222"),
    ("Breezy", "#aaaaaa", "#2a2a2a"),
    ("Unknown XYZ", "#ffe900", "#ffe900"),
])
def test_select_accent(forecast, expected_temp, expected_bg):
    temp, bg = select_accent(forecast)
    assert temp == expected_temp
    assert bg == expected_bg
