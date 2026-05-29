# Weather Fallback Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a three-tier fallback to `fetch_weather()` so NOAA outages degrade gracefully to Google Weather, then to the last cached reading.

**Architecture:** Mirrors the pattern already in `app/quotes.py` — module-level cache variable, module-level Google URL constant built from `GOOGLE_API` env var, three-tier try/except with stored exception re-raise. Colophon updated to worst-wins across both quote and weather sources.

**Tech Stack:** Python 3.12, httpx, pydantic-settings, pytest + pytest-asyncio (auto mode) + respx for HTTP mocking

---

## File Map

| File | Change |
|---|---|
| `app/weather.py` | Add `WeatherSource`, `source` field, module vars, three-tier fetch logic |
| `app/render_almanac.py` | Add `_SOURCE_RANK`, update `_colophon_label` / `_draw_colophon` / `render_almanac` call |
| `tests/test_weather.py` | Update `test_fetch_weather_http_error`; add 4 new tests |
| `tests/test_render_almanac.py` | Update 5 existing tests; add 3 new worst-wins tests |
| `docker-compose.yml` | Add `GOOGLE_API` to `environment:` |
| `synology/docker-compose.yml` | Add `GOOGLE_API` to `environment:` |

> All paths relative to `eink-dashboard/`. Run all commands from that directory.

---

## Task 1: WeatherSource type and source field on WeatherData

**Files:**
- Modify: `app/weather.py`
- Test: `tests/test_weather.py`

- [ ] **Step 1: Write three failing tests**

Add to the bottom of `tests/test_weather.py`:

```python
def test_weather_data_default_source_is_primary():
    w = WeatherData(
        period_name="Today",
        temperature=91,
        short_forecast="Sunny",
        detailed_forecast="Sunny. High near 91.",
        precip_percent=0,
    )
    assert w.source == "primary"


def test_weather_data_accepts_fallback_source():
    w = WeatherData(
        period_name="Today",
        temperature=91,
        short_forecast="Sunny",
        detailed_forecast="Sunny.",
        precip_percent=0,
        source="fallback",
    )
    assert w.source == "fallback"


def test_weather_data_accepts_cached_source():
    w = WeatherData(
        period_name="Today",
        temperature=91,
        short_forecast="Sunny",
        detailed_forecast="Sunny.",
        precip_percent=0,
        source="cached",
    )
    assert w.source == "cached"
```

- [ ] **Step 2: Run to confirm failure**

```bash
venv/bin/pytest tests/test_weather.py::test_weather_data_default_source_is_primary -v
```

Expected: `FAILED` — `WeatherData.__init__() got an unexpected keyword argument 'source'`

- [ ] **Step 3: Update `app/weather.py`**

Replace the entire file with:

```python
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Literal, Optional

import httpx

WeatherSource = Literal["primary", "fallback", "cached"]


@dataclass
class WeatherData:
    period_name: str
    temperature: int
    short_forecast: str
    detailed_forecast: str
    precip_percent: int
    source: WeatherSource = "primary"


_google_api = os.environ.get("GOOGLE_API", "")
_GOOGLE_WEATHER_URL: str = f"{_google_api}&unitsSystem=IMPERIAL" if _google_api else ""
_last_good_weather: Optional[WeatherData] = None


async def fetch_weather(grid: str) -> WeatherData:
    url = f"https://api.weather.gov/gridpoints/{grid}/forecast"
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(url, headers={"User-Agent": "InkyDashboard/1.0"})
        resp.raise_for_status()
        period = resp.json()["properties"]["periods"][0]
    return WeatherData(
        period_name=period["name"],
        temperature=period["temperature"],
        short_forecast=period["shortForecast"],
        detailed_forecast=period["detailedForecast"],
        precip_percent=period.get("probabilityOfPrecipitation", {}).get("value") or 0,
    )
```

> Note: `fetch_weather` is still single-tier here — the three-tier logic comes in Task 2. This step only adds the model.

- [ ] **Step 4: Run to confirm the three new tests pass**

```bash
venv/bin/pytest tests/test_weather.py::test_weather_data_default_source_is_primary tests/test_weather.py::test_weather_data_accepts_fallback_source tests/test_weather.py::test_weather_data_accepts_cached_source -v
```

