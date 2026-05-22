# E-Ink Dashboard — Design Spec
**Date:** 2026-04-30  
**Status:** Approved

---

## Overview

Replace an existing Node.js/Express + Firefox headless screenshot pipeline with a Python FastAPI server that generates dashboard PNGs directly using Pillow. The server runs in Docker on a Synology NAS. A Raspberry Pi fetches the PNG on a cron schedule and writes it to a Pimoroni Inky Impression e-ink display using the existing Pi-side scripts (unchanged).

---

## System Architecture

```
Synology NAS (Docker)                        Raspberry Pi
┌─────────────────────────────────┐          ┌────────────────────────────────┐
│  FastAPI app (port 8000)        │          │  Cron :00 → dailyImage.sh      │
│                                 │          │  Cron :30 → dailyDash.sh       │
│  APScheduler (hourly at :00)    │  HTTP    │    curl /dashboard/joe.png     │
│  ├─ Fetch NOAA weather          │◄─────────│    (or sam.png)                │
│  ├─ Fetch ZenQuotes quote       │          │                                │
│  ├─ Fetch Basmilius icon PNG    │          │  dailyClear.py  (unchanged)    │
│  └─ Render & cache both PNGs   │          │  dailyEink.py   (unchanged)    │
│                                 │          └────────────────────────────────┘
│  GET /dashboard/joe.png         │
│  GET /dashboard/sam.png         │
│  GET /health                    │
└─────────────────────────────────┘
```

**Key design principle:** The Pi-side scripts (`dailyEink.py`, `dailyClear.py`) are not modified. Only `dailyDash.sh` is simplified — replacing the Firefox screenshot block with a single `curl` call.

---

## Display Profiles

Two profiles share the same data but differ in layout, dimensions, and color theme.

| Property | Joe | Sam |
|---|---|---|
| Display size | 800 × 480 px | 600 × 400 px |
| Layout | Side-by-side | Warm split |
| Background | `#f8f9fa` (white) | `#f7f4fd` (lavender) |
| Weather panel bg | `#e8f0fe` (light blue) | `#ede7f6` (lavender tint) |
| Forecast box bg | `#d1e0fd` | `#ede7f6` |
| Temperature color | `#1a56db` (blue) | `#6d3bbf` (purple) |
| Accent / labels | `#1a56db` | `#6d3bbf` |
| Divider | `#dee2e6` | `#d8ccf0` |
| Header label | "JDU Dashboard" | "Joy of My Life" |
| Body font | Inter (bundled) | Inter (bundled) |

### Joe's Layout — Side by Side (800×480)

```
┌─────────────────────────────────────────────────────────────┐
│  JDU Dashboard                    Wed · Apr 30, 2026 · 6:30 │
│─────────────────────────────────────────────────────────────│
│  ┌──────────────────────┐  ┌─────────────────────────────┐  │
│  │ TODAY'S WEATHER      │  │ QUOTE                       │  │
│  │                      │  │                             │  │
│  │  ☀️  91°F            │  │ "The divine is not          │  │
│  │      Today · 3% rain │  │  something high above us…"  │  │
│  │                      │  │                             │  │
│  │ ┌──────────────────┐ │  │          — Morihei Ueshiba  │  │
│  │ │ Sunny. High near │ │  └─────────────────────────────┘  │
│  │ │ 91. SW wind 5mph │ │                                   │
│  │ └──────────────────┘ │                                   │
│  └──────────────────────┘                                   │
└─────────────────────────────────────────────────────────────┘
```

- Header bar: label left, date/time right, 2px bottom border
- Weather panel: `flex 1.4` — icon + large temp, period name + precip %, detailed forecast in tinted box
- Quote panel: `flex 1.6` — label, italic quote text, right-aligned author

### Sam's Layout — Warm Split (600×400)

```
┌──────────────────────────────────────────────────┐
│       JOY OF MY LIFE · Wed, Apr 30 · 6:30 AM    │
│  ┌─────────────────────────┬──────────────────┐  │
│  │ TODAY'S THOUGHT         │ WEATHER          │  │
│  │                         │                  │  │
│  │ "The divine is not      │    ☀️            │  │
│  │  something high         │   91°F           │  │
│  │  above us…"             │   Today          │  │
│  │                         │ ┌──────────────┐ │  │
│  │  — Morihei Ueshiba      │ │Sunny. SW wind│ │  │
│  └─────────────────────────┴─┤3% precip     │ │  │
│                               └──────────────┘ │  │
└──────────────────────────────────────────────────┘
```

- Single centered header row (date, time, label)
- Quote panel: `flex 1.5`, right border as divider
- Weather panel: `flex 1` — icon, large temp, period, forecast box

---

## Data Sources

### NOAA Weather API
- **Endpoint:** `https://api.weather.gov/gridpoints/PSR/166,61/forecast`
- **Fields used:** `periods[0].name`, `periods[0].temperature`, `periods[0].shortForecast`, `periods[0].detailedForecast`, `periods[0].probabilityOfPrecipitation.value`
- **Refresh:** Once per hour by APScheduler

### ZenQuotes
- **Endpoint:** `https://zenquotes.io/api/random`
- **Fields used:** `[0].q` (quote text), `[0].a` (author)
- **Refresh:** Once per hour (fresh quote each cycle)

