# Sam's Almanac Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `render_almanac_sam()` — a 600×400 Almanac Modern Inverted layout with "Joy of My Life" title and 45/55 column split — accessible at `/proto/almanac-sam.png` for local preview before deploying to Sam's Pi.

**Architecture:** New public function `render_almanac_sam()` added to the bottom of `app/render_almanac.py`. It reuses shared helpers (`_vfont`, `_colors`, `_roman_year`, `_draw_quote_panel`) but draws the masthead, dateband, weather panel, and colophon inline with 600×400-specific geometry — those four helpers all reference module-level 800×480 constants and cannot be called directly. A new `almanac_sam` cache slot, a proto endpoint, and a scheduler hook complete the wiring.

**Tech Stack:** Python 3.12, Pillow, FastAPI, APScheduler, pytest

---

### Task 1: Add `almanac_sam` cache slot

**Files:**
- Modify: `app/cache.py`
- Modify: `tests/test_cache.py`

- [ ] **Step 1: Write two failing tests**

Add to the bottom of `tests/test_cache.py`:

```python
def test_almanac_sam_slot_starts_empty():
    c = DashboardCache()
    assert c.almanac_sam is None


def test_store_and_get_almanac_sam():
    c = DashboardCache()
    stub = _make_png("gray")
    c.store_almanac_sam(stub)
    assert c.get_almanac_sam() == stub


def test_get_almanac_sam_fallback_when_empty():
    c = DashboardCache()
    result = c.get_almanac_sam()
    assert isinstance(result, bytes)
    img = Image.open(io.BytesIO(result))
    assert img.size == (600, 400)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd eink-dashboard && venv/bin/pytest tests/test_cache.py::test_almanac_sam_slot_starts_empty tests/test_cache.py::test_store_and_get_almanac_sam tests/test_cache.py::test_get_almanac_sam_fallback_when_empty -v
```

Expected: FAIL — `DashboardCache` has no `almanac_sam` attribute.

- [ ] **Step 3: Add cache field and methods to `app/cache.py`**

Add the new field after `almanac_modern_inv`:

```python
almanac_sam: Optional[bytes] = field(default=None)
```

Add two new methods after `store_almanac`:

```python
def store_almanac_sam(self, sam: bytes) -> None:
    self.almanac_sam = sam

def get_almanac_sam(self) -> bytes:
    if self.almanac_sam is None:
        return _make_fallback_png(600, 400, "Almanac starting…")
    return self.almanac_sam
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
venv/bin/pytest tests/test_cache.py -v
```

Expected: All PASS.

- [ ] **Step 5: Commit**

```bash
git add app/cache.py tests/test_cache.py
git commit -m "feat: add almanac_sam cache slot with fallback"
```

---

### Task 2: Implement `render_almanac_sam()`

**Files:**
- Modify: `app/render_almanac.py`
- Modify: `tests/test_render_almanac.py`

- [ ] **Step 1: Write failing tests**

Add to the bottom of `tests/test_render_almanac.py`:

```python
from app.render_almanac import render_almanac_sam


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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
venv/bin/pytest tests/test_render_almanac.py::test_render_almanac_sam_returns_png_bytes -v
```

Expected: FAIL — `cannot import name 'render_almanac_sam'`.

- [ ] **Step 3: Add `render_almanac_sam()` to the bottom of `app/render_almanac.py`**