Expected: all three `PASSED`

- [ ] **Step 5: Run full suite to confirm no regressions**

```bash
venv/bin/pytest tests/ -v
```

Expected: all previously passing tests still `PASSED`

- [ ] **Step 6: Commit**

```bash
git add app/weather.py tests/test_weather.py
git commit -m "feat: add WeatherSource type and source field to WeatherData"
```

---

## Task 2: Three-tier fetch_weather with Google fallback

**Files:**
- Modify: `app/weather.py`
- Test: `tests/test_weather.py`

- [ ] **Step 1: Update `test_fetch_weather_http_error` to work with the new three-tier logic**

The existing test will break after Task 2 because when NOAA fails, Tier 2 will attempt the Google URL. In tests, `_GOOGLE_WEATHER_URL` is `""` (no env var set), so httpx raises `UnsupportedProtocol` instead of `HTTPStatusError`. Fix by monkeypatching the URL and mocking a 503 from Google too.

Replace the existing `test_fetch_weather_http_error` in `tests/test_weather.py`:

```python
@respx.mock
async def test_fetch_weather_http_error(monkeypatch):
    import app.weather as weather_module
    monkeypatch.setattr(weather_module, "_last_good_weather", None)
    monkeypatch.setattr(weather_module, "_GOOGLE_WEATHER_URL", "https://weather.googleapis.com/v1/fake")
    respx.get("https://api.weather.gov/gridpoints/PSR/166,61/forecast").mock(
        return_value=httpx.Response(503)
    )
    respx.get("https://weather.googleapis.com/v1/fake").mock(
        return_value=httpx.Response(503)
    )
    with pytest.raises(httpx.HTTPStatusError):
        await fetch_weather("PSR/166,61")
```

- [ ] **Step 2: Add the four new fallback tests**

Add a `GOOGLE_MOCK_URL` constant and `GOOGLE_RESPONSE` fixture at the top of the test file (after the existing `NOAA_RESPONSE`), then append the four new tests:

Add after `NOAA_RESPONSE`:

```python
GOOGLE_MOCK_URL = "https://weather.googleapis.com/v1/fake"

GOOGLE_RESPONSE = {
    "isDaytime": True,
    "weatherCondition": {
        "description": {"text": "Sunny"},
    },
    "currentConditionsHistory": {
        "maxTemperature": {"degrees": 90.3, "unit": "FAHRENHEIT"},
    },
    "precipitation": {
        "probability": {"percent": 5},
    },
    "wind": {
        "speed": {"value": 11, "unit": "MILES_PER_HOUR"},
    },
}
```

Add to the bottom of the file:

