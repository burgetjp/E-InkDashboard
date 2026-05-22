import io
import pytest
from PIL import Image

from app.render_sam import render_sam


def test_render_sam_returns_png_bytes(sample_weather, sample_quote, blank_icon):
    icons = {"clear-day": blank_icon}
    png_bytes = render_sam(sample_weather, sample_quote, icons)
    assert isinstance(png_bytes, bytes)
    assert len(png_bytes) > 1000


def test_render_sam_correct_dimensions(sample_weather, sample_quote, blank_icon):
    icons = {"clear-day": blank_icon}
    png_bytes = render_sam(sample_weather, sample_quote, icons)
    img = Image.open(io.BytesIO(png_bytes))
    assert img.size == (600, 400)


def test_render_sam_missing_icon_uses_fallback(sample_weather, sample_quote):
    png_bytes = render_sam(sample_weather, sample_quote, {})
    img = Image.open(io.BytesIO(png_bytes))
    assert img.size == (600, 400)