```python
def render_almanac_sam(
    weather: WeatherData,
    quote: QuoteData,
    icons: dict[str, Image.Image],
) -> bytes:
    """Render Sam's Almanac at 600×400 in Almanac Modern Inverted style."""
    # --- Local geometry (600×400) ---
    sw, sh = 600, 400
    outer_bleed = 5
    frame_w = 2
    pinstripe_offset = 3
    masthead_h = 72
    dateband_h = 25
    colophon_h = 22
    pad = 10
    inner_x = outer_bleed + frame_w        # 7
    content_x = inner_x + pad              # 17
    content_right = sw - inner_x - pad     # 583
    content_w = content_right - content_x  # 566
    mast_y = inner_x                       # 7
    date_y = mast_y + masthead_h           # 79
    date_bot = date_y + dateband_h         # 104
    colon_y = sh - inner_x - colophon_h    # 371
    body_y = date_bot                      # 104
    body_h = colon_y - body_y              # 267
    wx_w = round(content_w * 0.45)         # 255
    divider_x = content_x + wx_w           # 272

    bg, fg, accent = _colors("modern", True)
    img = Image.new("RGB", (sw, sh), bg)
    draw = ImageDraw.Draw(img)

    # Border
    draw.rectangle(
        [(outer_bleed, outer_bleed), (sw - outer_bleed - 1, sh - outer_bleed - 1)],
        outline=fg,
        width=frame_w,
    )

    # Pinstripes
    pin_top = outer_bleed + frame_w + pinstripe_offset   # 10
    pin_bot = sh - outer_bleed - frame_w - pinstripe_offset  # 390
    draw.line([(inner_x + 2, pin_top), (sw - inner_x - 2, pin_top)], fill=fg, width=1)
    draw.line([(inner_x + 2, pin_bot), (sw - inner_x - 2, pin_bot)], fill=fg, width=1)

    now = datetime.now(ZoneInfo("America/Phoenix"))

    # Zone A: Masthead
    f_title = _vfont(PLAYFAIR, 28, 900)
    draw.text((content_x, mast_y + 14), "Joy of My Life", font=f_title, fill=fg, anchor="lt")

    # Zone B: Dateband
    day = now.strftime("%A").upper()
    month_day = now.strftime("%B %-d").upper()
    date_str = f"{month_day} · {_roman_year(now.year)}"
    f_date = _vfont(JETBRAINS, 11, 400)
    cy_date = date_y + (dateband_h - 14) // 2
    draw.line([(content_x, date_y), (content_right, date_y)], fill=fg, width=2)
    draw.line([(content_x, date_bot - 1), (content_right, date_bot - 1)], fill=fg, width=1)
    draw.text((content_x, cy_date), day, font=f_date, fill=fg)
    draw.text((content_right, cy_date), date_str, font=f_date, fill=fg, anchor="rt")

    # Vertical body divider
    draw.line([(divider_x, body_y + 8), (divider_x, colon_y - 8)], fill=fg, width=1)

    # Zone C Left: Weather (inline — scaled for 255px column)
    wx_inner_x = content_x + pad   # 27
    wx_inner_w = wx_w - 2 * pad    # 235
    cy = body_y + pad              # 114

    f_label = _vfont(JETBRAINS, 10, 500)
    draw.text((wx_inner_x, cy), "OF THE WEATHER", font=f_label, fill=accent)
    cy += 16
    draw.line([(wx_inner_x, cy), (content_x + wx_w - pad, cy)], fill=fg, width=1)
    cy += 8

    icon_size = 60
    icon_name = select_icon_name(weather.short_forecast, weather.period_name)
    raw = icons.get(icon_name) or icons.get("clear-day")
    if raw is None:
        raw = Image.new("RGBA", (icon_size, icon_size), (150, 150, 150, 255))
    icon_img = raw.resize((icon_size, icon_size), Image.LANCZOS)
    img.paste(icon_img, (wx_inner_x, cy), icon_img)

    temp_x = wx_inner_x + icon_size + 10
    f_temp = _vfont(SOURCE_SERIF, 80, 700)
    draw.text((temp_x, cy), str(weather.temperature), font=f_temp, fill=accent, anchor="lt")
    temp_bbox = draw.textbbox((temp_x, cy), str(weather.temperature), font=f_temp)
    f_deg = _vfont(SOURCE_SERIF, 28, 700)
    draw.text((temp_bbox[2] + 2, cy + 4), "°", font=f_deg, fill=accent, anchor="lt")

    cy += max(icon_size, 72) + 8

    stat = f"{weather.short_forecast.upper()} · {weather.precip_percent}% RAIN"
    f_stat = _vfont(JETBRAINS, 10, 400)
    draw.text((wx_inner_x, cy), stat, font=f_stat, fill=fg)
    cy += 18

    desc = weather.detailed_forecast
    if len(desc) > 120:
        desc = desc[:117].rstrip() + "…"
    f_desc = _vfont(SOURCE_SERIF_ITALIC, 12, 400)
    for line in wrap_text(draw, desc, f_desc, max_width=wx_inner_w)[:3]:
        draw.text((wx_inner_x, cy), line, font=f_desc, fill=fg)
        cy += 18

    # Zone C Right: Quote (reuse existing helper — 311px column fits font sizes)
    quote_x = divider_x + 1
    quote_w = content_right - quote_x
    _draw_quote_panel(
        draw, quote,
        x=quote_x, y=body_y, w=quote_w, h=body_h,
        fg=fg, accent=accent,
    )

    # Zone D: Colophon
    timestamp = now.strftime("%-I:%M %p")
    f_colon = _vfont(JETBRAINS, 9, 400)
    cy_colon = colon_y + (colophon_h - 12) // 2
    draw.line([(content_x, colon_y), (content_right, colon_y)], fill=fg, width=1)
    draw.text((content_x, cy_colon), f"PRINTED IN E-INK at {timestamp}", font=f_colon, fill=fg)
    draw.text((content_right, cy_colon), "INKY · 600×400", font=f_colon, fill=fg, anchor="rt")

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
venv/bin/pytest tests/test_render_almanac.py -v
```

Expected: All PASS, including the four new `test_render_almanac_sam_*` tests.

- [ ] **Step 5: Commit**

