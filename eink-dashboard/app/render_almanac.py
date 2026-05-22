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
    """Draw Zone A: Masthead (~62px tall, starts at MAST_Y)."""
    cx = W // 2

    if variant == "classic":
        f_ribbon = _vfont(JETBRAINS, 12, 400)
        draw.text((CONTENT_X, MAST_Y + 4), VOL_LABEL.upper(), font=f_ribbon, fill=accent)
        draw.text((CONTENT_RIGHT, MAST_Y + 4), ISSUE_LABEL, font=f_ribbon, fill=accent, anchor="rt")

        f_title = _vfont(PLAYFAIR, 38, 900)
        draw.text((cx, MAST_Y + 24), "The JDU Almanac", font=f_title, fill=fg, anchor="mt")

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
    cy = COLON_Y + (COLOPHON_H - 14) // 2

    draw.line([(CONTENT_X, COLON_Y), (CONTENT_RIGHT, COLON_Y)], fill=fg, width=2)

    draw.text((CONTENT_X, cy), "PRINTED IN INK", font=f, fill=fg)
    draw.text((CONTENT_RIGHT, cy), "INKY · 7.3″ · 800×480", font=f, fill=fg, anchor="rt")

    if variant == "classic":
        draw.text((W // 2, cy), "✦ ✦ ✦", font=f, fill=accent, anchor="mt")


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
    cy = DATE_Y + (DATEBAND_H - 16) // 2

    draw.line([(CONTENT_X, DATE_Y), (CONTENT_RIGHT, DATE_Y)], fill=fg, width=2)
    draw.line([(CONTENT_X, DATE_BOT - 1), (CONTENT_RIGHT, DATE_BOT - 1)], fill=fg, width=1)

    if variant == "classic":
        tokens = [day, f"{month_day} · {year_roman}", LOCATION_COORDS]
        sep = "  ·  "

        total_w = sum(draw.textbbox((0, 0), t, font=f)[2] for t in tokens)
        total_w += sum(draw.textbbox((0, 0), sep, font=f)[2] for _ in range(len(tokens) - 1))
        sx = W // 2 - total_w // 2

        for i, token in enumerate(tokens):
            draw.text((sx, cy), token, font=f, fill=fg)
            sx += draw.textbbox((0, 0), token, font=f)[2]
            if i < len(tokens) - 1:
                draw.text((sx, cy), sep, font=f, fill=accent)
                sx += draw.textbbox((0, 0), sep, font=f)[2]

    else:  # modern: day left, date right, no coordinates
        date_str = f"{month_day} · {year_roman}"
        draw.text((CONTENT_X, cy), day, font=f, fill=fg)
        draw.text((CONTENT_RIGHT, cy), date_str, font=f, fill=fg, anchor="rt")


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

    f_label = _vfont(JETBRAINS, 13, 500)
    draw.text((inner_x, cy), "OF THE WEATHER", font=f_label, fill=accent)
    cy += 18
    draw.line([(inner_x, cy), (x + w - pad, cy)], fill=fg, width=1)
    cy += 10

    icon_size = 70
    icon_name = select_icon_name(weather.short_forecast, weather.period_name)
    raw = icons.get(icon_name) or icons.get("clear-day")
    if raw is None:
        raw = Image.new("RGBA", (icon_size, icon_size), (150, 150, 150, 255))
    icon_img = raw.resize((icon_size, icon_size), Image.LANCZOS)
    img.paste(icon_img, (inner_x, cy), icon_img)

    temp_x = inner_x + icon_size + 12
    f_temp = _vfont(SOURCE_SERIF, 120, 700)
    draw.text((temp_x, cy), str(weather.temperature), font=f_temp, fill=accent, anchor="lt")

    temp_bbox = draw.textbbox((temp_x, cy), str(weather.temperature), font=f_temp)
    f_deg = _vfont(SOURCE_SERIF, 40, 700)
    draw.text((temp_bbox[2] + 2, cy + 4), "°", font=f_deg, fill=accent, anchor="lt")

    cy += max(icon_size, 90) + 12

    stat = f"{weather.short_forecast.upper()} · {weather.precip_percent}% RAIN"
    f_stat = _vfont(JETBRAINS, 13, 400)
    draw.text((inner_x, cy), stat, font=f_stat, fill=fg)
    cy += 22

    desc = weather.detailed_forecast
    if len(desc) > 120:
        desc = desc[:117].rstrip() + "…"
    f_desc = _vfont(SOURCE_SERIF_ITALIC, 15, 400)
    desc_lines = wrap_text(draw, desc, f_desc, max_width=inner_w)
    for line in desc_lines[:3]:
        draw.text((inner_x, cy), line, font=f_desc, fill=fg)
        cy += 22


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
