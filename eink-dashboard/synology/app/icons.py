from __future__ import annotations

import io
from typing import Optional

import httpx
from PIL import Image

BASE_URL = "https://raw.githubusercontent.com/basmilius/weather-icons/dev/production/fill/svg/"

# (keywords, day_icon, night_icon) — first match wins, case-insensitive substring.
# Multi-word keywords must precede their component single words to avoid false early matches.
ICON_MAPPING: list[tuple[list[str], str, str]] = [
    (["mostly sunny", "mostly clear"], "partly-cloudy-day", "partly-cloudy-night"),
    (["partly cloudy", "partly sunny"], "partly-cloudy-day", "partly-cloudy-night"),
    (["mostly cloudy"], "overcast-day", "overcast-night"),
    (["sunny", "clear", "hot"], "clear-day", "clear-night"),
    (["cloudy", "overcast"], "cloudy", "cloudy"),
    (["freezing drizzle", "drizzle"], "partly-cloudy-day-drizzle", "partly-cloudy-night-drizzle"),
    (["showers", "chance rain"], "partly-cloudy-day-rain", "partly-cloudy-night-rain"),
    (["heavy rain", "flood"], "extreme-day-rain", "extreme-night-rain"),
    (["sleet", "freezing rain", "wintry mix"], "overcast-day-sleet", "overcast-night-sleet"),
    (["rain"], "overcast-day-rain", "overcast-night-rain"),
    (["blizzard", "heavy snow"], "extreme-day-snow", "extreme-night-snow"),
    (["flurries", "chance snow"], "partly-cloudy-day-snow", "partly-cloudy-night-snow"),
    (["snow"], "overcast-day-snow", "overcast-night-snow"),
    (["thunder", "storm"], "thunderstorms-day", "thunderstorms-night"),
    (["tornado", "hurricane", "tropical"], "tornado", "hurricane"),
    (["fog", "mist"], "fog-day", "fog-night"),
    (["haze", "smoke", "dust", "sand"], "haze-day", "haze-night"),
    (["wind", "breezy", "blustery"], "wind", "wind"),
]

_NIGHT_NAMES = {"tonight", "overnight"}


def _is_night(period_name: str) -> bool:
    return period_name.lower() in _NIGHT_NAMES


def select_icon_name(short_forecast: str, period_name: str) -> str:
    forecast_lower = short_forecast.lower()
    night = _is_night(period_name)
    for keywords, day_icon, night_icon in ICON_MAPPING:
        if any(kw in forecast_lower for kw in keywords):
            return night_icon if night else day_icon
    return "clear-night" if night else "clear-day"


def _all_icon_names() -> list[str]:
    seen: set[str] = set()
    names: list[str] = []
    for _, day, night in ICON_MAPPING:
        for name in (day, night):
            if name not in seen:
                seen.add(name)
                names.append(name)
    for name in ("clear-day", "clear-night"):
        if name not in seen:
            names.append(name)
    return names


def rasterize_svg(name: str, size: int) -> Image.Image:
    import cairosvg

    url = f"{BASE_URL}{name}.svg"
    with httpx.Client(timeout=10) as client:
        resp = client.get(url)
        resp.raise_for_status()
        svg_bytes = resp.content
    png_bytes = cairosvg.svg2png(bytestring=svg_bytes, output_width=size, output_height=size)
    return Image.open(io.BytesIO(png_bytes)).convert("RGBA")


def load_all_icons(size: int = 120) -> dict[str, Image.Image]:
    icons: dict[str, Image.Image] = {}
    for name in _all_icon_names():
        try:
            icons[name] = rasterize_svg(name, size)
        except Exception:
            icons[name] = Image.new("RGBA", (size, size), (200, 200, 200, 255))
    return icons
