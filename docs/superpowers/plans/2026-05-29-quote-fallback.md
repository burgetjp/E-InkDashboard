# Quote Fallback API Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a three-tier quote fallback so the dashboard always regenerates: ZenQuotes → Motivational Spark API → last cached quote, with `*` or `**` appended to Joe's colophon timestamp to signal degraded state.

**Architecture:** `QuoteData` gains a `source` field. `fetch_quote()` catches failures and tries each tier in order, storing the last successful result in a module-level variable. `_draw_colophon()` receives `source` and appends the appropriate suffix to the timestamp string via a pure helper function.

**Tech Stack:** Python 3.12, httpx, Pillow, pytest, respx (HTTP mocking)

---

## File Map

| File | Change |
|------|--------|
| `app/quotes.py` | Add `QuoteSource` type alias, `source` field to `QuoteData`, `_last_good_quote` module var, three-tier logic in `fetch_quote()` |
| `app/render_almanac.py` | Add `_colophon_label()` helper, update `_draw_colophon()` signature, update call site in `render_almanac()` |
| `tests/test_quotes.py` | Add three new test cases for fallback/cache/total-failure behavior |
| `tests/test_render_almanac.py` | Update two existing colophon tests (new required arg), add three new tests for label logic |

`scheduler.py`, `conftest.py`, `render_sam.py`, and `render_joe.py` — no changes.

---

### Task 1: Extend QuoteData with `source` field

**Files:**
- Modify: `app/quotes.py`

- [ ] **Step 1: Write failing tests for the new `source` field**

Add to the bottom of `tests/test_quotes.py`:

```python
def test_quote_data_default_source_is_primary():
    q = QuoteData(text="Hello", author="World")
    assert q.source == "primary"


def test_quote_data_accepts_fallback_source():
    q = QuoteData(text="Hello", author="World", source="fallback")
    assert q.source == "fallback"


def test_quote_data_accepts_cached_source():
    q = QuoteData(text="Hello", author="World", source="cached")
    assert q.source == "cached"
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
cd /Users/joeburgett/Working/E-InkDashboard/eink-dashboard
venv/bin/pytest tests/test_quotes.py::test_quote_data_default_source_is_primary tests/test_quotes.py::test_quote_data_accepts_fallback_source tests/test_quotes.py::test_quote_data_accepts_cached_source -v
```

Expected: `FAILED` — `QuoteData` has no `source` field yet.

- [ ] **Step 3: Add `QuoteSource` and `source` field to `QuoteData`**

Replace the top of `app/quotes.py` with:

```python
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Optional

import httpx

QuoteSource = Literal["primary", "fallback", "cached"]


@dataclass
class QuoteData:
    text: str
    author: str
    source: QuoteSource = "primary"
```

Leave `fetch_quote()` unchanged for now.

- [ ] **Step 4: Run tests to confirm they pass**

```bash
venv/bin/pytest tests/test_quotes.py::test_quote_data_default_source_is_primary tests/test_quotes.py::test_quote_data_accepts_fallback_source tests/test_quotes.py::test_quote_data_accepts_cached_source -v
```

Expected: all three `PASSED`.

- [ ] **Step 5: Run full test suite to confirm nothing regressed**

```bash
venv/bin/pytest tests/ -v
```

Expected: all existing tests pass (the new `source` field has a default, so existing `QuoteData(text=..., author=...)` constructions still work).

- [ ] **Step 6: Commit**

```bash
git add app/quotes.py tests/test_quotes.py
git commit -m "feat: add source field to QuoteData"
```

---

### Task 2: Implement three-tier fetch_quote fallback

**Files:**
- Modify: `app/quotes.py`
- Modify: `tests/test_quotes.py`

- [ ] **Step 1: Write failing tests for fallback behavior**

Add to `tests/test_quotes.py`. These use `respx` for HTTP mocking (already imported):

