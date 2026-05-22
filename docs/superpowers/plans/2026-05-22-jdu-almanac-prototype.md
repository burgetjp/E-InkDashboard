# JDU Almanac Prototype Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add four "JDU Almanac" prototype dashboard variants (Classic/Modern × paper/inverted) served under `/proto/` without touching any production endpoints.

**Architecture:** A new `proto_router.py` FastAPI router with 4 endpoints, backed by a single `render_almanac.py` renderer that accepts `variant` and `inverted` params. Four new slots are added to `DashboardCache` and populated alongside the existing production renders on the hourly scheduler tick.

**Tech Stack:** FastAPI, Pillow (PIL), APScheduler, pytest, variable-weight TTF fonts (Playfair Display, Source Serif 4, JetBrains Mono) already in `assets/fonts/`.

---

## File Map

| File | Action | Responsibility |
|------|--------|----------------|
| `app/render_almanac.py` | **Create** | All drawing logic for all 4 variants |
| `app/proto_router.py` | **Create** | 4 FastAPI endpoints under `/proto/` |
| `app/cache.py` | **Modify** | Add 4 almanac slots + `store_almanac` / `get_almanac` |
| `app/scheduler.py` | **Modify** | Render 4 variants during hourly refresh |
| `app/main.py` | **Modify** | Include proto_router |
| `tests/test_render_almanac.py` | **Create** | Renderer unit tests |
| `tests/test_cache.py` | **Modify** | Tests for new cache methods |
| `tests/test_main.py` | **Modify** | Tests for `/proto/*` endpoints |

---

## Task 1: Extend DashboardCache with almanac slots

**Files:**
- Modify: `app/cache.py`
- Modify: `tests/test_cache.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_cache.py`:

```python
def test_almanac_slots_start_empty():
    c = DashboardCache()
    assert c.almanac_classic is None
    assert c.almanac_classic_inv is None
    assert c.almanac_modern is None
    assert c.almanac_modern_inv is None


def test_store_almanac_and_retrieve():
    c = DashboardCache()
    classic = _make_png("red")
    classic_inv = _make_png("yellow")
    modern = _make_png("black")
    modern_inv = _make_png("white")
    c.store_almanac(classic, classic_inv, modern, modern_inv)
    assert c.get_almanac("classic") == classic
    assert c.get_almanac("classic-inv") == classic_inv
    assert c.get_almanac("modern") == modern
    assert c.get_almanac("modern-inv") == modern_inv


def test_get_almanac_fallback_when_empty():
    c = DashboardCache()
    result = c.get_almanac("classic")
    assert isinstance(result, bytes)
    img = Image.open(io.BytesIO(result))
    assert img.size == (800, 480)


def test_get_almanac_unknown_variant_returns_fallback():
    c = DashboardCache()
    result = c.get_almanac("nonexistent")
    assert isinstance(result, bytes)
```

- [ ] **Step 2: Run to confirm failure**

```
venv/bin/pytest tests/test_cache.py -v -k almanac
```
Expected: 4 errors — `DashboardCache` has no almanac attributes.

- [ ] **Step 3: Implement the changes in `app/cache.py`**

Add four `Optional[bytes]` fields to `DashboardCache` and the two new methods. Full updated file:

```python
from __future__ import annotations

import io
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from PIL import Image, ImageDraw, ImageFont


def _make_fallback_png(width: int, height: int, message: str) -> bytes:
    img = Image.new("RGB", (width, height), "#f8f9fa")
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.load_default()
    except Exception:
        font = None
    draw.text((width // 2, height // 2), message, fill="#6c757d", anchor="mm", font=font)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@dataclass
class DashboardCache:
    joe_png: Optional[bytes] = field(default=None)
    sam_png: Optional[bytes] = field(default=None)
    almanac_classic: Optional[bytes] = field(default=None)
    almanac_classic_inv: Optional[bytes] = field(default=None)
    almanac_modern: Optional[bytes] = field(default=None)
    almanac_modern_inv: Optional[bytes] = field(default=None)
    last_refresh: Optional[datetime] = field(default=None)
    noaa_ok: bool = False
    quotes_ok: bool = False

    def store(self, joe: bytes, sam: bytes, *, noaa_ok: bool, quotes_ok: bool) -> None:
        self.joe_png = joe
        self.sam_png = sam
        self.last_refresh = datetime.now()
        self.noaa_ok = noaa_ok
        self.quotes_ok = quotes_ok

    def store_almanac(
        self,
        classic: bytes,
        classic_inv: bytes,
        modern: bytes,
        modern_inv: bytes,
    ) -> None:
        self.almanac_classic = classic
        self.almanac_classic_inv = classic_inv
        self.almanac_modern = modern
        self.almanac_modern_inv = modern_inv

    def get_joe(self) -> bytes:
        if self.joe_png is None:
            return _make_fallback_png(800, 480, "Dashboard starting…")
        return self.joe_png

    def get_sam(self) -> bytes:
        if self.sam_png is None:
            return _make_fallback_png(600, 400, "Dashboard starting…")
        return self.sam_png

    def get_almanac(self, variant: str) -> bytes:
        data = {
            "classic": self.almanac_classic,
            "classic-inv": self.almanac_classic_inv,
            "modern": self.almanac_modern,
            "modern-inv": self.almanac_modern_inv,
        }.get(variant)
        if data is None:
            return _make_fallback_png(800, 480, "Almanac starting…")
        return data


cache = DashboardCache()
```

