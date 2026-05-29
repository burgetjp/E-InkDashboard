# Weather Fallback Design

**Date:** 2026-05-29
**Status:** Approved

## Overview

Add a three-tier resilience pattern to `app/weather.py` so NOAA outages no longer block dashboard refreshes. Mirrors the pattern already implemented for quotes (`app/quotes.py`). Fallback API is Google Weather (`currentConditions:lookup`). Colophon indicator updated to worst-wins across both quote and weather sources.

## Data Model (`app/weather.py`)

```python
WeatherSource = Literal["primary", "fallback", "cached"]

@dataclass
class WeatherData:
    period_name: str
    temperature: int
    short_forecast: str
    detailed_forecast: str
    precip_percent: int
    source: WeatherSource = "primary"  # new field
```

## Fetch Logic (`app/weather.py`)

Module-level cache and fallback URL constant:

```python
_GOOGLE_WEATHER_URL: str = (
    os.environ.get("GOOGLE_API", "") + "&unitsSystem=IMPERIAL"
    if os.environ.get("GOOGLE_API") else ""
)
_last_good_weather: Optional[WeatherData] = None
```

Three-tier `fetch_weather(grid)`:

- **Tier 1 — NOAA:** Existing code unchanged. On success: `source="primary"`, update `_last_good_weather`, return.
- **Tier 2 — Google:** GET `_GOOGLE_WEATHER_URL`. On success: map response → `WeatherData(source="fallback")`, update `_last_good_weather`, return. Store exception as `last_exc`.
- **Tier 3 — Cache:** If `_last_good_weather is not None`, return copy with `source="cached"`. Otherwise `raise last_exc`.

## Google Field Mapping

Request: `_GOOGLE_WEATHER_URL` (includes `&unitsSystem=IMPERIAL` — all temperatures returned in °F).

| `WeatherData` field | Google response path | Notes |
|---|---|---|
| `period_name` | `isDaytime` | `"Tonight"` if false, else `"Today"` |
| `temperature` | `currentConditionsHistory.maxTemperature.degrees` | Today's recorded high, already °F — `round()` to int |
| `short_forecast` | `weatherCondition.description.text` | e.g. `"Sunny"` — maps directly to icon keywords |
| `detailed_forecast` | synthesized | `f"{description}. High near {temp}°F. Wind {wind_speed} mph."` |
| `precip_percent` | `precipitation.probability.percent` | integer |

Wind speed from `wind.speed.value` (mph via IMPERIAL).

## Colophon (`app/render_almanac.py`)

Worst-wins: the displayed suffix reflects the worst source across both quote and weather.

Ranking: `primary` (0) < `fallback` (1) < `cached` (2).

```python
_SOURCE_RANK = {"primary": 0, "fallback": 1, "cached": 2}

def _colophon_label(quote_source: QuoteSource, weather_source: WeatherSource, timestamp: str) -> str:
    rank = max(_SOURCE_RANK[quote_source], _SOURCE_RANK[weather_source])
    return f"PRINTED IN E-INK at {timestamp}{('', '*', '**')[rank]}"
```

`_draw_colophon` gains `weather_source: WeatherSource = "primary"` kwarg (rename existing `source` → `quote_source`).

`render_almanac` call site:
```python
_draw_colophon(draw, variant, fg, accent, quote_source=quote.source, weather_source=weather.source)
```

`WeatherSource` imported from `app.weather` in `render_almanac.py`.

Sam's `render_almanac_sam` colophon ("I LOVE YOU") is unchanged.

## Scheduler (`app/scheduler.py`)

No changes. `fetch_weather()` only raises when all three tiers fail, so `weather is None` guard continues to apply only on first boot. `noaa_ok` flag semantics unchanged.

## Configuration

`GOOGLE_API` env var already present in `.env` and Docker env. Contains full URL with API key and Phoenix coordinates (`33.4484, -112.0740`). Code appends `&unitsSystem=IMPERIAL` at module load — never stored in source.

## Tests

### `tests/test_weather.py` — new cases

- `test_weather_data_default_source_is_primary` — `WeatherData(...).source == "primary"`
- `test_fetch_weather_uses_fallback_on_noaa_failure` — mock NOAA 503, Google 200 → `source="fallback"`, correct field values
- `test_fetch_weather_uses_cache_when_both_apis_fail` — mock both 503, pre-set `_last_good_weather` → `source="cached"`
- `test_fetch_weather_raises_when_all_fail_and_no_cache` — mock both 503, `_last_good_weather=None` → raises

Mocking strategy: monkeypatch `app.weather._GOOGLE_WEATHER_URL` to a test URL, mock with `respx`.

### `tests/test_render_almanac.py` — updates + new

Update existing `test_colophon_label_*` tests to pass two source args.

New worst-wins tests:
- weather `"fallback"` + quote `"primary"` → `*`
- quote `"cached"` + weather `"primary"` → `**`
- quote `"fallback"` + weather `"cached"` → `**`

## Deployment

Per project convention: rsync `eink-dashboard/app/` → `eink-dashboard/synology/app/` before running `/push-eink-prod`. Docker reads `GOOGLE_API` from env at container start.