```python
FALLBACK_URL = "https://motivational-spark-api.vercel.app/api/quotes/random"
ZENQUOTES_URL = "https://zenquotes.io/api/random"


@respx.mock
async def test_fetch_quote_uses_fallback_on_zenquotes_failure():
    """ZenQuotes 429 → fallback API succeeds → source='fallback'."""
    import app.quotes as quotes_module
    quotes_module._last_good_quote = None  # reset module state

    respx.get(ZENQUOTES_URL).mock(return_value=httpx.Response(429))
    respx.get(FALLBACK_URL).mock(
        return_value=httpx.Response(
            200,
            json={"quote": "Keep going.", "author": "Unknown"},
        )
    )
    result = await quotes_module.fetch_quote()
    assert result.source == "fallback"
    assert result.text == "Keep going."
    assert result.author == "Unknown"


@respx.mock
async def test_fetch_quote_uses_cache_when_both_apis_fail():
    """Both APIs fail → returns last cached quote with source='cached'."""
    import app.quotes as quotes_module
    quotes_module._last_good_quote = QuoteData(
        text="Cached quote", author="Cache Author", source="primary"
    )

    respx.get(ZENQUOTES_URL).mock(return_value=httpx.Response(503))
    respx.get(FALLBACK_URL).mock(return_value=httpx.Response(503))

    result = await quotes_module.fetch_quote()
    assert result.source == "cached"
    assert result.text == "Cached quote"
    assert result.author == "Cache Author"


@respx.mock
async def test_fetch_quote_raises_when_all_fail_and_no_cache():
    """Both APIs fail and no cache → raises."""
    import app.quotes as quotes_module
    quotes_module._last_good_quote = None

    respx.get(ZENQUOTES_URL).mock(return_value=httpx.Response(503))
    respx.get(FALLBACK_URL).mock(return_value=httpx.Response(503))

    with pytest.raises(httpx.HTTPStatusError):
        await quotes_module.fetch_quote()
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
venv/bin/pytest tests/test_quotes.py::test_fetch_quote_uses_fallback_on_zenquotes_failure tests/test_quotes.py::test_fetch_quote_uses_cache_when_both_apis_fail tests/test_quotes.py::test_fetch_quote_raises_when_all_fail_and_no_cache -v
```

Expected: all three `FAILED` — `fetch_quote()` doesn't have fallback logic yet.

- [ ] **Step 3: Implement three-tier fetch_quote**

Replace `fetch_quote()` in `app/quotes.py` with:

```python
_FALLBACK_URL = "https://motivational-spark-api.vercel.app/api/quotes/random"
_last_good_quote: Optional[QuoteData] = None


async def fetch_quote() -> QuoteData:
    global _last_good_quote

    # Tier 1: ZenQuotes
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get("https://zenquotes.io/api/random")
            resp.raise_for_status()
            data = resp.json()[0]
        result = QuoteData(text=data["q"], author=data["a"], source="primary")
        _last_good_quote = result
        return result
    except Exception:
        pass

    # Tier 2: Motivational Spark
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(_FALLBACK_URL)
            resp.raise_for_status()
            data = resp.json()
        result = QuoteData(text=data["quote"], author=data["author"], source="fallback")
        _last_good_quote = result
        return result
    except Exception:
        pass

    # Tier 3: last cached quote
    if _last_good_quote is not None:
        return QuoteData(
            text=_last_good_quote.text,
            author=_last_good_quote.author,
            source="cached",
        )

    # All tiers exhausted — re-raise by trying fallback again (surfaces the error)
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(_FALLBACK_URL)
        resp.raise_for_status()
        data = resp.json()
    return QuoteData(text=data["quote"], author=data["author"], source="fallback")
```

- [ ] **Step 4: Run the new tests to confirm they pass**

```bash
venv/bin/pytest tests/test_quotes.py::test_fetch_quote_uses_fallback_on_zenquotes_failure tests/test_quotes.py::test_fetch_quote_uses_cache_when_both_apis_fail tests/test_quotes.py::test_fetch_quote_raises_when_all_fail_and_no_cache -v
```

Expected: all three `PASSED`.

- [ ] **Step 5: Run full test suite**

```bash
venv/bin/pytest tests/ -v
```

Expected: all tests pass.

- [ ] **Step 6: Commit**

```bash
git add app/quotes.py tests/test_quotes.py
git commit -m "feat: implement three-tier quote fallback with module-level cache"
```

---

### Task 3: Update colophon to show asterisk suffix

**Files:**
- Modify: `app/render_almanac.py`
- Modify: `tests/test_render_almanac.py`

- [ ] **Step 1: Write failing tests for `_colophon_label` and updated `_draw_colophon`**

Add to `tests/test_render_almanac.py` (after the existing colophon tests around line 84):

```python
from app.render_almanac import _colophon_label  # add to existing import block at top


# --- _colophon_label ---

def test_colophon_label_primary_has_no_suffix():
    label = _colophon_label("primary", "8:20 AM")
    assert label == "PRINTED IN E-INK at 8:20 AM"


def test_colophon_label_fallback_has_single_asterisk():
    label = _colophon_label("fallback", "8:20 AM")
    assert label == "PRINTED IN E-INK at 8:20 AM*"


def test_colophon_label_cached_has_double_asterisk():
    label = _colophon_label("cached", "8:20 AM")
    assert label == "PRINTED IN E-INK at 8:20 AM**"
```

Also update the two existing `_draw_colophon` tests to pass the new required `source` argument:

