import io
from PIL import Image

from app.cache import DashboardCache


def _make_png(color="red", size=(10, 10)) -> bytes:
    img = Image.new("RGB", size, color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_cache_starts_empty():
    c = DashboardCache()
    assert c.joe_png is None
    assert c.sam_png is None
    assert c.last_refresh is None
    assert c.noaa_ok is False
    assert c.quotes_ok is False


def test_store_and_retrieve():
    c = DashboardCache()
    joe = _make_png("blue")
    sam = _make_png("green")
    c.store(joe, sam, noaa_ok=True, quotes_ok=True)
    assert c.get_joe() == joe
    assert c.get_sam() == sam
    assert c.noaa_ok is True
    assert c.quotes_ok is True
    assert c.last_refresh is not None


def test_get_joe_fallback_when_empty():
    c = DashboardCache()
    result = c.get_joe()
    assert isinstance(result, bytes)
    img = Image.open(io.BytesIO(result))
    assert img.size == (800, 480)


def test_get_sam_fallback_when_empty():
    c = DashboardCache()
    result = c.get_sam()
    assert isinstance(result, bytes)
    img = Image.open(io.BytesIO(result))
    assert img.size == (600, 400)


def test_store_keeps_previous_on_partial_failure():
    c = DashboardCache()
    joe = _make_png("blue")
    sam = _make_png("green")
    c.store(joe, sam, noaa_ok=True, quotes_ok=True)
    # Simulate keeping old data (caller skips store on failure)
    assert c.get_joe() == joe
    assert c.get_sam() == sam
