# Quote Fallback API Design

**Date:** 2026-05-29
**Status:** Approved

## Problem

ZenQuotes outages block the entire dashboard refresh. When `fetch_quote()` raises, `scheduler.py` bails out early without updating the image cache — leaving the display frozen at the last successful render with no fresh weather data.

## Goal

Make the quote fetch resilient enough that the dashboard image always regenerates. The display's timestamp tells the user whether weather data is fresh; a suffix on the timestamp signals quote-source degradation.

---

## Data Model

### `QuoteData` (`app/quotes.py`)

Add a `source` field:

```python
from typing import Literal

QuoteSource = Literal["primary", "fallback", "cached"]

@dataclass
class QuoteData:
    text: str
    author: str
    source: QuoteSource = "primary"
```

---

## Fetch Logic (`app/quotes.py`)

A module-level variable persists the last successful quote across scheduler runs:

```python
_last_good_quote: Optional[QuoteData] = None
```

Three-tier fallback in `fetch_quote()`:

| Tier | Source | Behavior |
|------|--------|----------|
| 1 | ZenQuotes (`https://zenquotes.io/api/random`) | `source="primary"`, updates `_last_good_quote` |
| 2 | Motivational Spark (`https://motivational-spark-api.vercel.app/api/quotes/random`) | `source="fallback"`, updates `_last_good_quote` |
| 3 | `_last_good_quote` cache | `source="cached"`, no update |
| — | All fail, no cache | raise last exception |

Field mapping for Motivational Spark: `quote` → `text`, `author` → `author`.

Both successful tiers (primary and fallback) update `_last_good_quote` so the cache stays as fresh as possible.

The only hard-stop is tier 4: first-ever boot before any quote has succeeded. That preserves today's behavior and is acceptable — the display shows "Dashboard starting…" fallback PNG.

---

## Scheduler (`app/scheduler.py`)

No code changes. The existing guard `if weather is None or quote is None` no longer triggers on quote failure because `fetch_quote()` now returns a cached quote instead of raising. NOAA failure still bails out as before.

---

## Renderer (`app/render_almanac.py`)

`_draw_colophon()` gains a `source: QuoteSource` parameter:

| `source` | Timestamp suffix |
|----------|-----------------|
| `"primary"` | *(none)* — e.g. `PRINTED IN E-INK at 8:20 AM` |
| `"fallback"` | `*` — e.g. `PRINTED IN E-INK at 8:20 AM*` |
| `"cached"` | `**` — e.g. `PRINTED IN E-INK at 8:20 AM**` |

`render_almanac()` passes `quote.source` to `_draw_colophon()`. `render_almanac_sam()` is unchanged — Sam's colophon shows `I LOVE YOU` with no timestamp.

---

## Tests

### `tests/test_quotes.py`

- **Existing:** `test_fetch_quote_success`, `test_fetch_quote_http_error` — update signatures as needed
- **New:** `test_fetch_quote_uses_fallback_on_zenquotes_failure` — ZenQuotes 429, fallback 200, returns `source="fallback"`
- **New:** `test_fetch_quote_uses_cache_when_both_fail` — both 429, `_last_good_quote` pre-seeded, returns `source="cached"`
- **New:** `test_fetch_quote_raises_when_all_fail_and_no_cache` — both fail, no cache, raises

### `tests/test_render_almanac.py`

- **New:** render with `source="fallback"` quote, assert colophon bytes contain no double-asterisk but does contain a single `*` character region
- **New:** render with `source="cached"` quote, assert `**` appears in colophon

---

## Out of Scope

- NOAA fallback (separate concern)
- Sam's display asterisk indicator
- Persisting `_last_good_quote` across server restarts (Docker restart resets it; acceptable)