```python
def test_draw_colophon_classic_does_not_raise():
    img, draw = _blank_draw()
    _draw_colophon(draw, "classic", "#0c0c0c", "#c01818", source="primary")

def test_draw_colophon_modern_does_not_raise():
    img, draw = _blank_draw()
    _draw_colophon(draw, "modern", "#0c0c0c", "#0c0c0c", source="primary")
```

- [ ] **Step 2: Update the import line at the top of the test file**

Find the existing import block and add `_colophon_label`:

```python
from app.render_almanac import (
    _vfont, _colors, _roman_year,
    _draw_masthead, _draw_colophon, _draw_dateband,
    _draw_weather_panel, _draw_quote_panel,
    _colophon_label,
    render_almanac, render_almanac_sam,
    PLAYFAIR, JETBRAINS,
    W, H,
)
```

- [ ] **Step 3: Run tests to confirm they fail**

```bash
venv/bin/pytest tests/test_render_almanac.py::test_colophon_label_primary_has_no_suffix tests/test_render_almanac.py::test_colophon_label_fallback_has_single_asterisk tests/test_render_almanac.py::test_colophon_label_cached_has_double_asterisk tests/test_render_almanac.py::test_draw_colophon_classic_does_not_raise tests/test_render_almanac.py::test_draw_colophon_modern_does_not_raise -v
```

Expected: `FAILED` — `_colophon_label` doesn't exist yet and `_draw_colophon` doesn't accept `source`.

- [ ] **Step 4: Add `_colophon_label` and update `_draw_colophon` in render_almanac.py**

Add the import at the top of `app/render_almanac.py` (alongside existing imports):

```python
from app.quotes import QuoteData, QuoteSource
```

Add this helper function just before `_draw_colophon`:

```python
def _colophon_label(source: QuoteSource, timestamp: str) -> str:
    suffix = {"primary": "", "fallback": "*", "cached": "**"}[source]
    return f"PRINTED IN E-INK at {timestamp}{suffix}"
```

Update `_draw_colophon` signature and body:

```python
def _draw_colophon(
    draw: ImageDraw.ImageDraw,
    variant: str,
    fg: str,
    accent: str,
    *,
    source: QuoteSource = "primary",
) -> None:
    """Draw Zone D: Colophon (~26px tall, starts at COLON_Y)."""
    f = _vfont(JETBRAINS, 11, 400)
    cy = COLON_Y + (COLOPHON_H - 14) // 2

    draw.line([(CONTENT_X, COLON_Y), (CONTENT_RIGHT, COLON_Y)], fill=fg, width=2)

    now = datetime.now(ZoneInfo("America/Phoenix"))
    timestamp = now.strftime("%-I:%M %p")
    draw.text((CONTENT_X, cy), _colophon_label(source, timestamp), font=f, fill=fg)
    draw.text((CONTENT_RIGHT, cy), "INKY · 7.3″ · 800×480", font=f, fill=fg, anchor="rt")
```

Update the call site in `render_almanac()` (line ~331):

```python
    _draw_colophon(draw, variant, fg, accent, source=quote.source)
```

- [ ] **Step 5: Run the new and updated tests**

```bash
venv/bin/pytest tests/test_render_almanac.py::test_colophon_label_primary_has_no_suffix tests/test_render_almanac.py::test_colophon_label_fallback_has_single_asterisk tests/test_render_almanac.py::test_colophon_label_cached_has_double_asterisk tests/test_render_almanac.py::test_draw_colophon_classic_does_not_raise tests/test_render_almanac.py::test_draw_colophon_modern_does_not_raise -v
```

Expected: all `PASSED`.

- [ ] **Step 6: Run full test suite**

```bash
venv/bin/pytest tests/ -v
```

Expected: all tests pass.

- [ ] **Step 7: Commit**

```bash
git add app/render_almanac.py tests/test_render_almanac.py
git commit -m "feat: show * or ** suffix in colophon when quote API falls back"
```

---

### Task 4: Deploy

- [ ] **Step 1: Push to git**

```bash
git push
```

- [ ] **Step 2: Deploy to NAS**

Use the `/push-eink-prod` skill to rsync and rebuild the Docker image on the NAS.

- [ ] **Step 3: Verify health endpoint shows quotes_ok status**

```bash
curl -sf http://10.0.10.123:8000/health | python3 -m json.tool
```

Expected: `last_refresh` is recent, server is running.

- [ ] **Step 4: Trigger a manual refresh**

```bash
curl -sf -X POST http://10.0.10.123:8000/admin/refresh | python3 -m json.tool
```

Expected: `{"refreshed": true, "noaa_ok": true, "quotes_ok": true}` (or `false` if ZenQuotes is still down — which would confirm the fallback is now carrying the load).
