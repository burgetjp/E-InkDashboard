import io
import math
import pytest
from PIL import Image, ImageDraw, ImageFont

from app.render_almanac import (
    _vfont, _colors, _roman_year,
    _draw_masthead, _draw_colophon, _draw_dateband,
    _draw_weather_panel, _draw_quote_panel,
    render_almanac, render_almanac_sam,
    PLAYFAIR, JETBRAINS,
    W, H,
)
from app.weather import WeatherData
from app.quotes import QuoteData


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


# --- _draw_masthead ---

def test_draw_masthead_classic_does_not_raise():
    img, draw = _blank_draw()
    _draw_masthead(draw, "classic", "#0c0c0c", "#c01818")

def test_draw_masthead_modern_does_not_raise():
    img, draw = _blank_draw()
    _draw_masthead(draw, "modern", "#0c0c0c", "#0c0c0c")


# --- _draw_colophon ---

def test_draw_colophon_classic_does_not_raise():
    img, draw = _blank_draw()
    _draw_colophon(draw, "classic", "#0c0c0c", "#c01818")

def test_draw_colophon_modern_does_not_raise():
    img, draw = _blank_draw()
    _draw_colophon(draw, "modern", "#0c0c0c", "#0c0c0c")


# --- _draw_dateband ---

def test_draw_dateband_classic_does_not_raise():
    img, draw = _blank_draw()
    _draw_dateband(draw, "classic", "#0c0c0c", "#c01818")

def test_draw_dateband_modern_does_not_raise():
    img, draw = _blank_draw()
    _draw_dateband(draw, "modern", "#0c0c0c", "#0c0c0c")


# --- _draw_weather_panel ---

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


# --- _draw_quote_panel ---

def test_draw_quote_panel_does_not_raise(sample_quote):
    img, draw = _blank_draw()
    _draw_quote_panel(draw, sample_quote,
                      x=401, y=100, w=379, h=346, fg="#0c0c0c", accent="#c01818")

def test_draw_quote_panel_long_quote_does_not_raise():
    img, draw = _blank_draw()
    long_q = QuoteData(text="A" * 200, author="Author")
    _draw_quote_panel(draw, long_q,
                      x=401, y=100, w=379, h=346, fg="#0c0c0c", accent="#c01818")


# --- render_almanac integration ---

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


def test_render_almanac_sam_returns_png_bytes(sample_weather, sample_quote, blank_icon):
    result = render_almanac_sam(sample_weather, sample_quote, {"clear-day": blank_icon})
    assert isinstance(result, bytes)
    assert len(result) > 1000


def test_render_almanac_sam_correct_dimensions(sample_weather, sample_quote, blank_icon):
    result = render_almanac_sam(sample_weather, sample_quote, {"clear-day": blank_icon})
    img = Image.open(io.BytesIO(result))
    assert img.size == (600, 400)


def test_render_almanac_sam_missing_icon(sample_weather, sample_quote):
    result = render_almanac_sam(sample_weather, sample_quote, {})
    img = Image.open(io.BytesIO(result))
    assert img.size == (600, 400)


def test_render_almanac_sam_inverted_background(sample_weather, sample_quote, blank_icon):
    result = render_almanac_sam(sample_weather, sample_quote, {"clear-day": blank_icon})
    img = Image.open(io.BytesIO(result))
    # Center of canvas should be the dark (#0c0c0c) background
    r, g, b = img.getpixel((300, 200))
    assert r < 20 and g < 20 and b < 20
