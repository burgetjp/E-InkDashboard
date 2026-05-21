# E-Ink Dashboard — Documentation Design Spec
**Date:** 2026-05-21  
**Status:** Approved

---

## Overview

Create a single self-contained HTML documentation file (`docs/index.html`) for the E-Ink Dashboard project. The format mirrors the K&R Feeds architecture doc: Tailwind CSS (CDN), Mermaid diagrams (CDN), a fixed left sidebar with section navigation, and a main content area with cards, tables, and code blocks.

The doc serves three audiences simultaneously:
- **Personal reference** — quick lookup of config values, module APIs, color palettes
- **Future Claude Code sessions** — enough architecture context to extend or debug the app without re-reading the source
- **New collaborators** — full picture from hardware to deployment

---

## Output

A single file: `docs/index.html`

No build step, no dependencies beyond CDN scripts (Tailwind, Mermaid). Opens directly in any browser.

---

## Visual Style

Matches K&R Feeds doc exactly:
- Fixed top navbar (`h-12`, white, border-bottom) — project name left-aligned
- Fixed left sidebar (`160px` wide, white, border-right) — 8 section buttons with active state highlight (`#EBF3FF` / `#4A9EFF`)
- Main content area (`max-width: 820px`, `px-12 py-10`, scrollable)
- Section show/hide via `hidden` attribute — JS swaps on sidebar click
- Mermaid diagrams lazy-rendered on section activation (same pattern as K&R)
- Color tokens: slate palette for text/borders, `#4A9EFF` as accent
- `table`, `code`, `pre`, `h1`/`h2`/`h3` styled identically to K&R

---

## Sections

### 1. Overview
- Page title: "E-Ink Dashboard"
- Subtitle: "FastAPI + Pillow dashboard image server — architecture reference"
- Summary cards (2×2 grid):
  - **Platform:** Python 3.12 · FastAPI · Pillow · Docker
  - **Entry point:** `app/main.py` — FastAPI lifespan starts scheduler + initial refresh
  - **Displays:** Joe 800×480 (white/blue) · Sam 600×400 (lavender/purple)
  - **Data sources:** NOAA Weather · ZenQuotes · Basmilius icons (SVG → PNG)
- Key design principles (bullet list):
  - In-memory cache — no disk I/O on PNG requests
  - APScheduler fires hourly at `:00` — Pi-side scripts unchanged
  - On API failure: keep previous cached image, log warning
  - First-boot fallback PNG if both APIs down at startup

### 2. Architecture
Three Mermaid diagrams:

**System-level diagram** — hardware and network topology:
```
Pi (cron) → GET /dashboard/joe.png → Synology NAS (Docker :8000) → NOAA / ZenQuotes / Basmilius
```

**Request flow diagram** — what happens on a PNG request:
```
GET /dashboard/joe.png → joe_png() → cache.get_joe() → return bytes (image/png)
```

**Refresh cycle diagram** — what APScheduler triggers every hour:
```
CronTrigger(:00) → refresh_dashboard() → fetch_weather() + fetch_quote() → load_all_icons() (if empty) → render_joe() + render_sam() → cache.store()
```

### 3. Modules
One card per `app/*.py` file. Each card: module name (as `code`), file path, one-sentence description, and a table of public symbols (class/function name · signature · purpose).

Modules covered:
- `app/main.py` — FastAPI app, lifespan, 3 routes
- `app/config.py` — `Settings` (pydantic-settings), `settings` singleton; 3 env vars
- `app/cache.py` — `DashboardCache` dataclass; `get_joe()`, `get_sam()`, `store()`; fallback PNG
- `app/weather.py` — `WeatherData` dataclass; `fetch_weather(grid)` async
- `app/quotes.py` — `QuoteData` dataclass; `fetch_quote()` async
- `app/icons.py` — `ICON_MAPPING`; `select_icon_name(short_forecast, period_name)`; `rasterize_svg(name, size)`; `load_all_icons(size)`
- `app/accent.py` — `select_accent(short_forecast) → (temp_color, icon_bg_color)`
- `app/draw_utils.py` — `wrap_text(draw, text, font, max_width) → list[str]`
- `app/render_joe.py` — `render_joe(weather, quote, icon) → Image` — 800×480 dark layout
- `app/render_sam.py` — `render_sam(weather, quote, icon) → Image` — 600×400 dark layout
- `app/scheduler.py` — `refresh_dashboard(cache, noaa_grid)` coroutine; `start_scheduler(noaa_grid)`; APScheduler setup