### Weather Icons — Basmilius Weather Icons
- **Source:** `https://raw.githubusercontent.com/basmilius/weather-icons/dev/production/fill/svg/`
- **License:** MIT
- **Strategy:** Download and rasterize a fixed set of ~10 SVGs to PNG at server startup; cache in memory. No CDN dependency at runtime.
- **Icon mapping** (from NOAA `shortForecast` text, case-insensitive substring match, evaluated top-to-bottom — first match wins):

| NOAA shortForecast contains | Day icon | Night icon |
|---|---|---|
| "sunny", "clear", "hot" | `clear-day.svg` | `clear-night.svg` |
| "mostly sunny", "mostly clear" | `partly-cloudy-day.svg` | `partly-cloudy-night.svg` |
| "partly cloudy", "partly sunny" | `partly-cloudy-day.svg` | `partly-cloudy-night.svg` |
| "mostly cloudy" | `overcast-day.svg` | `overcast-night.svg` |
| "cloudy", "overcast" | `cloudy.svg` | `cloudy.svg` |
| "drizzle", "freezing drizzle" | `partly-cloudy-day-drizzle.svg` | `partly-cloudy-night-drizzle.svg` |
| "showers", "chance rain" | `partly-cloudy-day-rain.svg` | `partly-cloudy-night-rain.svg` |
| "heavy rain", "flood" | `extreme-day-rain.svg` | `extreme-night-rain.svg` |
| "rain" | `overcast-day-rain.svg` | `overcast-night-rain.svg` |
| "sleet", "freezing rain", "wintry mix" | `overcast-day-sleet.svg` | `overcast-night-sleet.svg` |
| "blizzard", "heavy snow" | `extreme-day-snow.svg` | `extreme-night-snow.svg` |
| "flurries", "chance snow" | `partly-cloudy-day-snow.svg` | `partly-cloudy-night-snow.svg` |
| "snow" | `overcast-day-snow.svg` | `overcast-night-snow.svg` |
| "thunder", "storm" | `thunderstorms-day.svg` | `thunderstorms-night.svg` |
| "tornado", "hurricane", "tropical" | `tornado.svg` | `hurricane.svg` |
| "fog", "mist" | `fog-day.svg` | `fog-night.svg` |
| "haze", "smoke", "dust", "sand" | `haze-day.svg` | `haze-night.svg` |
| "wind", "breezy", "blustery" | `wind.svg` | `wind.svg` |
| _(fallback)_ | `clear-day.svg` | `clear-night.svg` |

Night detection: if NOAA `periods[0].name` is "Tonight" or "Overnight".

---

## Caching & Refresh Strategy

- APScheduler runs a `refresh_dashboard` job every hour at `:00`
- On each run: fetch NOAA → fetch ZenQuotes → composite both PNGs → store in memory
- On server startup: run `refresh_dashboard` immediately so endpoints are never empty
- **On API failure:** log the error, keep the previous cached PNG unchanged
- **On first-boot failure (both APIs down):** serve a plain fallback PNG ("Dashboard starting…" text on white background)
- Cached PNGs are served directly from memory — no disk I/O on request

---

## API Endpoints

| Method | Path | Response |
|---|---|---|
| GET | `/dashboard/joe.png` | `image/png` — 800×480 Joe profile |
| GET | `/dashboard/sam.png` | `image/png` — 600×400 Sam profile |
| GET | `/health` | JSON — last successful refresh timestamp, API status |

---

## Fonts

- Bundle **Inter** (Regular + Bold) in the Docker image
- No external font calls at runtime — no Google Fonts dependency
- Quote text: Inter Regular, italic rendered via Pillow `font.getmask()` transform

---

## Docker

- Single `Dockerfile`, Python 3.12-slim base
- Exposes port `8000`
- No volumes, no database — all state is in-memory
- Environment variables:
  - `PORT` (default: 8000)
  - `NOAA_GRID` (default: `PSR/166,61`)
  - `REFRESH_HOUR_INTERVAL` (default: `1`)

---

## Pi-Side Changes

Only `dailyDash.sh` changes. All other scripts (`dailyEink.py`, `dailyClear.py`, `dailyImage.sh`) are untouched.

**New `dailyDash.sh` (Joe's display):**
```bash
#!/bin/bash
curl -sf http://synology:8000/dashboard/joe.png -o /tmp/dashboard.png || exit 1
/home/red/Dev/scripts/dailyClear.py
/home/red/Dev/scripts/dailyEink.py /tmp/dashboard.png
```

`killFirefox.sh` is no longer needed.

---

## Error Handling

| Scenario | Behavior |
|---|---|
| NOAA down at refresh | Keep previous cached image, log warning |
| ZenQuotes down at refresh | Keep previous quote, log warning |
| Both APIs down on first boot | Serve fallback "starting…" PNG |
| Pi curl fails | `dailyDash.sh` exits early (no clear, no display update) |
| `/health` endpoint | Returns JSON with last refresh timestamp and per-API status |

---

## Out of Scope

- Authentication on API endpoints (local network only)
- Multiple NOAA locations
- User-configurable refresh interval via API
- Push notifications to Pi (Pi always polls)