```python
@respx.mock
async def test_fetch_weather_uses_fallback_on_noaa_failure(monkeypatch):
    import app.weather as weather_module
    monkeypatch.setattr(weather_module, "_last_good_weather", None)
    monkeypatch.setattr(weather_module, "_GOOGLE_WEATHER_URL", GOOGLE_MOCK_URL)
    respx.get("https://api.weather.gov/gridpoints/PSR/166,61/forecast").mock(
        return_value=httpx.Response(503)
    )
    respx.get(GOOGLE_MOCK_URL).mock(
        return_value=httpx.Response(200, json=GOOGLE_RESPONSE)
    )
    result = await fetch_weather("PSR/166,61")
    assert result.source == "fallback"
    assert result.temperature == 90
    assert result.short_forecast == "Sunny"
    assert result.period_name == "Today"
    assert result.precip_percent == 5
    assert "High near 90°F" in result.detailed_forecast


@respx.mock
async def test_fetch_weather_uses_cache_when_both_apis_fail(monkeypatch):
    import app.weather as weather_module
    cached = WeatherData(
        period_name="Today",
        temperature=88,
        short_forecast="Cloudy",
        detailed_forecast="Cloudy.",
        precip_percent=10,
        source="primary",
    )
    monkeypatch.setattr(weather_module, "_last_good_weather", cached)
    monkeypatch.setattr(weather_module, "_GOOGLE_WEATHER_URL", GOOGLE_MOCK_URL)
    respx.get("https://api.weather.gov/gridpoints/PSR/166,61/forecast").mock(
        return_value=httpx.Response(503)
    )
    respx.get(GOOGLE_MOCK_URL).mock(return_value=httpx.Response(503))
    result = await fetch_weather("PSR/166,61")
    assert result.source == "cached"
    assert result.temperature == 88
    assert result.short_forecast == "Cloudy"


@respx.mock
async def test_fetch_weather_raises_when_all_fail_and_no_cache(monkeypatch):
    import app.weather as weather_module
    monkeypatch.setattr(weather_module, "_last_good_weather", None)
    monkeypatch.setattr(weather_module, "_GOOGLE_WEATHER_URL", GOOGLE_MOCK_URL)
    respx.get("https://api.weather.gov/gridpoints/PSR/166,61/forecast").mock(
        return_value=httpx.Response(503)
    )
    respx.get(GOOGLE_MOCK_URL).mock(return_value=httpx.Response(503))
    with pytest.raises(httpx.HTTPStatusError):
        await fetch_weather("PSR/166,61")


@respx.mock
async def test_fetch_weather_fallback_tonight_when_not_daytime(monkeypatch):
    import app.weather as weather_module
    monkeypatch.setattr(weather_module, "_last_good_weather", None)
    monkeypatch.setattr(weather_module, "_GOOGLE_WEATHER_URL", GOOGLE_MOCK_URL)
    night_response = {**GOOGLE_RESPONSE, "isDaytime": False}
    respx.get("https://api.weather.gov/gridpoints/PSR/166,61/forecast").mock(
        return_value=httpx.Response(503)
    )
    respx.get(GOOGLE_MOCK_URL).mock(
        return_value=httpx.Response(200, json=night_response)
    )
    result = await fetch_weather("PSR/166,61")
    assert result.period_name == "Tonight"
```

- [ ] **Step 3: Run tests to confirm they all fail**

```bash
venv/bin/pytest tests/test_weather.py::test_fetch_weather_uses_fallback_on_noaa_failure tests/test_weather.py::test_fetch_weather_uses_cache_when_both_apis_fail tests/test_weather.py::test_fetch_weather_raises_when_all_fail_and_no_cache tests/test_weather.py::test_fetch_weather_fallback_tonight_when_not_daytime -v
```

Expected: all `FAILED` — `fetch_weather` still single-tier

- [ ] **Step 4: Replace `fetch_weather` in `app/weather.py` with the three-tier implementation**

Replace the `fetch_weather` function (keep everything above it unchanged):

```python
async def fetch_weather(grid: str) -> WeatherData:
    global _last_good_weather

    # Tier 1: NOAA
    try:
        url = f"https://api.weather.gov/gridpoints/{grid}/forecast"
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url, headers={"User-Agent": "InkyDashboard/1.0"})
            resp.raise_for_status()
            period = resp.json()["properties"]["periods"][0]
        result = WeatherData(
            period_name=period["name"],
            temperature=period["temperature"],
            short_forecast=period["shortForecast"],
            detailed_forecast=period["detailedForecast"],
            precip_percent=period.get("probabilityOfPrecipitation", {}).get("value") or 0,
            source="primary",
        )
        _last_good_weather = result
        return result
    except Exception:
        pass

    # Tier 2: Google Weather
    last_exc: Optional[Exception] = None
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(_GOOGLE_WEATHER_URL)
            resp.raise_for_status()
            data = resp.json()
        desc = data["weatherCondition"]["description"]["text"]
        temp = round(data["currentConditionsHistory"]["maxTemperature"]["degrees"])
        wind = data["wind"]["speed"]["value"]
        result = WeatherData(
            period_name="Tonight" if not data["isDaytime"] else "Today",
            temperature=temp,
            short_forecast=desc,
            detailed_forecast=f"{desc}. High near {temp}°F. Wind {wind} mph.",
            precip_percent=data["precipitation"]["probability"]["percent"],
            source="fallback",
        )
        _last_good_weather = result
        return result
    except Exception as exc:
        last_exc = exc

    # Tier 3: module cache
    if _last_good_weather is not None:
        return WeatherData(
            period_name=_last_good_weather.period_name,
            temperature=_last_good_weather.temperature,
            short_forecast=_last_good_weather.short_forecast,
            detailed_forecast=_last_good_weather.detailed_forecast,
            precip_percent=_last_good_weather.precip_percent,
            source="cached",
        )

    raise last_exc  # type: ignore[misc]
```