```bash
git add app/render_almanac.py tests/test_render_almanac.py
git commit -m "feat: add render_almanac_sam() — 600x400 inverted almanac for Sam"
```

---

### Task 3: Wire Sam's almanac into the scheduler

**Files:**
- Modify: `app/scheduler.py`
- Modify: `tests/test_scheduler.py`

- [ ] **Step 1: Write a failing test**

Add to the bottom of `tests/test_scheduler.py`:

```python
@respx.mock
async def test_refresh_dashboard_populates_almanac_sam():
    respx.get("https://api.weather.gov/gridpoints/PSR/166,61/forecast").mock(
        return_value=httpx.Response(200, json=NOAA_RESP)
    )
    respx.get("https://zenquotes.io/api/random").mock(
        return_value=httpx.Response(200, json=QUOTE_RESP)
    )
    c = DashboardCache()
    with patch("app.scheduler.load_all_icons", return_value=_blank_icons()):
        await refresh_dashboard(cache=c, noaa_grid="PSR/166,61")

    assert c.almanac_sam is not None
```

- [ ] **Step 2: Run test to verify it fails**

```bash
venv/bin/pytest tests/test_scheduler.py::test_refresh_dashboard_populates_almanac_sam -v
```

Expected: FAIL — `c.almanac_sam` is `None` (scheduler doesn't call `render_almanac_sam` yet).

- [ ] **Step 3: Add the render call to `app/scheduler.py`**

First, add the import at the top of the import block in `scheduler.py`:

```python
from app.render_almanac import render_almanac, render_almanac_sam
```

Then in `refresh_dashboard()`, after the existing `cache.store_almanac(...)` call, add:

```python
cache.store_almanac_sam(
    render_almanac_sam(weather, quote, icons)
)
```

The full block should look like:

```python
cache.store_almanac(
    classic=render_almanac(weather, quote, icons, variant="classic", inverted=False),
    classic_inv=render_almanac(weather, quote, icons, variant="classic", inverted=True),
    modern=render_almanac(weather, quote, icons, variant="modern", inverted=False),
    modern_inv=render_almanac(weather, quote, icons, variant="modern", inverted=True),
)
cache.store_almanac_sam(
    render_almanac_sam(weather, quote, icons)
)
```

- [ ] **Step 4: Run all scheduler tests to verify they pass**

```bash
venv/bin/pytest tests/test_scheduler.py -v
```

Expected: All PASS.

- [ ] **Step 5: Commit**

```bash
git add app/scheduler.py tests/test_scheduler.py
git commit -m "feat: render and cache Sam's almanac on every scheduler refresh"
```

---

### Task 4: Expose `/proto/almanac-sam.png` endpoint

**Files:**
- Modify: `app/proto_router.py`
- Modify: `tests/test_main.py`

- [ ] **Step 1: Write a failing test**

`tests/test_main.py` already has a `client` fixture that mocks NOAA and ZenQuotes on startup. Add to the bottom of that file:

```python
def test_almanac_sam_endpoint_returns_png(client):
    resp = client.get("/proto/almanac-sam.png")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "image/png"
    img = Image.open(io.BytesIO(resp.content))
    assert img.size == (600, 400)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
venv/bin/pytest tests/test_main.py::test_almanac_sam_endpoint_returns_png -v
```

Expected: FAIL — 404 Not Found (route doesn't exist yet).

- [ ] **Step 3: Add the route to `app/proto_router.py`**

```python
@proto_router.get("/almanac-sam.png")
async def almanac_sam_png() -> Response:
    return Response(content=cache.get_almanac_sam(), media_type="image/png")
```

- [ ] **Step 4: Run the test to verify it passes**

```bash
venv/bin/pytest tests/test_main.py::test_almanac_sam_endpoint_returns_png -v
```

Expected: PASS.

- [ ] **Step 5: Run the full test suite**

```bash
venv/bin/pytest tests/ -v
```

Expected: All tests PASS.

- [ ] **Step 6: Commit**

```bash
git add app/proto_router.py tests/test_main.py
git commit -m "feat: expose /proto/almanac-sam.png endpoint"
```

---

### Task 5: Local preview

- [ ] **Step 1: Start the server**

```bash
cd eink-dashboard && venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
```

- [ ] **Step 2: Open the preview URL**

Navigate to: `http://localhost:8000/proto/almanac-sam.png`

Verify:
- 600×400 image renders without errors
- Black background, cream text
- "Joy of My Life" in masthead
- Weather left (no circle under icon), quote right
- Dateband and colophon visible

- [ ] **Step 3: Force a refresh if needed**

```bash
curl -s -X POST http://localhost:8000/admin/refresh | python3 -m json.tool
```

Expected: `{"refreshed": true, "noaa_ok": true, "quotes_ok": true}`