### 4. API Endpoints
Table: Method · Path · Response type · Notes

| Method | Path | Response | Notes |
|---|---|---|---|
| GET | `/dashboard/joe.png` | `image/png` | 800×480, Joe profile |
| GET | `/dashboard/sam.png` | `image/png` | 600×400, Sam profile |
| GET | `/health` | `application/json` | Last refresh timestamp + API status |

`/health` response fields breakdown:
- `last_refresh` — ISO-8601 UTC timestamp or `null` on first boot
- `noaa_ok` — `true` if last NOAA fetch succeeded
- `quotes_ok` — `true` if last ZenQuotes fetch succeeded

### 5. Data Sources
Three subsections, each as a card with a details table:

**NOAA Weather API**
- Endpoint: `https://api.weather.gov/gridpoints/{NOAA_GRID}/forecast`
- Default grid: `PSR/166,61`
- Fields used: `periods[0].name`, `.temperature`, `.shortForecast`, `.detailedForecast`, `.probabilityOfPrecipitation.value`
- Error behavior: raise `HTTPStatusError` → scheduler catches, keeps previous cache

**ZenQuotes**
- Endpoint: `https://zenquotes.io/api/random`
- Fields used: `[0].q` (quote text), `[0].a` (author)
- Error behavior: same as NOAA

**Basmilius Weather Icons**
- Source: GitHub raw SVG (MIT license)
- Strategy: SVGs fetched and rasterized at server startup via cairosvg; cached in memory
- Full 18-condition icon mapping table (keywords · day icon · night icon)
- Night detection: `period_name` is "Tonight" or "Overnight"

### 6. Display Profiles
Two side-by-side subsections (Joe / Sam) each with:
- Dimensions
- Color palette table (element · hex value)
- Layout description (ASCII art from the dark redesign spec)

Plus a unified **Condition Accent Colors** table (from `accent.py`):
- Condition keywords → temp color → icon bg color
- 10 condition groups + fallback

### 7. Configuration
**Environment variables table:**

| Variable | Default | Purpose |
|---|---|---|
| `PORT` | `8000` | uvicorn listen port |
| `NOAA_GRID` | `PSR/166,61` | NOAA gridpoint for Phoenix area |
| `REFRESH_HOUR_INTERVAL` | `1` | Scheduler interval (hours) |

**Python environment note:** Use `venv/bin/python` (Python 3.12). System Python 3.9 cannot load cairosvg.

**Synology deployment note:** `synology/` directory contains a parallel copy of the app tuned for the Synology NAS environment.

### 8. Deployment
**Quick reference commands** (code block):
```bash
# Run tests
venv/bin/pytest tests/

# Start server locally  
venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000

# Build and run in Docker
docker compose up --build
```

**Synology setup:** docker-compose in `synology/`, port 8000, env vars set in compose file.

**Pi-side setup:**
- Cron calls `pi/dailyDash.sh` at `:30`
- Script: `curl` the PNG from NAS → `dailyClear.py` → `dailyEink.py`
- `killFirefox.sh` no longer needed (old Node.js pipeline artifact)

**Full data flow Mermaid diagram** (same concept as K&R deployment diagram):
```
Pi cron :30 → curl /dashboard/joe.png → FastAPI (Synology :8000)
                                              ↑
                             APScheduler (:00) → NOAA + ZenQuotes + Basmilius
```

---

## Out of Scope

- Dark/light theme toggle on the doc itself
- Search functionality
- Auto-generation from source (the doc is hand-authored and maintained)
- Multiple language versions