- [ ] **Step 4: Run all cache tests**

```
venv/bin/pytest tests/test_cache.py -v
```
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add app/cache.py tests/test_cache.py
git commit -m "feat: add almanac slots to DashboardCache"
```

---

## Task 2: Core helpers in render_almanac.py

Create `app/render_almanac.py` with constants, font loader, color resolver, and Roman numeral helper. Create `tests/test_render_almanac.py`.

**Files:**
- Create: `app/render_almanac.py`
- Create: `tests/test_render_almanac.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_render_almanac.py` — include **all imports the full test file will ever need** up front:

```python
import io
import math
import pytest
from PIL import Image, ImageDraw, ImageFont

from app.render_almanac import (
    _vfont, _colors, _roman_year,
    _draw_masthead, _draw_colophon, _draw_dateband,
    _draw_weather_panel, _draw_quote_panel,
    render_almanac,
    PLAYFAIR, JETBRAINS,
    W, H,
)
from app.weather import WeatherData
from app.quotes import QuoteData


# Shared helper used throughout the test file
def _blank_draw():
    img = Image.new("RGB", (W, H), "#f6f3ea")
    return img, ImageDraw.Draw(img)

# --- _roman_year ---

def test_roman_year_2026():
    assert _roman_year(2026) == "MMXXVI"

def test_roman_year_2025():
    assert _roman_year(2025) == "MMXXV"

def test_roman_year_2000():
    assert _roman_year(2000) == "MM"

# --- _colors ---

def test_colors_classic_paper():
    bg, fg, accent = _colors("classic", False)
    assert bg == "#f6f3ea"
    assert fg == "#0c0c0c"
    assert accent == "#c01818"

def test_colors_classic_inverted():
    bg, fg, accent = _colors("classic", True)
    assert bg == "#0c0c0c"
    assert fg == "#f6f3ea"
    assert accent == "#f2c200"

def test_colors_modern_paper():
    bg, fg, accent = _colors("modern", False)
    assert bg == "#f6f3ea"
    assert fg == "#0c0c0c"
    assert accent == "#0c0c0c"

def test_colors_modern_inverted():
    bg, fg, accent = _colors("modern", True)
    assert bg == "#0c0c0c"
    assert fg == "#f6f3ea"
    assert accent == "#f6f3ea"

# --- _vfont ---

def test_vfont_returns_freetype_font():
    font = _vfont(PLAYFAIR, 40, 900)
    assert isinstance(font, ImageFont.FreeTypeFont)

def test_vfont_jetbrains_regular():
    font = _vfont(JETBRAINS, 13, 400)
    assert isinstance(font, ImageFont.FreeTypeFont)
```

- [ ] **Step 2: Run to confirm failure**

```
venv/bin/pytest tests/test_render_almanac.py -v
```
Expected: ImportError — `app.render_almanac` doesn't exist.

- [ ] **Step 3: Create `app/render_almanac.py` with helpers only**

```python
from __future__ import annotations

import io
import math
import os
from datetime import datetime
from zoneinfo import ZoneInfo

from PIL import Image, ImageDraw, ImageFont

from app.draw_utils import wrap_text
from app.icons import select_icon_name
from app.weather import WeatherData
from app.quotes import QuoteData

# --- Canvas & zone constants ---
W, H = 800, 480
OUTER_BLEED = 6
FRAME_W = 2
PINSTRIPE_OFFSET = 4
MASTHEAD_H = 62
DATEBAND_H = 30
COLOPHON_H = 26
PAD = 12           # content padding inside border

INNER_X = OUTER_BLEED + FRAME_W   # = 8
CONTENT_X = INNER_X + PAD         # = 20
CONTENT_RIGHT = W - INNER_X - PAD # = 780
CONTENT_W = CONTENT_RIGHT - CONTENT_X  # = 760

MAST_Y = INNER_X                       # = 8
MAST_BOT = MAST_Y + MASTHEAD_H         # = 70
DATE_Y = MAST_BOT                      # = 70
DATE_BOT = DATE_Y + DATEBAND_H         # = 100
COLON_Y = H - INNER_X - COLOPHON_H    # = 446
COLON_BOT = H - INNER_X               # = 472
BODY_Y = DATE_BOT                      # = 100
BODY_H = COLON_Y - BODY_Y             # = 346

WX_W = CONTENT_W // 2                 # weather column width = 380
DIVIDER_X = CONTENT_X + WX_W          # = 400

# --- Palette tokens ---
INK = "#0c0c0c"
PAPER = "#f6f3ea"
RED = "#c01818"
YELLOW = "#f2c200"

