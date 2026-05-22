from __future__ import annotations

# (keywords, temp_color, icon_bg_color)
# First match wins. Keywords are case-insensitive substrings of short_forecast.
# Colors drawn from the Inky Impression native 7-color palette to avoid dithering.
_ACCENT_MAP: list[tuple[list[str], str, str]] = [
    (["mostly sunny", "mostly clear"], "#ffe900", "#ffe900"),
    (["partly cloudy", "partly sunny"], "#aaaaaa", "#2a2a2a"),
    (["mostly cloudy"], "#aaaaaa", "#2a2a2a"),
    (["sunny", "clear", "hot"], "#ffe900", "#ffe900"),
    (["cloudy", "overcast"], "#aaaaaa", "#2a2a2a"),
    (["freezing drizzle", "drizzle"], "#cce8ff", "#1a3a5c"),
    (["showers", "chance rain"], "#5b9bd5", "#00439c"),
    (["heavy rain", "flood"], "#5b9bd5", "#00439c"),
    (["sleet", "freezing rain", "wintry mix"], "#cce8ff", "#1a3a5c"),
    (["rain"], "#5b9bd5", "#00439c"),
    (["blizzard", "heavy snow"], "#cce8ff", "#1a3a5c"),
    (["flurries", "chance snow"], "#cce8ff", "#1a3a5c"),
    (["snow"], "#cce8ff", "#1a3a5c"),
    (["thunder", "storm"], "#ff7201", "#333333"),
    (["tornado", "hurricane", "tropical"], "#ff7201", "#333333"),
    (["fog", "mist"], "#888888", "#222222"),
    (["haze", "smoke", "dust", "sand"], "#888888", "#222222"),
    (["wind", "breezy", "blustery"], "#aaaaaa", "#2a2a2a"),
]


def select_accent(short_forecast: str) -> tuple[str, str]:
    """Return (temp_color, icon_bg_color) for the given NOAA shortForecast string."""
    forecast_lower = short_forecast.lower()
    for keywords, temp_color, icon_bg in _ACCENT_MAP:
        if any(kw in forecast_lower for kw in keywords):
            return temp_color, icon_bg
    return "#ffe900", "#ffe900"
