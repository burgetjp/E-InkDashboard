# E-Ink Dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a FastAPI + Pillow server that generates PNG dashboard images for two Pimoroni Inky e-ink displays, deployed in Docker on a Synology NAS.

**Architecture:** FastAPI serves two cached PNG endpoints (`/dashboard/joe.png` at 800×480, `/dashboard/sam.png` at 600×400). APScheduler refreshes both images hourly by fetching NOAA weather and ZenQuotes, rasterizing a Basmilius weather icon, and rendering with Pillow. The Raspberry Pi replaces its Firefox screenshot flow with a single `curl` call — all Pi-side display scripts remain unchanged.

**Tech Stack:** Python 3.12, FastAPI, Pillow, httpx, cairosvg, APScheduler, pydantic-settings, pytest, respx, Docker

---

## File Map

```
eink-dashboard/                   ← new project root (sibling to as-is/)
├── app/
│   ├── __init__.py
│   ├── main.py                   FastAPI app, lifespan, routes
│   ├── config.py                 Pydantic settings from env vars
│   ├── cache.py                  In-memory PNG cache + fallback PNG
│   ├── weather.py                NOAA API client + WeatherData dataclass
│   ├── quotes.py                 ZenQuotes API client + QuoteData dataclass
│   ├── icons.py                  SVG rasterization + condition→icon mapping
│   ├── draw_utils.py             Shared Pillow helper: wrap_text
│   ├── render_joe.py             800×480 Pillow renderer
│   ├── render_sam.py             600×400 Pillow renderer
│   └── scheduler.py              APScheduler setup + refresh_dashboard job
├── assets/
│   └── fonts/
│       ├── Inter-Regular.ttf
│       ├── Inter-Bold.ttf
│       └── Inter-Italic.ttf
├── tests/
│   ├── conftest.py               Shared fixtures
│   ├── test_weather.py
│   ├── test_quotes.py
│   ├── test_icons.py
│   ├── test_draw_utils.py
│   ├── test_render_joe.py
│   ├── test_render_sam.py
│   ├── test_cache.py
│   └── test_api.py               FastAPI TestClient tests
├── scripts/
│   └── dailyDash.sh              Updated Pi script (replaces as-is version)
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── pytest.ini
```

---

## Task 1: Project Scaffold

**Files:**
- Create: `eink-dashboard/requirements.txt`
- Create: `eink-dashboard/.env.example`
- Create: `eink-dashboard/pytest.ini`
- Create: `eink-dashboard/app/__init__.py`
- Create: `eink-dashboard/tests/__init__.py`
- Create: `eink-dashboard/assets/fonts/.gitkeep`

- [ ] **Step 1: Create the project directory structure**

```bash
cd /Users/joeburgett/Working/E-InkDashboard
mkdir -p eink-dashboard/app eink-dashboard/tests eink-dashboard/assets/fonts eink-dashboard/scripts
touch eink-dashboard/app/__init__.py eink-dashboard/tests/__init__.py
```

- [ ] **Step 2: Write requirements.txt**

```
# eink-dashboard/requirements.txt
fastapi>=0.115.0
uvicorn[standard]>=0.30.0
httpx>=0.27.0
pillow>=10.4.0
cairosvg>=2.7.0
apscheduler>=3.10.4
pydantic-settings>=2.3.0

# Testing
pytest>=8.3.0
pytest-asyncio>=0.23.0
respx>=0.21.0
anyio>=4.4.0
```

- [ ] **Step 3: Write .env.example**

```
# eink-dashboard/.env.example
PORT=8000
NOAA_GRID=PSR/166,61
REFRESH_HOUR_INTERVAL=1
```

- [ ] **Step 4: Write pytest.ini**

```ini
# eink-dashboard/pytest.ini
[pytest]
asyncio_mode = auto
testpaths = tests
```

