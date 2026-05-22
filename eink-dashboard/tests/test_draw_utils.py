from PIL import Image, ImageDraw, ImageFont

from app.draw_utils import wrap_text


def _make_draw(width=400, height=400):
    img = Image.new("RGB", (width, height), "white")
    return ImageDraw.Draw(img)


def test_wrap_text_short_fits_one_line():
    draw = _make_draw()
    font = ImageFont.load_default()
    lines = wrap_text(draw, "Hello", font, max_width=300)
    assert lines == ["Hello"]


def test_wrap_text_long_breaks_into_lines():
    draw = _make_draw(width=200)
    font = ImageFont.load_default()
    text = "This is a very long sentence that should be wrapped across multiple lines"
    lines = wrap_text(draw, text, font, max_width=80)
    assert len(lines) > 1
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        assert bbox[2] - bbox[0] <= 80


def test_wrap_text_empty_string():
    draw = _make_draw()
    font = ImageFont.load_default()
    lines = wrap_text(draw, "", font, max_width=300)
    assert lines == [""]
