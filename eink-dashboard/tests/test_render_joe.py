import io
import pytest
from PIL import Image

from app.render_joe import render_joe


def test_render_joe_returns_png_bytes(sample_weather, sample_quote, blank_icon):
    icons = {"clear-day": blank_icon}
    png_bytes = render_joe(sample_weather, sample_quote, icons)
    assert isinstance(png_bytes, bytes)
    assert len(png_bytes) > 1000


def test_render_joe_correct_dimensions(sample_weather, sample_quote, blank_icon):
    icons = {"clear-day": blank_icon}
    png_bytes = render_joe(sample_weather, sample_quote, icons)
    img = Image.open(io.BytesIO(png_bytes))
    assert img.size == (800, 480)


def test_render_joe_missing_icon_uses_fallback(sample_weather, sample_quote):
    png_bytes = render_joe(sample_weather, sample_quote, {})
    img = Image.open(io.BytesIO(png_bytes))
    assert img.size == (800, 480)
