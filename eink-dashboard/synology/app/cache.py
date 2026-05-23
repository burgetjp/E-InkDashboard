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
