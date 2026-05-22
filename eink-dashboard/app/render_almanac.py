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

INNER_X = OUTER_BLEED + FRAME_W    # = 8
CONTENT_X = INNER_X + PAD          # = 20
CONTENT_RIGHT = W - INNER_X - PAD  # = 780
CONTENT_W = CONTENT_RIGHT - CONTENT_X  # = 760

MAST_Y = INNER_X                        # = 8
MAST_BOT = MAST_Y + MASTHEAD_H          # = 70
DATE_Y = MAST_BOT                       # = 70
DATE_BOT = DATE_Y + DATEBAND_H          # = 100
COLON_Y = H - INNER_X - COLOPHON_H     # = 446
COLON_BOT = H - INNER_X                # = 472
BODY_Y = DATE_BOT                       # = 100
BODY_H = COLON_Y - BODY_Y              # = 346

WX_W = CONTENT_W // 2                  # weather column width = 380
DIVIDER_X = CONTENT_X + WX_W           # = 400

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


def _draw_masthead(
    draw: ImageDraw.ImageDraw,
    variant: str,
    fg: str,
    accent: str,
) -> None:
    raise NotImplementedError


def _draw_colophon(
    draw: ImageDraw.ImageDraw,
    variant: str,
    fg: str,
    accent: str,
) -> None:
    raise NotImplementedError


def _draw_dateband(
    draw: ImageDraw.ImageDraw,
    variant: str,
    fg: str,
    accent: str,
) -> None:
    raise NotImplementedError


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
    raise NotImplementedError


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
    raise NotImplementedError


def render_almanac(
    weather: WeatherData,
    quote: QuoteData,
    icons: dict[str, Image.Image],
    *,
    variant: str,
    inverted: bool,
) -> bytes:
    raise NotImplementedError
