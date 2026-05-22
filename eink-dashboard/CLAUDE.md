# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Run all tests
venv/bin/pytest tests/

# Run a single test file
venv/bin/pytest tests/test_weather.py -v

# Run a single test
venv/bin/pytest tests/test_icons.py::test_select_icon_name_night -v

# Start the server locally
venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000

# Build and run in Docker
docker compose up --build
```

## Architecture

FastAPI server that generates PNG dashboard images for two Pimoroni Inky Impression e-ink displays. All data is fetched hourly by APScheduler and cached in memory — no database, no disk I/O on requests.

**Request path:** `GET /dashboard/joe.png` → `cache.get_joe()` → returns cached bytes directly.

**Refresh path:** APScheduler fires at `:00` → `refresh_dashboard()` → `fetch_weather()` + `fetch_quote()` + `load_all_icons()` → `render_joe()` + `render_sam()` → `cache.store()`.

**Key modules:**
- `app/main.py` — FastAPI app, lifespan (startup refresh + scheduler), three endpoints
- `app/scheduler.py` — `refresh_dashboard()` coroutine, APScheduler setup
- `app/cache.py` — `DashboardCache` dataclass; `get_joe()`/`get_sam()` return fallback PNG on first boot
- `app/render_joe.py` — 800×480 white/blue layout (weather left, quote right)
- `app/render_sam.py` — 600×400 lavender/purple layout (quote left, weather right)
- `app/icons.py` — 18-condition `ICON_MAPPING`; `load_all_icons()` fetches Basmilius SVGs via HTTP and rasterizes with cairosvg
- `app/weather.py` / `app/quotes.py` — thin async clients for NOAA and ZenQuotes
- `app/draw_utils.py` — `wrap_text()` for Pillow

**Icon mapping order matters:** multi-word keywords (e.g. `"mostly sunny"`) must appear before their single-word components (`"sunny"`) in `ICON_MAPPING` to prevent false early matches.

**Python environment:** Use `venv/bin/python` (Python 3.12 via Homebrew). The system Python 3.9 cannot load `cairosvg` because cairocffi cannot find libcairo on macOS without the venv.

**Fonts:** Inter Regular and Bold are bundled at `assets/fonts/`. No external font calls at runtime.

**Pi-side:** `pi/dailyDash.sh` curls the PNG from the NAS and calls the existing `dailyEink.py` + `dailyClear.py` (those scripts are unchanged).
