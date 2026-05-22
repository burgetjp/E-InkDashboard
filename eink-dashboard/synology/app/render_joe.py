from __future__ import annotations

import io
import os
from datetime import datetime
from zoneinfo import ZoneInfo

from PIL import Image, ImageDraw, ImageFont

from app.accent import select_accent
from app.draw_utils import wrap_text
from app.icons import select_icon_name
from app.weather import WeatherData
from app.quotes import QuoteData

W, H = 800, 480
PAD = 20
HEADER_H = 48

BG = "#000000"
HEADER_BORDER = "#222222"
DIVIDER = "#444444"
LABEL_COLOR = "#ffffff"
SUBTITLE_COLOR = "#ffffff"
QUOTE_COLOR = "#ffffff"
AUTHOR_COLOR = "#ffffff"
FORECAST_BG = "#1a1a1a"
FORECAST_BORDER = "#303030"
FORECAST_TEXT = "#ffffff"
HEADER_TITLE = "#ffffff"
HEADER_DATE = "#ffffff"

_FONT_DIR = os.path.join(os.path.dirname(__file__), "..", "assets", "fonts")


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    name = "Inter-Bold.ttf" if bold else "Inter-Regular.ttf"
    return ImageFont.truetype(os.path.join(_FONT_DIR, name), size)


def render_joe(
    weather: WeatherData,
    quote: QuoteData,
    icons: dict[str, Image.Image],
) -> bytes:
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    date_str = datetime.now(ZoneInfo("America/Phoenix")).strftime("%A, %B %-d, %Y")

    # Header
    draw.line([(0, HEADER_H), (W, HEADER_H)], fill=HEADER_BORDER, width=1)
    draw.text((PAD, HEADER_H // 2), "JDU DASHBOARD", font=_font(18, bold=True), fill=HEADER_TITLE, anchor="lm")
    draw.text((W - PAD, HEADER_H // 2), date_str, font=_font(15), fill=HEADER_DATE, anchor="rm")

    # Body layout
    body_top = HEADER_H
    body_h = H - HEADER_H
    usable_w = W - 2 * PAD
    weather_w = round(usable_w * 1.4 / 3.0)
    quote_w = usable_w - weather_w - 1  # -1 for divider

    wx = PAD
    divider_x = PAD + weather_w
    qx = divider_x + 1

    # Vertical divider
    draw.line([(divider_x, body_top + PAD), (divider_x, H - PAD)], fill=DIVIDER, width=2)

    # Accent colors
    temp_color, icon_bg = select_accent(weather.short_forecast)

    # Weather section
    inner_x = wx + PAD
    wy = body_top + PAD

    draw.text((inner_x, wy), f"{weather.period_name.upper()}'S WEATHER", font=_font(13, bold=True), fill=LABEL_COLOR)
    wy += 30

    # Icon circle
    icon_size = 90
    icon_name = select_icon_name(weather.short_forecast, weather.period_name)
    icon_img = icons.get(icon_name) or icons.get("clear-day") or Image.new("RGBA", (icon_size, icon_size), (100, 100, 100, 255))
    icon_img_r = icon_img.resize((icon_size, icon_size), Image.LANCZOS)

    circle_img = Image.new("RGBA", (icon_size, icon_size), (0, 0, 0, 0))
    circle_draw = ImageDraw.Draw(circle_img)
    circle_draw.ellipse([(0, 0), (icon_size - 1, icon_size - 1)], fill=icon_bg)
    circle_img.paste(icon_img_r, (0, 0), icon_img_r)
    img.paste(circle_img, (inner_x, wy), circle_img)

    # Temperature
    temp_x = inner_x + icon_size + 16
    draw.text((temp_x, wy), f"{weather.temperature}°", font=_font(80, bold=True), fill=temp_color, anchor="lt")

    wy += icon_size + 8

    # Subtitle
    subtitle = f"{weather.short_forecast} · {weather.precip_percent}% chance rain"
    f_subtitle = _font(16)
    subtitle_lines = wrap_text(draw, subtitle, f_subtitle, max_width=weather_w - 2 * PAD)
    for line in subtitle_lines:
        draw.text((inner_x, wy), line, font=f_subtitle, fill=SUBTITLE_COLOR)
        wy += 22
    wy += 6

    # Forecast box
    box_x1 = wx + PAD // 2
    box_x2 = wx + weather_w - PAD // 2
    box_y1 = wy
    box_y2 = H - PAD
    draw.rounded_rectangle([(box_x1, box_y1), (box_x2, box_y2)], radius=6, fill=FORECAST_BG, outline=FORECAST_BORDER)
    f_forecast = _font(13)
    forecast_lines = wrap_text(draw, weather.detailed_forecast, f_forecast, max_width=box_x2 - box_x1 - 24)
    lines_to_draw = forecast_lines[:4]
    txt_y = max(box_y2 - 12 - 13 - (len(lines_to_draw) - 1) * 20, box_y1 + 12)
    for line in lines_to_draw:
        draw.text((box_x1 + 12, txt_y), line, font=f_forecast, fill=FORECAST_TEXT)
        txt_y += 20

    # Quote section
    inner_qx = qx + PAD
    qy = body_top + PAD

    draw.text((inner_qx, qy), "QUOTE", font=_font(13, bold=True), fill=LABEL_COLOR)
    qy += 30

    f_quote = _font(18)
    quote_lines = wrap_text(draw, f'"{quote.text}"', f_quote, max_width=quote_w - 2 * PAD)
    for line in quote_lines:
        draw.text((inner_qx, qy), line, font=f_quote, fill=QUOTE_COLOR)
        qy += 28

    qy += 8
    draw.text((qx + quote_w - PAD + 1, qy), f"— {quote.author}", font=_font(14), fill=AUTHOR_COLOR, anchor="rm")

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