- [ ] **Step 5: Run all weather tests**

```bash
venv/bin/pytest tests/test_weather.py -v
```

Expected: all `PASSED`

- [ ] **Step 6: Run full suite**

```bash
venv/bin/pytest tests/ -v
```

Expected: all `PASSED`

- [ ] **Step 7: Commit**

```bash
git add app/weather.py tests/test_weather.py
git commit -m "feat: add Google Weather fallback and module cache to fetch_weather"
```

---

## Task 3: Colophon worst-wins across quote and weather sources

**Files:**
- Modify: `app/render_almanac.py`
- Test: `tests/test_render_almanac.py`

- [ ] **Step 1: Update the five existing tests that reference `_colophon_label` or `_draw_colophon`**

In `tests/test_render_almanac.py`, find and replace these five tests:

```python
# REPLACE:
def test_draw_colophon_classic_does_not_raise():
    img, draw = _blank_draw()
    _draw_colophon(draw, "classic", "#0c0c0c", "#c01818", source="primary")

def test_draw_colophon_modern_does_not_raise():
    img, draw = _blank_draw()
    _draw_colophon(draw, "modern", "#0c0c0c", "#0c0c0c", source="primary")

def test_colophon_label_primary_has_no_suffix():
    label = _colophon_label("primary", "8:20 AM")
    assert label == "PRINTED IN E-INK at 8:20 AM"

def test_colophon_label_fallback_has_single_asterisk():
    label = _colophon_label("fallback", "8:20 AM")
    assert label == "PRINTED IN E-INK at 8:20 AM*"

def test_colophon_label_cached_has_double_asterisk():
    label = _colophon_label("cached", "8:20 AM")
    assert label == "PRINTED IN E-INK at 8:20 AM**"

# WITH:
def test_draw_colophon_classic_does_not_raise():
    img, draw = _blank_draw()
    _draw_colophon(draw, "classic", "#0c0c0c", "#c01818", quote_source="primary", weather_source="primary")

def test_draw_colophon_modern_does_not_raise():
    img, draw = _blank_draw()
    _draw_colophon(draw, "modern", "#0c0c0c", "#0c0c0c", quote_source="primary", weather_source="primary")

def test_colophon_label_primary_has_no_suffix():
    label = _colophon_label("primary", "primary", "8:20 AM")
    assert label == "PRINTED IN E-INK at 8:20 AM"

def test_colophon_label_fallback_has_single_asterisk():
    label = _colophon_label("fallback", "primary", "8:20 AM")
    assert label == "PRINTED IN E-INK at 8:20 AM*"

def test_colophon_label_cached_has_double_asterisk():
    label = _colophon_label("cached", "primary", "8:20 AM")
    assert label == "PRINTED IN E-INK at 8:20 AM**"
```

- [ ] **Step 2: Add three new worst-wins tests**

Append to `tests/test_render_almanac.py`:

```python
def test_colophon_label_weather_fallback_beats_quote_primary():
    label = _colophon_label("primary", "fallback", "8:20 AM")
    assert label == "PRINTED IN E-INK at 8:20 AM*"


def test_colophon_label_weather_cached_beats_quote_primary():
    label = _colophon_label("primary", "cached", "8:20 AM")
    assert label == "PRINTED IN E-INK at 8:20 AM**"


def test_colophon_label_worst_wins_mixed():
    label = _colophon_label("fallback", "cached", "8:20 AM")
    assert label == "PRINTED IN E-INK at 8:20 AM**"
```

- [ ] **Step 3: Run to confirm failures**

```bash
venv/bin/pytest tests/test_render_almanac.py -k "colophon" -v
```

Expected: all eight colophon tests `FAILED` — wrong number of args / wrong kwarg names

- [ ] **Step 4: Update `app/render_almanac.py`**

