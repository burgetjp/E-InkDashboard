# E-Ink Dashboard — Dark Mode Redesign Spec
**Date:** 2026-04-30
**Status:** Approved

---

## Overview

Replace the current light-mode dashboard layout with a dark mode design optimized for the Pimoroni Inky Impression 7-color e-ink display. Uses only native palette colors (black, white, yellow, blue, orange, gray) to avoid dithering artifacts.

---

## Design Principles

- **Black background** — maximum contrast, zero dithering on the dark field
- **Native palette only** — temperature and icon accent colors drawn from the 7 native e-ink colors
- **No colored panel backgrounds** — single vertical divider separates weather from quote; no filled rectangles
- **Date only in header** — timestamp removed, date displayed right-aligned
- **Larger type** — all font sizes increased for readability at arm's length

---

## Joe's Layout — 800×480

```
┌────────────────────────────────────────────────────────────────┐  black bg
│  JDU DASHBOARD                        Wednesday, April 30, 2026│  header
│────────────────────────────────────────────────────────────────│  #222 border
│                           │                                     │
│  TODAY'S WEATHER          │  QUOTE                              │
│                           │                                     │
│  [icon●]  91°F            │  "The divine is not something       │
│            ↑ yellow       │   high above us…"                   │
│  Sunny · 3% chance rain   │                                     │
│  ↑ 16px                   │            — Morihei Ueshiba        │
│                           │                                     │
│  ┌─────────────────────┐  │                                     │
│  │ Sunny. High near 91.│  │                                     │
│  │ SW wind 5-10 mph.   │  │                                     │
│  └─────────────────────┘  │                                     │
└────────────────────────────────────────────────────────────────┘
```

### Colors
| Element | Value |
|---|---|
| Background | `#000000` |
| Header title | `#ffffff` |
| Header date | `#666666` |
| Panel divider | `#1a1a1a` (1px line) |
| Section labels | `#444444` |
| Quote text | `#dddddd` |
| Author text | `#555555` |
| Forecast box bg | `#0d0d0d` |
| Forecast box border | `#1e1e1e` |
| Forecast text | `#666666` |
| Subtitle (period/precip) | `#888888` — 16px |

### Typography
| Element | Size | Weight |
|---|---|---|
| Header title | 18px | 900 |
| Header date | 15px | 400 |
| Section labels | 11px | 700 |
| Temperature | 80px | 900 |
| Condition subtitle | 16px | 400 |
| Forecast detail | 13px | 400 |
| Quote text | 18px | 400 italic |
| Author | 14px | 400 |

---

## Condition Accent Colors

Temperature and icon circle use condition-matched colors from the native palette. First-match on `short_forecast` (same order as existing `ICON_MAPPING`).

| Condition keywords | Temp color | Icon bg |
|---|---|---|
| sunny, clear, hot, mostly sunny, mostly clear | `#ffe900` (yellow) | `#ffe900` |
| showers, chance rain, rain, heavy rain, flood, drizzle | `#5b9bd5` (blue) | `#00439c` |
| thunder, storm | `#ff7201` (orange) | `#333333` |
| snow, blizzard, flurries, chance snow, heavy snow | `#cce8ff` (white-blue) | `#1a3a5c` |
| sleet, freezing rain, wintry mix, freezing drizzle | `#cce8ff` | `#1a3a5c` |
| fog, mist, haze, smoke, dust, sand | `#888888` | `#222222` |
| cloudy, overcast, mostly cloudy, partly cloudy, partly sunny | `#aaaaaa` | `#2a2a2a` |
| wind, breezy, blustery | `#aaaaaa` | `#2a2a2a` |
| tornado, hurricane, tropical | `#ff7201` | `#333333` |
| _(fallback)_ | `#ffe900` | `#ffe900` |

---

## Sam's Layout — 600×400

Same dark mode treatment with the same accent color system. Layout unchanged (centered header, quote left, weather right, vertical divider).

| Element | Value |
|---|---|
| Background | `#000000` |
| Header title | `#ffffff` |
| Header date | `#666666` |
| Section labels | `#444444` |
| Quote text | `#dddddd` |
| Author | `#555555` |
| Forecast box bg | `#0d0d0d` |
| Forecast text | `#666666` |

---

## Implementation Changes

### New module: `app/accent.py`
Single function `select_accent(short_forecast) -> tuple[str, str]` returning `(temp_color, icon_bg_color)`. Mirrors the keyword-matching pattern from `app/icons.py`.

### Updated: `app/render_joe.py`
- All color constants replaced with dark palette
- Header: title + date only (no time) — `strftime("%A, %B %-d, %Y")`
- Weather panel: no filled `rounded_rectangle` background; just content drawn on black
- Vertical divider: 1px `#1a1a1a` line
- Temperature and icon bg: from `select_accent()`
- Subtitle font size: 16px

### Updated: `app/render_sam.py`
- Same color constant replacements
- Header: centered, date only
- Same `select_accent()` call

### Updated: `synology/app/` copies
Both renderer files synced to `synology/app/` after changes.

---

## Out of Scope

- Changing layout structure (panel proportions, panel order)
- Sam-specific accent color (uses same system as Joe)
- Font changes beyond size adjustments already specified