# --- Static config ---
LOCATION_COORDS = "112°W · 34°N"   # Phoenix, AZ (33.5°N, -111.9°W)
VOL_LABEL = "Vol. III"
ISSUE_LABEL = "№ 142"

# --- Font paths ---
_FONT_DIR = os.path.join(os.path.dirname(__file__), "..", "assets", "fonts")
PLAYFAIR = os.path.join(_FONT_DIR, "PlayfairDisplay[wght].ttf")
PLAYFAIR_ITALIC = os.path.join(_FONT_DIR, "PlayfairDisplay-Italic[wght].ttf")
SOURCE_SERIF = os.path.join(_FONT_DIR, "SourceSerif4[opsz,wght].ttf")
SOURCE_SERIF_ITALIC = os.path.join(_FONT_DIR, "SourceSerif4-Italic[opsz,wght].ttf")
JETBRAINS = os.path.join(_FONT_DIR, "JetBrainsMono[wght].ttf")


def _vfont(path: str, size: int, weight: int = 400) -> ImageFont.FreeTypeFont:
    """Load a variable font and set its weight (and optical size if present)."""
    font = ImageFont.truetype(path, size)
    axes = font.get_variation_axes()
    vals = []
    for ax in axes:
        name = ax["name"]
        if name == b"Weight":
            vals.append(max(ax["minimum"], min(weight, ax["maximum"])))
        elif name == b"Optical Size":
            vals.append(max(ax["minimum"], min(float(size), ax["maximum"])))
        else:
            vals.append(ax["minimum"])
    font.set_variation_by_axes(vals)
    return font


def _colors(variant: str, inverted: bool) -> tuple[str, str, str]:
    """Return (bg, fg, accent) for the given variant and inversion."""
    bg = INK if inverted else PAPER
    fg = PAPER if inverted else INK
    if variant == "classic":
        accent = YELLOW if inverted else RED
    else:
        accent = PAPER if inverted else INK
    return bg, fg, accent