**4a.** Change the import on line 13 from:
```python
from app.weather import WeatherData
```
to:
```python
from app.weather import WeatherData, WeatherSource
```

**4b.** Add `_SOURCE_RANK` immediately after the `QuoteSource` import (after line 13, before the canvas constants):
```python
_SOURCE_RANK: dict[str, int] = {"primary": 0, "fallback": 1, "cached": 2}
```

**4c.** Replace `_colophon_label`:
```python
def _colophon_label(quote_source: QuoteSource, weather_source: WeatherSource, timestamp: str) -> str:
    rank = max(_SOURCE_RANK[quote_source], _SOURCE_RANK[weather_source])
    return f"PRINTED IN E-INK at {timestamp}{('', '*', '**')[rank]}"
```

**4d.** Replace `_draw_colophon` signature and body:
```python
def _draw_colophon(
    draw: ImageDraw.ImageDraw,
    variant: str,
    fg: str,
    accent: str,
    *,
    quote_source: QuoteSource = "primary",
    weather_source: WeatherSource = "primary",
) -> None:
    """Draw Zone D: Colophon (~26px tall, starts at COLON_Y)."""
    f = _vfont(JETBRAINS, 11, 400)
    cy = COLON_Y + (COLOPHON_H - 14) // 2

    draw.line([(CONTENT_X, COLON_Y), (CONTENT_RIGHT, COLON_Y)], fill=fg, width=2)

    now = datetime.now(ZoneInfo("America/Phoenix"))
    timestamp = now.strftime("%-I:%M %p")
    draw.text((CONTENT_X, cy), _colophon_label(quote_source, weather_source, timestamp), font=f, fill=fg)
    draw.text((CONTENT_RIGHT, cy), "INKY · 7.3″ · 800×480", font=f, fill=fg, anchor="rt")
```

**4e.** In `render_almanac`, update the `_draw_colophon` call (near the bottom of the function):
```python
_draw_colophon(draw, variant, fg, accent, quote_source=quote.source, weather_source=weather.source)
```

- [ ] **Step 5: Run colophon tests**

```bash
venv/bin/pytest tests/test_render_almanac.py -k "colophon" -v
```

Expected: all eight `PASSED`

- [ ] **Step 6: Run full suite**

```bash
venv/bin/pytest tests/ -v
```

Expected: all `PASSED`

- [ ] **Step 7: Commit**

```bash
git add app/render_almanac.py tests/test_render_almanac.py
git commit -m "feat: colophon worst-wins across quote and weather sources"
```

---

## Task 4: Docker Compose env var and final verification

**Files:**
- Modify: `docker-compose.yml`
- Modify: `synology/docker-compose.yml`

- [ ] **Step 1: Add `GOOGLE_API` to `docker-compose.yml`**

In `docker-compose.yml`, the `environment:` block currently ends at `REFRESH_HOUR_INTERVAL=1`. Add one line:

```yaml
    environment:
      - PORT=8000
      - NOAA_GRID=PSR/166,61
      - REFRESH_HOUR_INTERVAL=1
      - GOOGLE_API
```

`- GOOGLE_API` (no `=`) tells Docker Compose to pass the value through from the host environment. Docker Compose auto-loads `.env` from its own directory — if you need it for local Docker testing, copy the `GOOGLE_API` line from the project-root `.env` into `eink-dashboard/.env`.

- [ ] **Step 2: Apply the same change to `synology/docker-compose.yml`**

```yaml
    environment:
      - PORT=8000
      - NOAA_GRID=PSR/166,61
      - REFRESH_HOUR_INTERVAL=1
      - GOOGLE_API
```

- [ ] **Step 3: Run the full test suite one final time**

```bash
venv/bin/pytest tests/ -v
```

Expected: all `PASSED`

- [ ] **Step 4: Commit**

```bash
git add docker-compose.yml synology/docker-compose.yml
git commit -m "chore: pass GOOGLE_API env var into Docker container"
```

---

## Deploy

After all tasks pass:

1. Rsync app to Synology: `eink-dashboard/app/` → `eink-dashboard/synology/app/`
2. Run `/push-eink-prod` to build and restart the container on the NAS
3. Confirm the dashboard loads at `http://10.0.10.123:8000/health`