- [ ] **Step 5: Download Inter fonts into assets/fonts/**

```bash
cd eink-dashboard/assets/fonts
curl -L "https://github.com/rsms/inter/releases/download/v4.0/Inter-4.0.zip" -o inter.zip
unzip -j inter.zip "*.ttf" -x "*[Hh]airline*" "*[Dd]isplay*" "*[Mm]edium*" "*[Ll]ight*" "*[Ee]xtra*" "*[Ss]emi*" "*[Tt]hin*" "*[Bb]lack*"
# Keep only: Inter-Regular.ttf, Inter-Bold.ttf, Inter-Italic.ttf
ls *.ttf
rm inter.zip
```

Verify these three files exist: `Inter-Regular.ttf`, `Inter-Bold.ttf`, `Inter-Italic.ttf`

- [ ] **Step 6: Install dependencies**

```bash
cd eink-dashboard
pip install -r requirements.txt
```

- [ ] **Step 7: Commit**

```bash
cd eink-dashboard
git add .
git commit -m "feat: scaffold eink-dashboard project structure"
```

---

## Task 2: Config Module

**Files:**
- Create: `eink-dashboard/app/config.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_config.py  (create this file)
from app.config import settings

def test_defaults():
    assert settings.port == 8000
    assert settings.noaa_grid == "PSR/166,61"
    assert settings.refresh_hour_interval == 1
```

- [ ] **Step 2: Run to confirm failure**

```bash
cd eink-dashboard
pytest tests/test_config.py -v
```

Expected: `ImportError: cannot import name 'settings'`

- [ ] **Step 3: Implement config.py**

```python
# app/config.py
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    port: int = 8000
    noaa_grid: str = "PSR/166,61"
    refresh_hour_interval: int = 1

    model_config = {"env_file": ".env"}


settings = Settings()
```

- [ ] **Step 4: Run to confirm pass**

```bash
pytest tests/test_config.py -v
```

Expected: `PASSED`

- [ ] **Step 5: Commit**

```bash
git add app/config.py tests/test_config.py
git commit -m "feat: add config module with pydantic settings"
```

---

## Task 3: Test Fixtures (conftest.py)

**Files:**
- Create: `eink-dashboard/tests/conftest.py`

- [ ] **Step 1: Write conftest.py**

These fixtures are used by all renderer and scheduler tests.

```python
# tests/conftest.py
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
        detailed_forecast=(
            "Sunny. High near 91, with temperatures falling to around 89 in the afternoon. "
            "South southwest wind around 5 mph."
        ),
        precip_percent=3,
    )


@pytest.fixture
def sample_weather_night():
    return WeatherData(
        period_name="Tonight",
        temperature=74,
        short_forecast="Clear",
        detailed_forecast="Clear skies overnight. Low near 74. South winds around 5 mph.",
        precip_percent=0,
    )


@pytest.fixture
def sample_quote():
    return QuoteData(
        text="The divine is not something high above us. It is in heaven, it is in earth, it is inside us.",
        author="Morihei Ueshiba",
    )


@pytest.fixture
def sample_icon():
    """120×120 RGBA orange square standing in for a real weather icon."""
    img = Image.new("RGBA", (120, 120), (255, 165, 0, 255))
    return img
```

- [ ] **Step 2: Verify fixtures load**

```bash
pytest tests/conftest.py --collect-only
```

Expected: no errors, fixtures collected

- [ ] **Step 3: Commit**

```bash
git add tests/conftest.py
git commit -m "test: add shared fixtures to conftest"
```

---

## Task 4: Weather Client

**Files:**
- Create: `eink-dashboard/app/weather.py`
- Create: `eink-dashboard/tests/test_weather.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_weather.py
import pytest
import respx
import httpx
from app.weather import fetch_weather, WeatherData

NOAA_URL = "https://api.weather.gov/gridpoints/PSR/166,61/forecast"

NOAA_RESPONSE = {
    "properties": {
        "periods": [
            {
                "name": "Today",
                "temperature": 91,
                "temperatureUnit": "F",
                "shortForecast": "Sunny",
                "detailedForecast": "Sunny. High near 91. South southwest wind around 5 mph.",
                "probabilityOfPrecipitation": {"value": 3},
            }
        ]
    }
}


@respx.mock
async def test_fetch_weather_returns_dataclass():
    respx.get(NOAA_URL).mock(return_value=httpx.Response(200, json=NOAA_RESPONSE))
    result = await fetch_weather("PSR/166,61")
    assert isinstance(result, WeatherData)
    assert result.temperature == 91
    assert result.period_name == "Today"
    assert result.short_forecast == "Sunny"
    assert result.precip_percent == 3


@respx.mock
async def test_fetch_weather_raises_on_http_error():
    respx.get(NOAA_URL).mock(return_value=httpx.Response(500))
    with pytest.raises(httpx.HTTPStatusError):
        await fetch_weather("PSR/166,61")


@respx.mock
async def test_fetch_weather_handles_null_precip():
    response = {
        "properties": {
            "periods": [
                {
                    "name": "Tonight",
                    "temperature": 74,
                    "temperatureUnit": "F",
                    "shortForecast": "Clear",
                    "detailedForecast": "Clear overnight.",
                    "probabilityOfPrecipitation": {"value": None},
                }
            ]
        }
    }
    respx.get(NOAA_URL).mock(return_value=httpx.Response(200, json=response))
    result = await fetch_weather("PSR/166,61")
    assert result.precip_percent == 0
```

- [ ] **Step 2: Run to confirm failure**

```bash
pytest tests/test_weather.py -v
```

Expected: `ImportError: cannot import name 'fetch_weather'`

- [ ] **Step 3: Implement weather.py**

```python
# app/weather.py
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
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            url,
            headers={"User-Agent": "InkyDashboard/1.0"},
            timeout=10,
        )
        resp.raise_for_status()
    period = resp.json()["properties"]["periods"][0]
    return WeatherData(
        period_name=period["name"],
        temperature=period["temperature"],
        short_forecast=period["shortForecast"],
        detailed_forecast=period["detailedForecast"],
        precip_percent=period["probabilityOfPrecipitation"]["value"] or 0,
    )
```

- [ ] **Step 4: Run to confirm pass**

```bash
pytest tests/test_weather.py -v
```

Expected: 3 tests `PASSED`

- [ ] **Step 5: Commit**

```bash
git add app/weather.py tests/test_weather.py
git commit -m "feat: add NOAA weather client"
```

---

## Task 5: Quote Client

**Files:**
- Create: `eink-dashboard/app/quotes.py`
- Create: `eink-dashboard/tests/test_quotes.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_quotes.py
import pytest
import respx
import httpx
from app.quotes import fetch_quote, QuoteData

QUOTES_URL = "https://zenquotes.io/api/random"


@respx.mock
async def test_fetch_quote_returns_dataclass():
    respx.get(QUOTES_URL).mock(return_value=httpx.Response(
        200,
        json=[{"q": "Test quote text.", "a": "Test Author"}],
    ))
    result = await fetch_quote()
    assert isinstance(result, QuoteData)
    assert result.text == "Test quote text."
    assert result.author == "Test Author"


@respx.mock
async def test_fetch_quote_raises_on_http_error():
    respx.get(QUOTES_URL).mock(return_value=httpx.Response(429))
    with pytest.raises(httpx.HTTPStatusError):
        await fetch_quote()
```

- [ ] **Step 2: Run to confirm failure**

```bash
pytest tests/test_quotes.py -v
```

Expected: `ImportError: cannot import name 'fetch_quote'`

- [ ] **Step 3: Implement quotes.py**

```python
# app/quotes.py
from dataclasses import dataclass
import httpx


@dataclass
class QuoteData:
    text: str
    author: str


async def fetch_quote() -> QuoteData:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://zenquotes.io/api/random",
            timeout=10,
        )
        resp.raise_for_status()
    data = resp.json()
    return QuoteData(text=data[0]["q"], author=data[0]["a"])
```

- [ ] **Step 4: Run to confirm pass**

```bash
pytest tests/test_quotes.py -v
```

Expected: 2 tests `PASSED`

- [ ] **Step 5: Commit**

```bash
git add app/quotes.py tests/test_quotes.py
git commit -m "feat: add ZenQuotes client"
```

---

## Task 6: Icon Mapping + Rasterization

**Files:**
- Create: `eink-dashboard/app/icons.py`
- Create: `eink-dashboard/tests/test_icons.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_icons.py
import pytest
import respx
import httpx
from PIL import Image
from app.icons import select_icon_name, rasterize_svg, load_all_icons

ICON_BASE = "https://raw.githubusercontent.com/basmilius/weather-icons/dev/production/fill/svg/"

# Minimal valid SVG for mocking
MOCK_SVG = b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><circle cx="50" cy="50" r="40" fill="orange"/></svg>'


def test_select_icon_sunny_day():
    assert select_icon_name("Sunny", "Today") == "clear-day"


def test_select_icon_clear_night():
    assert select_icon_name("Clear", "Tonight") == "clear-night"


def test_select_icon_partly_cloudy_day():
    assert select_icon_name("Partly Cloudy", "Today") == "partly-cloudy-day"


def test_select_icon_heavy_rain_beats_rain():
    # "heavy rain" must match before "rain" (first-match-wins ordering)
    assert select_icon_name("Heavy Rain", "Today") == "extreme-day-rain"


def test_select_icon_blizzard_beats_snow():
    assert select_icon_name("Blizzard", "Tonight") == "extreme-night-snow"


def test_select_icon_thunderstorm_day():
    assert select_icon_name("Thunderstorms", "Today") == "thunderstorms-day"


def test_select_icon_fog_night():
    assert select_icon_name("Patchy Fog", "Tonight") == "fog-night"


def test_select_icon_fallback_day():
    assert select_icon_name("Unknown Condition XYZ", "Today") == "clear-day"


def test_select_icon_fallback_night():
    assert select_icon_name("Unknown Condition XYZ", "Tonight") == "clear-night"


@respx.mock
async def test_rasterize_svg_returns_rgba_image():
    respx.get(f"{ICON_BASE}clear-day.svg").mock(
        return_value=httpx.Response(200, content=MOCK_SVG)
    )
    img = await rasterize_svg("clear-day", size=120)
    assert isinstance(img, Image.Image)
    assert img.size == (120, 120)
    assert img.mode == "RGBA"
```

- [ ] **Step 2: Run to confirm failure**

```bash
pytest tests/test_icons.py -v
```

Expected: `ImportError: cannot import name 'select_icon_name'`

- [ ] **Step 3: Implement icons.py**

```python
# app/icons.py
from __future__ import annotations
import io
import httpx
import cairosvg
from PIL import Image

ICON_BASE = "https://raw.githubusercontent.com/basmilius/weather-icons/dev/production/fill/svg/"

# Ordered top-to-bottom — first keyword match wins
ICON_MAPPING: list[tuple[list[str], str, str]] = [
    (["sunny", "clear", "hot"],                        "clear-day",                   "clear-night"),
    (["mostly sunny", "mostly clear"],                 "partly-cloudy-day",           "partly-cloudy-night"),
    (["partly cloudy", "partly sunny"],                "partly-cloudy-day",           "partly-cloudy-night"),
    (["mostly cloudy"],                                "overcast-day",                "overcast-night"),
    (["cloudy", "overcast"],                           "cloudy",                      "cloudy"),
    (["drizzle", "freezing drizzle"],                  "partly-cloudy-day-drizzle",   "partly-cloudy-night-drizzle"),
    (["showers", "chance rain"],                       "partly-cloudy-day-rain",      "partly-cloudy-night-rain"),
    (["heavy rain", "flood"],                          "extreme-day-rain",            "extreme-night-rain"),
    (["rain"],                                         "overcast-day-rain",           "overcast-night-rain"),
    (["sleet", "freezing rain", "wintry mix"],         "overcast-day-sleet",          "overcast-night-sleet"),
    (["blizzard", "heavy snow"],                       "extreme-day-snow",            "extreme-night-snow"),
    (["flurries", "chance snow"],                      "partly-cloudy-day-snow",      "partly-cloudy-night-snow"),
    (["snow"],                                         "overcast-day-snow",           "overcast-night-snow"),
    (["thunder", "storm"],                             "thunderstorms-day",           "thunderstorms-night"),
    (["tornado", "hurricane", "tropical"],             "tornado",                     "hurricane"),
    (["fog", "mist"],                                  "fog-day",                     "fog-night"),
    (["haze", "smoke", "dust", "sand"],                "haze-day",                    "haze-night"),
    (["wind", "breezy", "blustery"],                   "wind",                        "wind"),
]

_FALLBACK_DAY = "clear-day"
_FALLBACK_NIGHT = "clear-night"
_NIGHT_PERIODS = {"tonight", "overnight"}


def select_icon_name(short_forecast: str, period_name: str) -> str:
    forecast_lower = short_forecast.lower()
    is_night = period_name.lower() in _NIGHT_PERIODS
    for keywords, day_icon, night_icon in ICON_MAPPING:
        if any(kw in forecast_lower for kw in keywords):
            return night_icon if is_night else day_icon
    return _FALLBACK_NIGHT if is_night else _FALLBACK_DAY


async def rasterize_svg(name: str, size: int) -> Image.Image:
    url = f"{ICON_BASE}{name}.svg"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, timeout=15)
        resp.raise_for_status()
    png_bytes = cairosvg.svg2png(
        bytestring=resp.content,
        output_width=size,
        output_height=size,
    )
    return Image.open(io.BytesIO(png_bytes)).convert("RGBA")


async def load_all_icons(size: int = 120) -> dict[str, Image.Image]:
    names: set[str] = {_FALLBACK_DAY, _FALLBACK_NIGHT}
    for _, day_icon, night_icon in ICON_MAPPING:
        names.add(day_icon)
        names.add(night_icon)
    icons: dict[str, Image.Image] = {}
    for name in sorted(names):
        icons[name] = await rasterize_svg(name, size)
    return icons
```

- [ ] **Step 4: Run to confirm pass**

```bash
pytest tests/test_icons.py -v
```

Expected: all tests `PASSED`

- [ ] **Step 5: Commit**

```bash
git add app/icons.py tests/test_icons.py
git commit -m "feat: add icon mapping and SVG rasterization"
```

---

## Task 7: Drawing Utilities

**Files:**
- Create: `eink-dashboard/app/draw_utils.py`
- Create: `eink-dashboard/tests/test_draw_utils.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_draw_utils.py
from PIL import Image, ImageDraw, ImageFont
from app.draw_utils import wrap_text


def _make_draw(width: int = 400) -> tuple[Image.Image, ImageDraw.Draw]:
    img = Image.new("RGB", (width, 200), "white")
    return img, ImageDraw.Draw(img)


def test_wrap_text_short_string_single_line():
    img, draw = _make_draw()
    font = ImageFont.load_default()
    lines = wrap_text(draw, "Hello world", font, max_width=400)
    assert lines == ["Hello world"]


def test_wrap_text_long_string_wraps():
    img, draw = _make_draw(200)
    font = ImageFont.load_default()
    text = "The quick brown fox jumps over the lazy dog"
    lines = wrap_text(draw, text, font, max_width=100)
    assert len(lines) > 1
    # All words appear across all lines
    assert " ".join(lines) == text


def test_wrap_text_empty_string():
    img, draw = _make_draw()
    font = ImageFont.load_default()
    assert wrap_text(draw, "", font, max_width=400) == []


def test_wrap_text_single_word_too_wide():
    img, draw = _make_draw()
    font = ImageFont.load_default()
    # Even if a word is wider than max_width, it must appear on its own line
    lines = wrap_text(draw, "Supercalifragilisticexpialidocious", font, max_width=1)
    assert len(lines) == 1
    assert "Supercalifragilisticexpialidocious" in lines[0]
```

- [ ] **Step 2: Run to confirm failure**

```bash
pytest tests/test_draw_utils.py -v
```

Expected: `ImportError: cannot import name 'wrap_text'`

- [ ] **Step 3: Implement draw_utils.py**

```python
# app/draw_utils.py
from PIL import ImageDraw, ImageFont


def wrap_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont,
    max_width: int,
) -> list[str]:
    """Split text into lines that fit within max_width pixels."""
    if not text:
        return []
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if draw.textlength(candidate, font=font) <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines
```

- [ ] **Step 4: Run to confirm pass**

```bash
pytest tests/test_draw_utils.py -v
```

Expected: 4 tests `PASSED`

- [ ] **Step 5: Commit**

```bash
git add app/draw_utils.py tests/test_draw_utils.py
git commit -m "feat: add wrap_text drawing utility"
```

---

## Task 8: Joe Renderer (800×480)

**Files:**
- Create: `eink-dashboard/app/render_joe.py`
- Create: `eink-dashboard/tests/test_render_joe.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_render_joe.py
from PIL import Image
from app.render_joe import render_joe


def test_render_joe_correct_size(sample_weather, sample_quote, sample_icon):
    img = render_joe(sample_weather, sample_quote, sample_icon)
    assert img.size == (800, 480)


def test_render_joe_returns_rgb(sample_weather, sample_quote, sample_icon):
    img = render_joe(sample_weather, sample_quote, sample_icon)
    assert img.mode == "RGB"


def test_render_joe_not_blank(sample_weather, sample_quote, sample_icon):
    img = render_joe(sample_weather, sample_quote, sample_icon)
    pixels = list(img.getdata())
    unique = set(pixels)
    assert len(unique) > 1, "Image appears blank — nothing was drawn"


def test_render_joe_works_without_icon(sample_weather, sample_quote):
    img = render_joe(sample_weather, sample_quote, icon=None)
    assert img.size == (800, 480)
```

- [ ] **Step 2: Run to confirm failure**

```bash
pytest tests/test_render_joe.py -v
```

Expected: `ImportError: cannot import name 'render_joe'`

- [ ] **Step 3: Implement render_joe.py**

```python
# app/render_joe.py
from __future__ import annotations
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from app.draw_utils import wrap_text
from app.weather import WeatherData
from app.quotes import QuoteData

_ASSETS = Path(__file__).parent.parent / "assets"
_FONTS = _ASSETS / "fonts"

# Dimensions
W, H = 800, 480
PAD = 16
GAP = 12

# Colors (Joe: white/blue theme)
BG            = "#f8f9fa"
WEATHER_BG    = "#e8f0fe"
FORECAST_BG   = "#d1e0fd"
QUOTE_BG      = "#ffffff"
TEMP_COLOR    = "#1a56db"
ACCENT        = "#1a56db"
TEXT_DARK     = "#212529"
TEXT_MID      = "#374151"
TEXT_LIGHT    = "#6c757d"
BORDER_COLOR  = "#dee2e6"


def render_joe(
    weather: WeatherData,
    quote: QuoteData,
    icon: Image.Image | None,
) -> Image.Image:
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    f_label   = ImageFont.truetype(str(_FONTS / "Inter-Regular.ttf"), 9)
    f_header  = ImageFont.truetype(str(_FONTS / "Inter-Bold.ttf"), 12)
    f_date    = ImageFont.truetype(str(_FONTS / "Inter-Regular.ttf"), 11)
    f_temp    = ImageFont.truetype(str(_FONTS / "Inter-Bold.ttf"), 52)
    f_sub     = ImageFont.truetype(str(_FONTS / "Inter-Regular.ttf"), 13)
    f_forecast= ImageFont.truetype(str(_FONTS / "Inter-Regular.ttf"), 13)
    f_quote   = ImageFont.truetype(str(_FONTS / "Inter-Italic.ttf"), 17)
    f_author  = ImageFont.truetype(str(_FONTS / "Inter-Regular.ttf"), 14)

    # ── Header ────────────────────────────────────────────────────────────────
    header_text_y = PAD + 10
    draw.text((PAD, header_text_y), "JDU DASHBOARD", font=f_header, fill=TEXT_DARK)

    now = datetime.now()
    date_str = now.strftime("%A · %B %-d, %Y · %-I:%M %p")
    draw.text((W - PAD, header_text_y), date_str, font=f_date, fill=TEXT_LIGHT, anchor="ra")

    border_y = PAD + 36
    draw.line([(PAD, border_y), (W - PAD, border_y)], fill=TEXT_DARK, width=2)

    # ── Panel geometry ────────────────────────────────────────────────────────
    content_y = border_y + 10
    content_h = H - content_y - PAD
    usable_w  = W - 2 * PAD - GAP
    weather_w = round(usable_w * 1.4 / 3.0)
    quote_w   = usable_w - weather_w

    wx = PAD
    qx = PAD + weather_w + GAP

    # ── Weather panel ─────────────────────────────────────────────────────────
    draw.rounded_rectangle(
        [wx, content_y, wx + weather_w, content_y + content_h],
        radius=8, fill=WEATHER_BG,
    )

    wp = 14   # inner padding
    cy = content_y + wp

    draw.text((wx + wp, cy), "TODAY'S WEATHER", font=f_label, fill=TEXT_LIGHT)
    cy += 18

    # Icon + temperature
    icon_size = 80
    if icon:
        icon_rgba = icon.resize((icon_size, icon_size), Image.LANCZOS)
        img.paste(icon_rgba, (wx + wp, cy), icon_rgba)
    tx = wx + wp + icon_size + 10
    draw.text((tx, cy), f"{weather.temperature}°F", font=f_temp, fill=TEMP_COLOR)
    draw.text((tx, cy + 56), f"{weather.period_name} · {weather.precip_percent}% precip",
              font=f_sub, fill=TEXT_LIGHT)
    cy += icon_size + 12

    # Forecast box (pinned to bottom of weather panel)
    box_h     = content_h - (cy - content_y) - wp
    box_y     = content_y + content_h - wp - box_h
    draw.rounded_rectangle(
        [wx + wp, box_y, wx + weather_w - wp, box_y + box_h],
        radius=5, fill=FORECAST_BG,
    )
    inner_w = weather_w - 2 * wp - 20
    lines = wrap_text(draw, weather.detailed_forecast, f_forecast, inner_w)
    ty = box_y + 10
    for line in lines[:5]:
        draw.text((wx + wp + 10, ty), line, font=f_forecast, fill=TEXT_MID)
        ty += 19

    # ── Quote panel ───────────────────────────────────────────────────────────
    draw.rounded_rectangle(
        [qx, content_y, qx + quote_w, content_y + content_h],
        radius=8, fill=QUOTE_BG, outline=BORDER_COLOR, width=1,
    )

    qp = 14
    qy = content_y + qp
    draw.text((qx + qp, qy), "QUOTE", font=f_label, fill=TEXT_LIGHT)
    qy += 18

    # Vertically center quote text
    quote_text  = f'"{quote.text}"'
    max_qw      = quote_w - 2 * qp
    q_lines     = wrap_text(draw, quote_text, f_quote, max_qw)
    line_h      = 26
    author_h    = 30
    total_text_h = len(q_lines) * line_h + author_h
    remaining   = content_h - 2 * qp - 18
    start_y     = qy + max(0, (remaining - total_text_h) // 2)

    for line in q_lines:
        draw.text((qx + qp, start_y), line, font=f_quote, fill=TEXT_MID)
        start_y += line_h

    start_y += 12
    draw.text(
        (qx + quote_w - qp, start_y),
        f"— {quote.author}",
        font=f_author,
        fill=TEXT_LIGHT,
        anchor="ra",
    )

    return img
```

- [ ] **Step 4: Run to confirm pass**

```bash
pytest tests/test_render_joe.py -v
```

Expected: 4 tests `PASSED`

- [ ] **Step 5: Commit**

```bash
git add app/render_joe.py tests/test_render_joe.py
git commit -m "feat: add Joe 800x480 dashboard renderer"
```

---

## Task 9: Sam Renderer (600×400)

**Files:**
- Create: `eink-dashboard/app/render_sam.py`
- Create: `eink-dashboard/tests/test_render_sam.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_render_sam.py
from PIL import Image
from app.render_sam import render_sam


def test_render_sam_correct_size(sample_weather, sample_quote, sample_icon):
    img = render_sam(sample_weather, sample_quote, sample_icon)
    assert img.size == (600, 400)


def test_render_sam_returns_rgb(sample_weather, sample_quote, sample_icon):
    img = render_sam(sample_weather, sample_quote, sample_icon)
    assert img.mode == "RGB"


def test_render_sam_not_blank(sample_weather, sample_quote, sample_icon):
    img = render_sam(sample_weather, sample_quote, sample_icon)
    pixels = list(img.getdata())
    assert len(set(pixels)) > 1, "Image appears blank — nothing was drawn"


def test_render_sam_works_without_icon(sample_weather, sample_quote):
    img = render_sam(sample_weather, sample_quote, icon=None)
    assert img.size == (600, 400)
```

- [ ] **Step 2: Run to confirm failure**

```bash
pytest tests/test_render_sam.py -v
```

Expected: `ImportError: cannot import name 'render_sam'`

- [ ] **Step 3: Implement render_sam.py**

```python
# app/render_sam.py
from __future__ import annotations
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from app.draw_utils import wrap_text
from app.weather import WeatherData
from app.quotes import QuoteData

_ASSETS = Path(__file__).parent.parent / "assets"
_FONTS  = _ASSETS / "fonts"

# Dimensions
W, H = 600, 400
PAD  = 14
GAP  = 12

# Colors (Sam: lavender/purple theme)
BG           = "#f7f4fd"
WEATHER_BG   = "#ede7f6"
FORECAST_BG  = "#ede7f6"
ACCENT       = "#6d3bbf"
TEXT_DARK    = "#1e1030"
TEXT_MID     = "#374151"
TEXT_LIGHT   = "#9e8ec0"
DIVIDER      = "#d8ccf0"


def render_sam(
    weather: WeatherData,
    quote: QuoteData,
    icon: Image.Image | None,
) -> Image.Image:
    img  = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    f_header  = ImageFont.truetype(str(_FONTS / "Inter-Regular.ttf"), 9)
    f_label   = ImageFont.truetype(str(_FONTS / "Inter-Regular.ttf"), 9)
    f_temp    = ImageFont.truetype(str(_FONTS / "Inter-Bold.ttf"), 38)
    f_sub     = ImageFont.truetype(str(_FONTS / "Inter-Regular.ttf"), 11)
    f_forecast= ImageFont.truetype(str(_FONTS / "Inter-Regular.ttf"), 11)
    f_quote   = ImageFont.truetype(str(_FONTS / "Inter-Italic.ttf"), 15)
    f_author  = ImageFont.truetype(str(_FONTS / "Inter-Regular.ttf"), 12)

    # ── Header ────────────────────────────────────────────────────────────────
    now = datetime.now()
    header = (
        f"JOY OF MY LIFE  ·  "
        f"{now.strftime('%A, %B %-d')}  ·  {now.strftime('%-I:%M %p')}"
    )
    draw.text((W // 2, PAD + 4), header, font=f_header, fill=TEXT_LIGHT, anchor="ma")

    content_y = PAD + 20
    content_h = H - content_y - PAD

    # ── Column geometry ───────────────────────────────────────────────────────
    usable_w = W - 2 * PAD - GAP
    quote_w  = round(usable_w * 1.5 / 2.5)
    weather_w = usable_w - quote_w

    quote_x   = PAD
    weather_x = PAD + quote_w + GAP

    # ── Quote panel (left) ────────────────────────────────────────────────────
    qp = 12
    draw.text((quote_x + qp, content_y + qp), "TODAY'S THOUGHT",
              font=f_label, fill=ACCENT)

    # Vertical divider
    div_x = quote_x + quote_w + GAP // 2
    draw.line([(div_x, content_y), (div_x, content_y + content_h)],
              fill=DIVIDER, width=2)

    # Vertically center quote text
    quote_text  = f'"{quote.text}"'
    max_qw      = quote_w - 2 * qp
    q_lines     = wrap_text(draw, quote_text, f_quote, max_qw)
    line_h      = 22
    author_h    = 28
    total_h     = len(q_lines) * line_h + author_h
    label_offset = 24
    remaining   = content_h - label_offset - 2 * qp
    start_y     = content_y + qp + label_offset + max(0, (remaining - total_h) // 2)

    for line in q_lines:
        draw.text((quote_x + qp, start_y), line, font=f_quote, fill=TEXT_DARK)
        start_y += line_h

    start_y += 10
    draw.text(
        (quote_x + quote_w - qp, start_y),
        f"— {quote.author}",
        font=f_author,
        fill=TEXT_LIGHT,
        anchor="ra",
    )

    # ── Weather panel (right) ─────────────────────────────────────────────────
    wp = 10
    draw.text((weather_x + wp, content_y + wp), "WEATHER",
              font=f_label, fill=ACCENT)

    # Icon
    icon_size = 64
    icon_y    = content_y + wp + 20
    if icon:
        icon_rgba = icon.resize((icon_size, icon_size), Image.LANCZOS)
        icon_cx   = weather_x + wp + (weather_w - 2 * wp - icon_size) // 2
        img.paste(icon_rgba, (icon_cx, icon_y), icon_rgba)

    # Temperature
    temp_y = icon_y + icon_size + 4
    draw.text(
        (weather_x + weather_w // 2 + wp // 2, temp_y),
        f"{weather.temperature}°F",
        font=f_temp,
        fill=ACCENT,
        anchor="ma",
    )
    draw.text(
        (weather_x + weather_w // 2 + wp // 2, temp_y + 46),
        weather.period_name,
        font=f_sub,
        fill=TEXT_LIGHT,
        anchor="ma",
    )

    # Forecast box
    box_y = content_y + content_h - 80 - wp
    draw.rounded_rectangle(
        [weather_x + wp, box_y, weather_x + weather_w - wp, content_y + content_h - wp],
        radius=5, fill=WEATHER_BG,
    )
    inner_w = weather_w - 2 * wp - 16
    lines   = wrap_text(draw, weather.short_forecast, f_forecast, inner_w)
    ty      = box_y + 8
    for line in lines[:3]:
        draw.text((weather_x + wp + 8, ty), line, font=f_forecast, fill=TEXT_MID)
        ty += 17

    precip_line = f"{weather.precip_percent}% precip"
    draw.text((weather_x + wp + 8, ty), precip_line, font=f_forecast, fill=TEXT_LIGHT)

    return img
```

- [ ] **Step 4: Run to confirm pass**

```bash
pytest tests/test_render_sam.py -v
```

Expected: 4 tests `PASSED`

- [ ] **Step 5: Commit**

```bash
git add app/render_sam.py tests/test_render_sam.py
git commit -m "feat: add Sam 600x400 dashboard renderer"
```

---

## Task 10: Cache Module

**Files:**
- Create: `eink-dashboard/app/cache.py`
- Create: `eink-dashboard/tests/test_cache.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_cache.py
from PIL import Image
from app.cache import DashboardCache


def _make_img(w: int, h: int, color: str = "red") -> Image.Image:
    return Image.new("RGB", (w, h), color)


def test_get_joe_returns_fallback_when_empty():
    cache = DashboardCache()
    png = cache.get_joe()
    assert isinstance(png, bytes)
    assert len(png) > 0


def test_get_sam_returns_fallback_when_empty():
    cache = DashboardCache()
    png = cache.get_sam()
    assert isinstance(png, bytes)
    assert len(png) > 0


def test_store_and_retrieve():
    cache = DashboardCache()
    joe_img = _make_img(800, 480, "blue")
    sam_img = _make_img(600, 400, "green")
    cache.store(joe_img, sam_img)
    assert cache.joe_png is not None
    assert cache.sam_png is not None
    assert cache.last_refresh is not None


def test_get_returns_stored_bytes_after_store():
    cache = DashboardCache()
    joe_img = _make_img(800, 480)
    sam_img = _make_img(600, 400)
    cache.store(joe_img, sam_img)
    joe_bytes = cache.get_joe()
    sam_bytes = cache.get_sam()
    # Re-open and check sizes
    from io import BytesIO
    assert Image.open(BytesIO(joe_bytes)).size == (800, 480)
    assert Image.open(BytesIO(sam_bytes)).size == (600, 400)
```

- [ ] **Step 2: Run to confirm failure**

```bash
pytest tests/test_cache.py -v
```

Expected: `ImportError: cannot import name 'DashboardCache'`

- [ ] **Step 3: Implement cache.py**

```python
# app/cache.py
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from io import BytesIO

from PIL import Image, ImageDraw, ImageFont


@dataclass
class DashboardCache:
    joe_png: bytes | None = field(default=None)
    sam_png: bytes | None = field(default=None)
    last_refresh: datetime | None = field(default=None)
    noaa_ok: bool = False
    quotes_ok: bool = False

    def store(self, joe: Image.Image, sam: Image.Image) -> None:
        self.joe_png = _to_png_bytes(joe)
        self.sam_png = _to_png_bytes(sam)
        self.last_refresh = datetime.utcnow()

    def get_joe(self) -> bytes:
        return self.joe_png if self.joe_png is not None else _fallback_png(800, 480)

    def get_sam(self) -> bytes:
        return self.sam_png if self.sam_png is not None else _fallback_png(600, 400)


def _to_png_bytes(img: Image.Image) -> bytes:
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _fallback_png(width: int, height: int) -> bytes:
    img  = Image.new("RGB", (width, height), "#f8f9fa")
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default()
    draw.text(
        (width // 2, height // 2),
        "Dashboard starting…",
        fill="#6c757d",
        font=font,
        anchor="mm",
    )
    return _to_png_bytes(img)


# Module-level singleton
cache = DashboardCache()
```

- [ ] **Step 4: Run to confirm pass**

```bash
pytest tests/test_cache.py -v
```

Expected: 4 tests `PASSED`

- [ ] **Step 5: Commit**

```bash
git add app/cache.py tests/test_cache.py
git commit -m "feat: add in-memory PNG cache with fallback"
```

---

## Task 11: Scheduler + Refresh Job

**Files:**
- Create: `eink-dashboard/app/scheduler.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_scheduler.py  (create this file)
import pytest
import respx
import httpx
from unittest.mock import AsyncMock, patch, MagicMock
from app.scheduler import refresh_dashboard
from app.cache import DashboardCache

NOAA_RESPONSE = {
    "properties": {"periods": [{
        "name": "Today", "temperature": 91,
        "shortForecast": "Sunny",
        "detailedForecast": "Sunny. High near 91.",
        "probabilityOfPrecipitation": {"value": 3},
    }]}
}
QUOTE_RESPONSE = [{"q": "Test quote.", "a": "Test Author"}]
MOCK_SVG = b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><rect width="100" height="100" fill="orange"/></svg>'


@respx.mock
async def test_refresh_dashboard_populates_cache():
    test_cache = DashboardCache()

    respx.get("https://api.weather.gov/gridpoints/PSR/166,61/forecast").mock(
        return_value=httpx.Response(200, json=NOAA_RESPONSE)
    )
    respx.get("https://zenquotes.io/api/random").mock(
        return_value=httpx.Response(200, json=QUOTE_RESPONSE)
    )
    # Mock all icon SVG fetches
    respx.get(respx.pattern.M(r"https://raw\.githubusercontent\.com/basmilius/weather-icons/.*")).mock(
        return_value=httpx.Response(200, content=MOCK_SVG)
    )

    await refresh_dashboard(cache=test_cache, noaa_grid="PSR/166,61")

    assert test_cache.joe_png is not None
    assert test_cache.sam_png is not None
    assert test_cache.noaa_ok is True
    assert test_cache.quotes_ok is True


@respx.mock
async def test_refresh_keeps_old_cache_on_noaa_failure():
    from PIL import Image
    test_cache = DashboardCache()
    # Pre-populate with a known image
    old_joe = Image.new("RGB", (800, 480), "red")
    old_sam = Image.new("RGB", (600, 400), "green")
    test_cache.store(old_joe, old_sam)
    old_joe_bytes = test_cache.joe_png

    respx.get("https://api.weather.gov/gridpoints/PSR/166,61/forecast").mock(
        return_value=httpx.Response(500)
    )
    respx.get("https://zenquotes.io/api/random").mock(
        return_value=httpx.Response(200, json=QUOTE_RESPONSE)
    )

    await refresh_dashboard(cache=test_cache, noaa_grid="PSR/166,61")

    # Cache should be unchanged
    assert test_cache.joe_png == old_joe_bytes
    assert test_cache.noaa_ok is False
```

- [ ] **Step 2: Run to confirm failure**

```bash
pytest tests/test_scheduler.py -v
```

Expected: `ImportError: cannot import name 'refresh_dashboard'`

- [ ] **Step 3: Implement scheduler.py**

```python
# app/scheduler.py
from __future__ import annotations
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.cache import DashboardCache, cache as _default_cache
from app.icons import load_all_icons, select_icon_name
from app.quotes import fetch_quote
from app.render_joe import render_joe
from app.render_sam import render_sam
from app.weather import fetch_weather

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()

# Icons loaded once and reused across refreshes
_icons: dict = {}


async def refresh_dashboard(
    cache: DashboardCache = _default_cache,
    noaa_grid: str = "PSR/166,61",
) -> None:
    global _icons

    weather = None
    quote = None

    try:
        weather = await fetch_weather(noaa_grid)
        cache.noaa_ok = True
    except Exception as exc:
        logger.warning("NOAA fetch failed: %s", exc)
        cache.noaa_ok = False

    try:
        quote = await fetch_quote()
        cache.quotes_ok = True
    except Exception as exc:
        logger.warning("ZenQuotes fetch failed: %s", exc)
        cache.quotes_ok = False

    if weather is None or quote is None:
        logger.warning("Skipping render — keeping previous cache intact")
        return

    if not _icons:
        logger.info("Loading and rasterizing weather icons…")
        _icons = await load_all_icons(size=120)

    icon_name = select_icon_name(weather.short_forecast, weather.period_name)
    icon = _icons.get(icon_name)

    joe_img = render_joe(weather, quote, icon)
    sam_img = render_sam(weather, quote, icon)
    cache.store(joe_img, sam_img)
    logger.info("Dashboard refreshed at %s", cache.last_refresh)


def start_scheduler(noaa_grid: str = "PSR/166,61") -> None:
    scheduler.add_job(
        refresh_dashboard,
        CronTrigger(minute=0),
        kwargs={"noaa_grid": noaa_grid},
        id="refresh_dashboard",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Scheduler started — dashboard refreshes at the top of every hour")
```

- [ ] **Step 4: Run to confirm pass**

```bash
pytest tests/test_scheduler.py -v
```

Expected: 2 tests `PASSED`

- [ ] **Step 5: Commit**

```bash
git add app/scheduler.py tests/test_scheduler.py
git commit -m "feat: add APScheduler refresh job with error isolation"
```

---

## Task 12: FastAPI App + Routes

**Files:**
- Create: `eink-dashboard/app/main.py`
- Create: `eink-dashboard/tests/test_api.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_api.py
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from PIL import Image
from io import BytesIO
from app.cache import DashboardCache


def _png_bytes(w: int, h: int, color: str = "blue") -> bytes:
    buf = BytesIO()
    Image.new("RGB", (w, h), color).save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture
def client():
    test_cache = DashboardCache()
    test_cache.joe_png = _png_bytes(800, 480)
    test_cache.sam_png = _png_bytes(600, 400)

    with patch("app.main.cache", test_cache), \
         patch("app.main.refresh_dashboard", new_callable=AsyncMock), \
         patch("app.main.start_scheduler"):
        from app.main import app
        with TestClient(app) as c:
            yield c


def test_joe_endpoint_returns_png(client):
    resp = client.get("/dashboard/joe.png")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "image/png"
    img = Image.open(BytesIO(resp.content))
    assert img.size == (800, 480)


def test_sam_endpoint_returns_png(client):
    resp = client.get("/dashboard/sam.png")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "image/png"
    img = Image.open(BytesIO(resp.content))
    assert img.size == (600, 400)


def test_health_endpoint(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert "last_refresh" in data
    assert "noaa_ok" in data
    assert "quotes_ok" in data


def test_unknown_route_returns_404(client):
    resp = client.get("/nonexistent")
    assert resp.status_code == 404
```

- [ ] **Step 2: Run to confirm failure**

```bash
pytest tests/test_api.py -v
```

Expected: `ImportError: cannot import name 'app'` from app.main

- [ ] **Step 3: Implement main.py**

```python
# app/main.py
from __future__ import annotations
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse, Response

from app.cache import cache
from app.config import settings
from app.scheduler import refresh_dashboard, start_scheduler, scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await refresh_dashboard(cache=cache, noaa_grid=settings.noaa_grid)
    start_scheduler(noaa_grid=settings.noaa_grid)
    yield
    scheduler.shutdown(wait=False)


app = FastAPI(title="InkyDashboard", lifespan=lifespan)


@app.get("/dashboard/joe.png")
async def joe_dashboard() -> Response:
    return Response(content=cache.get_joe(), media_type="image/png")


@app.get("/dashboard/sam.png")
async def sam_dashboard() -> Response:
    return Response(content=cache.get_sam(), media_type="image/png")


@app.get("/health")
async def health() -> JSONResponse:
    return JSONResponse({
        "last_refresh": cache.last_refresh.isoformat() if cache.last_refresh else None,
        "noaa_ok": cache.noaa_ok,
        "quotes_ok": cache.quotes_ok,
    })
```

- [ ] **Step 4: Run to confirm pass**

```bash
pytest tests/test_api.py -v
```

Expected: 4 tests `PASSED`

- [ ] **Step 5: Run full test suite**

```bash
pytest -v
```

Expected: all tests `PASSED`

- [ ] **Step 6: Commit**

```bash
git add app/main.py tests/test_api.py
git commit -m "feat: add FastAPI routes and lifespan startup"
```

---

## Task 13: Docker

**Files:**
- Create: `eink-dashboard/Dockerfile`
- Create: `eink-dashboard/docker-compose.yml`

- [ ] **Step 1: Write Dockerfile**

```dockerfile
# Dockerfile
FROM python:3.12-slim

# cairosvg requires libcairo2
RUN apt-get update && apt-get install -y --no-install-recommends \
    libcairo2 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY assets/ ./assets/

ENV PORT=8000

EXPOSE 8000

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
```

- [ ] **Step 2: Write docker-compose.yml**

```yaml
# docker-compose.yml
services:
  inkydashboard:
    build: .
    restart: unless-stopped
    ports:
      - "8000:8000"
    environment:
      PORT: 8000
      NOAA_GRID: PSR/166,61
      REFRESH_HOUR_INTERVAL: 1
```

- [ ] **Step 3: Build and verify**

```bash
cd eink-dashboard
docker build -t inkydashboard .
```

Expected: build succeeds, image created

- [ ] **Step 4: Run container and smoke-test**

```bash
docker run -d -p 8000:8000 --name inkydash-test inkydashboard
sleep 30   # wait for startup refresh
curl -s -o /tmp/joe.png http://localhost:8000/dashboard/joe.png
curl -s http://localhost:8000/health
```

Expected:
- `/tmp/joe.png` is a valid PNG file (`file /tmp/joe.png` → `PNG image data, 800 x 480`)
- `/health` returns JSON with `noaa_ok: true` and `quotes_ok: true`

- [ ] **Step 5: Stop and clean up test container**

```bash
docker stop inkydash-test && docker rm inkydash-test
```

- [ ] **Step 6: Commit**

```bash
git add Dockerfile docker-compose.yml
git commit -m "feat: add Dockerfile and docker-compose for Synology deployment"
```

---

## Task 14: Pi-Side Script Update

**Files:**
- Create: `eink-dashboard/scripts/dailyDash.sh`

- [ ] **Step 1: Write the new dailyDash.sh**

Replace `as-is/scripts/dailyDash.sh` on the Pi. The Synology hostname/IP should match your local network — replace `synology` with the actual IP or hostname.

```bash
#!/bin/bash
# scripts/dailyDash.sh
# Fetches the pre-rendered dashboard PNG from the FastAPI server and displays it.
# killFirefox.sh is no longer needed.

set -e

SERVER="http://synology:8000"
PROFILE="joe"   # change to "sam" for Sam's display
TMP_PNG="/tmp/dashboard.png"

curl -sf "${SERVER}/dashboard/${PROFILE}.png" -o "${TMP_PNG}"

/home/red/Dev/scripts/dailyClear.py
/home/red/Dev/scripts/dailyEink.py "${TMP_PNG}"

rm -f "${TMP_PNG}"
```

- [ ] **Step 2: Make it executable and commit**

```bash
chmod +x scripts/dailyDash.sh
git add scripts/dailyDash.sh
git commit -m "feat: simplified Pi dailyDash.sh — curl instead of Firefox screenshot"
```

- [ ] **Step 3: Copy to Pi and test**

On the Mac:
```bash
scp scripts/dailyDash.sh red@10.0.10.17:/home/red/Dev/scripts/dailyDash.sh
```

On the Pi (after the Docker container is running on Synology):
```bash
ssh red@10.0.10.17
bash /home/red/Dev/scripts/dailyDash.sh
```

Expected: display clears, dashboard appears on the e-ink screen.

---

## Self-Review

**Spec coverage check:**
- ✅ FastAPI server with 3 endpoints (`/dashboard/joe.png`, `/dashboard/sam.png`, `/health`)
- ✅ APScheduler hourly at `:00` with `CronTrigger(minute=0)`
- ✅ NOAA weather fetch with all required fields
- ✅ ZenQuotes random quote fetch
- ✅ Basmilius SVG rasterization via cairosvg
- ✅ Full 18-condition icon mapping (first-match-wins)
- ✅ Joe layout: 800×480, side-by-side, white/blue colors
- ✅ Sam layout: 600×400, warm split, lavender/purple colors
- ✅ In-memory cache with fallback PNG on first-boot failure
- ✅ Error isolation: failed API keeps previous cache, logs warning
- ✅ Docker: python:3.12-slim + libcairo2, port 8000, env vars
- ✅ Pi script simplified to curl + clear + display
- ✅ Inter fonts bundled (Regular, Bold, Italic)

**Type consistency check:**
- `refresh_dashboard(cache, noaa_grid)` — matches usage in `main.py` lifespan and test
- `DashboardCache.store(joe_img, sam_img)` — matches scheduler call
- `render_joe(weather, quote, icon)` / `render_sam(weather, quote, icon)` — consistent signatures
- `WeatherData` and `QuoteData` dataclasses — used consistently across all modules
- `select_icon_name(short_forecast, period_name)` — matches scheduler call

**No placeholders found.**