def _roman_year(year: int) -> str:
    """Convert a year to Roman numerals (e.g. 2026 → 'MMXXVI')."""
    vals = [
        (1000, "M"), (900, "CM"), (500, "D"), (400, "CD"),
        (100, "C"), (90, "XC"), (50, "L"), (40, "XL"),
        (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I"),
    ]
    result = ""
    for v, s in vals:
        while year >= v:
            result += s
            year -= v
    return result
```

- [ ] **Step 4: Run the helper tests**

```
venv/bin/pytest tests/test_render_almanac.py -v
```
Expected: all 10 pass.

- [ ] **Step 5: Commit**

```bash
git add app/render_almanac.py tests/test_render_almanac.py
git commit -m "feat: add render_almanac module with core helpers"
```

---

## Task 3: Draw masthead and colophon zones

**Files:**
- Modify: `app/render_almanac.py`
- Modify: `tests/test_render_almanac.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_render_almanac.py`:

```python
def test_draw_masthead_classic_does_not_raise():
    img, draw = _blank_draw()
    _draw_masthead(draw, "classic", "#0c0c0c", "#c01818")


def test_draw_masthead_modern_does_not_raise():
    img, draw = _blank_draw()
    _draw_masthead(draw, "modern", "#0c0c0c", "#0c0c0c")


def test_draw_colophon_classic_does_not_raise():
    img, draw = _blank_draw()
    _draw_colophon(draw, "classic", "#0c0c0c", "#c01818")


def test_draw_colophon_modern_does_not_raise():
    img, draw = _blank_draw()
    _draw_colophon(draw, "modern", "#0c0c0c", "#0c0c0c")
```

- [ ] **Step 2: Run to confirm failure**

```
venv/bin/pytest tests/test_render_almanac.py -v -k "masthead or colophon"
```
Expected: ImportError — `_draw_masthead` not defined.

- [ ] **Step 3: Add `_draw_masthead` and `_draw_colophon` to `app/render_almanac.py`**

Add these two functions after `_roman_year`:

```python
def _draw_masthead(
    draw: ImageDraw.ImageDraw,
    variant: str,
    fg: str,
    accent: str,
) -> None:
    """Draw Zone A: Masthead (~62px tall, starts at MAST_Y)."""
    cx = W // 2

    if variant == "classic":
        # Flanking ribbons
        f_ribbon = _vfont(JETBRAINS, 12, 400)
        draw.text((CONTENT_X, MAST_Y + 4), VOL_LABEL.upper(), font=f_ribbon, fill=accent)
        draw.text((CONTENT_RIGHT, MAST_Y + 4), ISSUE_LABEL, font=f_ribbon, fill=accent, anchor="rt")

        # Main title
        f_title = _vfont(PLAYFAIR, 38, 900)
        draw.text((cx, MAST_Y + 24), "The JDU Almanac", font=f_title, fill=fg, anchor="mt")

        # Italic subtitle
        f_sub = _vfont(PLAYFAIR_ITALIC, 14, 700)
        draw.text((cx, MAST_Y + 50), "— a daily dashboard of weather & thought —",
                  font=f_sub, fill=accent, anchor="mt")

    else:  # modern
        f_title = _vfont(PLAYFAIR, 34, 900)
        draw.text((CONTENT_X, MAST_Y + 16), "JDU Almanac", font=f_title, fill=fg, anchor="lt")


def _draw_colophon(
    draw: ImageDraw.ImageDraw,
    variant: str,
    fg: str,
    accent: str,
) -> None:
    """Draw Zone D: Colophon (~26px tall, starts at COLON_Y)."""
    f = _vfont(JETBRAINS, 11, 400)
    cy = COLON_Y + (COLOPHON_H - 14) // 2  # vertically centered

    # Top hairline
    draw.line([(CONTENT_X, COLON_Y), (CONTENT_RIGHT, COLON_Y)], fill=fg, width=2)

    draw.text((CONTENT_X, cy), "PRINTED IN INK", font=f, fill=fg)
    draw.text((CONTENT_RIGHT, cy), "INKY · 7.3″ · 800×480", font=f, fill=fg, anchor="rt")

    if variant == "classic":
        draw.text((W // 2, cy), "✦ ✦ ✦", font=f, fill=accent, anchor="mt")
```

- [ ] **Step 4: Run the tests**

```
venv/bin/pytest tests/test_render_almanac.py -v -k "masthead or colophon"
```
Expected: 4 pass.

- [ ] **Step 5: Commit**

```bash
git add app/render_almanac.py tests/test_render_almanac.py
git commit -m "feat: add _draw_masthead and _draw_colophon"
```

---

## Task 4: Draw dateband zone

**Files:**
- Modify: `app/render_almanac.py`
- Modify: `tests/test_render_almanac.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_render_almanac.py`:

```python
def test_draw_dateband_classic_does_not_raise():
    img, draw = _blank_draw()
    _draw_dateband(draw, "classic", "#0c0c0c", "#c01818")


def test_draw_dateband_modern_does_not_raise():
    img, draw = _blank_draw()
    _draw_dateband(draw, "modern", "#0c0c0c", "#0c0c0c")
```

- [ ] **Step 2: Run to confirm failure**

```
venv/bin/pytest tests/test_render_almanac.py -v -k "dateband"
```
Expected: ImportError — `_draw_dateband` not defined.

- [ ] **Step 3: Add `_draw_dateband` to `app/render_almanac.py`**

```python
def _draw_dateband(
    draw: ImageDraw.ImageDraw,
    variant: str,
    fg: str,
    accent: str,
) -> None:
    """Draw Zone B: Dateband (~30px tall, starts at DATE_Y)."""
    now = datetime.now(ZoneInfo("America/Phoenix"))
    day = now.strftime("%A").upper()
    month_day = now.strftime("%B %-d").upper()
    year_roman = _roman_year(now.year)

    f = _vfont(JETBRAINS, 13, 400)
    cy = DATE_Y + (DATEBAND_H - 16) // 2  # vertically centered

    # Border hairlines
    draw.line([(CONTENT_X, DATE_Y), (CONTENT_RIGHT, DATE_Y)], fill=fg, width=2)
    draw.line([(CONTENT_X, DATE_BOT - 1), (CONTENT_RIGHT, DATE_BOT - 1)], fill=fg, width=1)

    if variant == "classic":
        # Centered: "FRIDAY · MAY 22 · MMXXVI · 112°W · 34°N"
        # Draw dots in accent, text tokens in fg
        tokens = [day, f"{month_day} · {year_roman}", LOCATION_COORDS]
        sep = "  ·  "
        f_sep = _vfont(JETBRAINS, 13, 400)

        # Measure total width
        total_w = sum(draw.textbbox((0, 0), t, font=f)[2] for t in tokens)
        total_w += sum(draw.textbbox((0, 0), sep, font=f_sep)[2] for _ in range(len(tokens) - 1))
        sx = W // 2 - total_w // 2

        for i, token in enumerate(tokens):
            draw.text((sx, cy), token, font=f, fill=fg)
            sx += draw.textbbox((0, 0), token, font=f)[2]
            if i < len(tokens) - 1:
                draw.text((sx, cy), sep, font=f_sep, fill=accent)
                sx += draw.textbbox((0, 0), sep, font=f_sep)[2]

    else:  # modern: day left, date right, no coordinates
        date_str = f"{month_day} · {year_roman}"
        draw.text((CONTENT_X, cy), day, font=f, fill=fg)
        draw.text((CONTENT_RIGHT, cy), date_str, font=f, fill=fg, anchor="rt")
```

- [ ] **Step 4: Run the tests**

```
venv/bin/pytest tests/test_render_almanac.py -v -k "dateband"
```
Expected: 2 pass.

- [ ] **Step 5: Commit**

```bash
git add app/render_almanac.py tests/test_render_almanac.py
git commit -m "feat: add _draw_dateband"
```

---

## Task 5: Draw weather panel

**Files:**
- Modify: `app/render_almanac.py`
- Modify: `tests/test_render_almanac.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_render_almanac.py`. `sample_weather` and `blank_icon` come from `tests/conftest.py` — do not redefine them.

```python
def test_draw_weather_panel_does_not_raise(sample_weather, blank_icon):
    img, draw = _blank_draw()
    icons = {"clear-day": blank_icon}
    _draw_weather_panel(img, draw, sample_weather, icons,
                        x=20, y=100, w=380, h=346, fg="#0c0c0c", accent="#c01818")


def test_draw_weather_panel_missing_icon_does_not_raise(sample_weather):
    img, draw = _blank_draw()
    _draw_weather_panel(img, draw, sample_weather, {},
                        x=20, y=100, w=380, h=346, fg="#0c0c0c", accent="#c01818")


def test_draw_weather_panel_triple_digit_temp(sample_weather, blank_icon):
    img, draw = _blank_draw()
    icons = {"clear-day": blank_icon}
    sample_weather.temperature = 108
    _draw_weather_panel(img, draw, sample_weather, icons,
                        x=20, y=100, w=380, h=346, fg="#0c0c0c", accent="#c01818")
```

- [ ] **Step 2: Run to confirm failure**

```
venv/bin/pytest tests/test_render_almanac.py -v -k "weather_panel"
```
Expected: ImportError — `_draw_weather_panel` not defined.

- [ ] **Step 3: Add `_draw_weather_panel` to `app/render_almanac.py`**

```python
def _draw_weather_panel(
    img: Image.Image,
    draw: ImageDraw.ImageDraw,
    weather: WeatherData,
    icons: dict[str, Image.Image],
    *,
    x: int,
    y: int,
    w: int,
    h: int,
    fg: str,
    accent: str,
) -> None:
    """Draw Zone C/Left: Of the Weather."""
    pad = 12
    inner_x = x + pad
    inner_w = w - 2 * pad
    cy = y + pad

    # Section label + hairline
    f_label = _vfont(JETBRAINS, 13, 500)
    draw.text((inner_x, cy), "OF THE WEATHER", font=f_label, fill=accent)
    cy += 18
    draw.line([(inner_x, cy), (x + w - pad, cy)], fill=fg, width=1)
    cy += 10

    # Icon (70px, no circle — paste directly onto background)
    icon_size = 70
    icon_name = select_icon_name(weather.short_forecast, weather.period_name)
    raw = icons.get(icon_name) or icons.get("clear-day")
    if raw is None:
        raw = Image.new("RGBA", (icon_size, icon_size), (150, 150, 150, 255))
    icon_img = raw.resize((icon_size, icon_size), Image.LANCZOS)
    img.paste(icon_img, (inner_x, cy), icon_img)

    # Temperature alongside icon
    temp_x = inner_x + icon_size + 12
    f_temp = _vfont(SOURCE_SERIF, 120, 700)
    draw.text((temp_x, cy), str(weather.temperature), font=f_temp, fill=accent, anchor="lt")

    # Degree superscript (top-right of the temp digits)
    temp_bbox = draw.textbbox((temp_x, cy), str(weather.temperature), font=f_temp)
    f_deg = _vfont(SOURCE_SERIF, 40, 700)
    draw.text((temp_bbox[2] + 2, cy + 4), "°", font=f_deg, fill=accent, anchor="lt")

    cy += max(icon_size, 90) + 12  # advance past icon row (temp extends lower)

    # Stat line: "SUNNY · 3% RAIN"
    stat = f"{weather.short_forecast.upper()} · {weather.precip_percent}% RAIN"
    f_stat = _vfont(JETBRAINS, 13, 400)
    draw.text((inner_x, cy), stat, font=f_stat, fill=fg)
    cy += 22

    # Forecast description (italic, ~2 lines, truncated at 120 chars)
    desc = weather.detailed_forecast
    if len(desc) > 120:
        desc = desc[:117].rstrip() + "…"
    f_desc = _vfont(SOURCE_SERIF_ITALIC, 15, 400)
    desc_lines = wrap_text(draw, desc, f_desc, max_width=inner_w)
    for line in desc_lines[:3]:
        draw.text((inner_x, cy), line, font=f_desc, fill=fg)
        cy += 22
```

- [ ] **Step 4: Run the tests**

```
venv/bin/pytest tests/test_render_almanac.py -v -k "weather_panel"
```
Expected: 3 pass.

- [ ] **Step 5: Commit**

```bash
git add app/render_almanac.py tests/test_render_almanac.py
git commit -m "feat: add _draw_weather_panel"
```

---

## Task 6: Draw quote panel with drop-cap

**Files:**
- Modify: `app/render_almanac.py`
- Modify: `tests/test_render_almanac.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_render_almanac.py`. `sample_quote` comes from `tests/conftest.py` — do not redefine it.

```python
def test_draw_quote_panel_does_not_raise(sample_quote):
    img, draw = _blank_draw()
    _draw_quote_panel(draw, sample_quote,
                      x=401, y=100, w=379, h=346, fg="#0c0c0c", accent="#c01818")


def test_draw_quote_panel_long_quote_does_not_raise():
    img, draw = _blank_draw()
    long_q = QuoteData(
        text="A" * 200,
        author="Author",
    )
    _draw_quote_panel(draw, long_q,
                      x=401, y=100, w=379, h=346, fg="#0c0c0c", accent="#c01818")
```

- [ ] **Step 2: Run to confirm failure**

```
venv/bin/pytest tests/test_render_almanac.py -v -k "quote_panel"
```
Expected: ImportError — `_draw_quote_panel` not defined.

- [ ] **Step 3: Add `_draw_quote_panel` to `app/render_almanac.py`**

```python
def _draw_quote_panel(
    draw: ImageDraw.ImageDraw,
    quote: QuoteData,
    *,
    x: int,
    y: int,
    w: int,
    h: int,
    fg: str,
    accent: str,
) -> None:
    """Draw Zone C/Right: Of the Mind (quote with drop-cap)."""
    pad = 12
    inner_x = x + pad
    inner_w = w - 2 * pad
    cy = y + pad

    # Section label + hairline
    f_label = _vfont(JETBRAINS, 13, 500)
    draw.text((inner_x, cy), "OF THE MIND", font=f_label, fill=accent)
    cy += 18
    draw.line([(inner_x, cy), (x + w - pad, cy)], fill=fg, width=1)
    cy += 10

    # Drop-cap: first character of quote text in Playfair Display 900, 62px
    text = quote.text[:160]  # ceiling at 160 chars
    first_char = text[0]
    rest_text = '"' + text[1:] + '"'

    f_dc = _vfont(PLAYFAIR, 62, 900)
    dc_bbox = draw.textbbox((0, 0), first_char, font=f_dc)
    dc_w = dc_bbox[2] - dc_bbox[0] + 6   # +6px gap between drop-cap and body text
    dc_h = dc_bbox[3] - dc_bbox[1]

    draw.text((inner_x, cy), first_char, font=f_dc, fill=accent)

    # Body text flows around the drop-cap
    f_quote = _vfont(SOURCE_SERIF_ITALIC, 21, 400)
    line_h = 28   # 21px * ~1.34 line-height

    # Lines that run beside the drop-cap use a narrower width
    narrow_w = inner_w - dc_w
    cap_lines = max(1, math.ceil(dc_h / line_h))

    narrow_wrapped = wrap_text(draw, rest_text, f_quote, max_width=narrow_w)
    alongside = narrow_wrapped[:cap_lines]
    overflow_words = " ".join(narrow_wrapped[cap_lines:])

    for i, line in enumerate(alongside):
        draw.text((inner_x + dc_w, cy + i * line_h), line, font=f_quote, fill=fg)

    cy_overflow = cy + cap_lines * line_h
    if overflow_words:
        for line in wrap_text(draw, overflow_words, f_quote, max_width=inner_w):
            if cy_overflow + line_h > y + h - 40:  # leave room for attribution
                break
            draw.text((inner_x, cy_overflow), line, font=f_quote, fill=fg)
            cy_overflow += line_h

    # Attribution: right-aligned, hairline above, author in accent
    attr_y = min(cy_overflow + 12, y + h - 28)
    draw.line([(inner_x, attr_y), (x + w - pad, attr_y)], fill=fg, width=1)
    attr_y += 5

    f_attr = _vfont(JETBRAINS, 12, 400)
    author_upper = quote.author.upper()
    draw.text((x + w - pad, attr_y), author_upper, font=f_attr, fill=accent, anchor="rt")
    # Em-dash just to the left of the author text
    auth_w = draw.textbbox((0, 0), author_upper, font=f_attr)[2]
    draw.text((x + w - pad - auth_w - 4, attr_y), "—", font=f_attr, fill=fg, anchor="rt")
```

- [ ] **Step 4: Run the tests**

```
venv/bin/pytest tests/test_render_almanac.py -v -k "quote_panel"
```
Expected: 2 pass.

- [ ] **Step 5: Commit**

```bash
git add app/render_almanac.py tests/test_render_almanac.py
git commit -m "feat: add _draw_quote_panel with drop-cap"
```

---

## Task 7: Implement render_almanac (full integration)

**Files:**
- Modify: `app/render_almanac.py`
- Modify: `tests/test_render_almanac.py`

- [ ] **Step 1: Write the failing integration tests**

Append to `tests/test_render_almanac.py`. All imports were added in Task 2.

```python
_VARIANTS = [
    ("classic", False),
    ("classic", True),
    ("modern", False),
    ("modern", True),
]


@pytest.mark.parametrize("variant,inverted", _VARIANTS)
def test_render_almanac_returns_png_bytes(variant, inverted, sample_weather, sample_quote, blank_icon):
    icons = {"clear-day": blank_icon}
    result = render_almanac(sample_weather, sample_quote, icons, variant=variant, inverted=inverted)
    assert isinstance(result, bytes)
    assert len(result) > 1000


@pytest.mark.parametrize("variant,inverted", _VARIANTS)
def test_render_almanac_correct_dimensions(variant, inverted, sample_weather, sample_quote, blank_icon):
    icons = {"clear-day": blank_icon}
    result = render_almanac(sample_weather, sample_quote, icons, variant=variant, inverted=inverted)
    img = Image.open(io.BytesIO(result))
    assert img.size == (800, 480)


@pytest.mark.parametrize("variant,inverted", _VARIANTS)
def test_render_almanac_missing_icon(variant, inverted, sample_weather, sample_quote):
    result = render_almanac(sample_weather, sample_quote, {}, variant=variant, inverted=inverted)
    img = Image.open(io.BytesIO(result))
    assert img.size == (800, 480)
```

- [ ] **Step 2: Run to confirm failure**

```
venv/bin/pytest tests/test_render_almanac.py -v -k "render_almanac"
```
Expected: ImportError — `render_almanac` not defined.

- [ ] **Step 3: Add `render_almanac` to `app/render_almanac.py`**

Append to the end of `app/render_almanac.py`:

```python
def render_almanac(
    weather: WeatherData,
    quote: QuoteData,
    icons: dict[str, Image.Image],
    *,
    variant: str,
    inverted: bool,
) -> bytes:
    """Render one of four JDU Almanac prototype variants at 800×480."""
    bg, fg, accent = _colors(variant, inverted)
    img = Image.new("RGB", (W, H), bg)
    draw = ImageDraw.Draw(img)

    # Outer border frame
    draw.rectangle(
        [(OUTER_BLEED, OUTER_BLEED), (W - OUTER_BLEED - 1, H - OUTER_BLEED - 1)],
        outline=fg,
        width=FRAME_W,
    )

    # Decorative inner pinstripe (top and bottom only)
    pin_y_top = OUTER_BLEED + FRAME_W + PINSTRIPE_OFFSET
    pin_y_bot = H - OUTER_BLEED - FRAME_W - PINSTRIPE_OFFSET
    draw.line([(INNER_X + 2, pin_y_top), (W - INNER_X - 2, pin_y_top)], fill=fg, width=1)
    draw.line([(INNER_X + 2, pin_y_bot), (W - INNER_X - 2, pin_y_bot)], fill=fg, width=1)

    _draw_masthead(draw, variant, fg, accent)
    _draw_dateband(draw, variant, fg, accent)

    # Vertical body divider
    draw.line([(DIVIDER_X, BODY_Y + 8), (DIVIDER_X, COLON_Y - 8)], fill=fg, width=1)

    _draw_weather_panel(
        img, draw, weather, icons,
        x=CONTENT_X, y=BODY_Y, w=WX_W, h=BODY_H,
        fg=fg, accent=accent,
    )
    _draw_quote_panel(
        draw, quote,
        x=DIVIDER_X + 1, y=BODY_Y, w=CONTENT_RIGHT - DIVIDER_X - 1, h=BODY_H,
        fg=fg, accent=accent,
    )

    _draw_colophon(draw, variant, fg, accent)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
```

- [ ] **Step 4: Run all render_almanac tests**

```
venv/bin/pytest tests/test_render_almanac.py -v
```
Expected: all pass (includes helpers + panel functions + integration tests = ~22 tests).

- [ ] **Step 5: Commit**

```bash
git add app/render_almanac.py tests/test_render_almanac.py
git commit -m "feat: implement render_almanac integration function"
```

---

## Task 8: Add proto_router with 4 endpoints

**Files:**
- Create: `app/proto_router.py`
- Modify: `tests/test_main.py`

- [ ] **Step 1: Write the failing endpoint tests**

Append to `tests/test_main.py` (inside the existing `client` fixture scope — the fixture already handles lifespan):

```python
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
```

- [ ] **Step 2: Run to confirm failure**

```
venv/bin/pytest tests/test_main.py -v -k "almanac"
```
Expected: 404 — endpoints don't exist yet.

- [ ] **Step 3: Create `app/proto_router.py`**

```python
from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import Response

from app.cache import cache

proto_router = APIRouter()


@proto_router.get("/almanac-classic.png")
async def almanac_classic() -> Response:
    return Response(content=cache.get_almanac("classic"), media_type="image/png")


@proto_router.get("/almanac-classic-inv.png")
async def almanac_classic_inv() -> Response:
    return Response(content=cache.get_almanac("classic-inv"), media_type="image/png")


@proto_router.get("/almanac-modern.png")
async def almanac_modern() -> Response:
    return Response(content=cache.get_almanac("modern"), media_type="image/png")


@proto_router.get("/almanac-modern-inv.png")
async def almanac_modern_inv() -> Response:
    return Response(content=cache.get_almanac("modern-inv"), media_type="image/png")
```

- [ ] **Step 4: Wire the router into `app/main.py`**

`app/main.py` needs one import and one `include_router` call. Full updated file:

```python
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import Response, JSONResponse

from app.cache import cache
from app.config import settings
from app.proto_router import proto_router
from app.scheduler import refresh_dashboard, scheduler, start_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    await refresh_dashboard(cache=cache, noaa_grid=settings.noaa_grid)
    start_scheduler(noaa_grid=settings.noaa_grid)
    yield
    scheduler.shutdown(wait=False)


app = FastAPI(title="InkyDashboard", lifespan=lifespan)
app.include_router(proto_router, prefix="/proto")


@app.get("/dashboard/joe.png")
async def joe_png() -> Response:
    return Response(content=cache.get_joe(), media_type="image/png")


@app.get("/dashboard/sam.png")
async def sam_png() -> Response:
    return Response(content=cache.get_sam(), media_type="image/png")


@app.get("/health")
async def health() -> JSONResponse:
    last = cache.last_refresh.isoformat() if cache.last_refresh else None
    return JSONResponse({
        "last_refresh": last,
        "noaa_ok": cache.noaa_ok,
        "quotes_ok": cache.quotes_ok,
    })
```

- [ ] **Step 5: Run the endpoint tests**

```
venv/bin/pytest tests/test_main.py -v
```
Expected: all pass (existing 3 + new 4 = 7 tests).

- [ ] **Step 6: Commit**

```bash
git add app/proto_router.py app/main.py tests/test_main.py
git commit -m "feat: add proto_router with 4 almanac endpoints"
```

---

## Task 9: Wire render_almanac into the scheduler

**Files:**
- Modify: `app/scheduler.py`

- [ ] **Step 1: Update `app/scheduler.py`**

Add the almanac renders to `refresh_dashboard`. The almanac variants are rendered after the production images, reusing the same `weather`, `quote`, and `icons` already fetched. Full updated file:

```python
from __future__ import annotations

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.cache import DashboardCache, cache as _default_cache
from app.icons import load_all_icons
from app.quotes import fetch_quote
from app.render_almanac import render_almanac
from app.render_joe import render_joe
from app.render_sam import render_sam
from app.weather import fetch_weather

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def refresh_dashboard(
    cache: DashboardCache = _default_cache,
    noaa_grid: str = "PSR/166,61",
) -> None:
    icons = load_all_icons(size=120)

    weather = None
    noaa_ok = False
    try:
        weather = await fetch_weather(noaa_grid)
        noaa_ok = True
    except Exception as exc:
        logger.warning("NOAA fetch failed: %s", exc)

    quote = None
    quotes_ok = False
    try:
        quote = await fetch_quote()
        quotes_ok = True
    except Exception as exc:
        logger.warning("ZenQuotes fetch failed: %s", exc)

    if weather is None or quote is None:
        cache.noaa_ok = noaa_ok
        cache.quotes_ok = quotes_ok
        return

    joe_png = render_joe(weather, quote, icons)
    sam_png = render_sam(weather, quote, icons)
    cache.store(joe_png, sam_png, noaa_ok=noaa_ok, quotes_ok=quotes_ok)

    cache.store_almanac(
        classic=render_almanac(weather, quote, icons, variant="classic", inverted=False),
        classic_inv=render_almanac(weather, quote, icons, variant="classic", inverted=True),
        modern=render_almanac(weather, quote, icons, variant="modern", inverted=False),
        modern_inv=render_almanac(weather, quote, icons, variant="modern", inverted=True),
    )


def start_scheduler(noaa_grid: str = "PSR/166,61") -> None:
    scheduler.add_job(
        refresh_dashboard,
        CronTrigger(minute=0),
        kwargs={"noaa_grid": noaa_grid},
        id="refresh_dashboard",
        replace_existing=True,
    )
    scheduler.start()
```

- [ ] **Step 2: Run all tests**

```
venv/bin/pytest tests/ -v
```
Expected: all pass. The `test_main.py` client fixture exercises the full lifespan including the new almanac renders.

- [ ] **Step 3: Commit**

```bash
git add app/scheduler.py
git commit -m "feat: render all 4 almanac variants on hourly scheduler tick"
```

---

## Task 10: Smoke-test the server locally

- [ ] **Step 1: Start the server**

```bash
cd eink-dashboard
venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
```

- [ ] **Step 2: Hit all four proto endpoints**

In a second terminal (from the repo root):

```bash
curl -s -o /tmp/classic.png     http://localhost:8000/proto/almanac-classic.png     && echo "classic OK"
curl -s -o /tmp/classic-inv.png http://localhost:8000/proto/almanac-classic-inv.png && echo "classic-inv OK"
curl -s -o /tmp/modern.png      http://localhost:8000/proto/almanac-modern.png      && echo "modern OK"
curl -s -o /tmp/modern-inv.png  http://localhost:8000/proto/almanac-modern-inv.png  && echo "modern-inv OK"
```

Expected: 4 "OK" lines and 4 non-empty PNG files in `/tmp/`.

- [ ] **Step 3: Open the PNGs to visually verify all 4 variants**

```bash
open /tmp/classic.png /tmp/classic-inv.png /tmp/modern.png /tmp/modern-inv.png
```

- [ ] **Step 4: Final commit (if any tweaks were needed)**

```bash
git add -p   # stage only intentional changes
git commit -m "fix: visual tweaks from smoke test"
```
