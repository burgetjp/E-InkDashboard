# JDU Almanac Prototype — Design Spec
**Date:** 2026-05-22
**Status:** Approved

---

## Overview

Four prototype variants of the JDU Dashboard in an editorial "almanac" aesthetic for the Joe Pi (800×480 Inky Impression 7.3″). Served under a `/proto/` URL prefix alongside the existing production endpoints, which remain untouched.

---

## Hardware Constraints

- **Panel:** Pimoroni Inky Impression 7.3″ (ACeP/E5), 800×480 px
- **Palette:** Exactly 7 native colors — avoid any other values to prevent dithering
- **No backlight, no animation, ~15–40 s refresh** — design must read at-a-glance

---

## Color Palette (7 native e-ink colors)

| Token  | Hex       |
|--------|-----------|
| Ink    | `#0c0c0c` |
| Paper  | `#f6f3ea` |
| Red    | `#c01818` |
| Orange | `#ea6a16` |
| Yellow | `#f2c200` |
| Green  | `#1d8a3a` |
| Blue   | `#1b4cb0` |

---

## Typography

Three font families, all variable-weight TTF files bundled in `assets/fonts/`.

| Role        | Family                 | File(s)                                         | Used for                                                 |
|-------------|------------------------|-------------------------------------------------|----------------------------------------------------------|
| **Display** | Playfair Display       | `PlayfairDisplay[wght].ttf`                     | Masthead title (wt 900), drop-cap (wt 900), wt 700 bold  |
|             |                        | `PlayfairDisplay-Italic[wght].ttf`              | Subtitle (italic, wt 700)                                |
| **Body**    | Source Serif 4         | `SourceSerif4[opsz,wght].ttf`                   | Temperature (wt 700)                                     |
|             |                        | `SourceSerif4-Italic[opsz,wght].ttf`            | Quote body (wt 400 italic), forecast description (italic)|
| **Mono**    | JetBrains Mono         | `JetBrainsMono[wght].ttf`                       | Ribbons, dateband, stat line, attribution, colophon      |

Weight axes are set via `font.set_variation_by_axes([wght])` after `ImageFont.truetype()`.

---

## Four Variants

| ID             | Endpoint                          | Background | Accent      |
|----------------|-----------------------------------|------------|-------------|
| classic        | `/proto/almanac-classic.png`      | `#f6f3ea`  | `#c01818` (Red)    |
| classic-inv    | `/proto/almanac-classic-inv.png`  | `#0c0c0c`  | `#f2c200` (Yellow) |
| modern         | `/proto/almanac-modern.png`       | `#f6f3ea`  | `#0c0c0c` (Ink)    |
| modern-inv     | `/proto/almanac-modern-inv.png`   | `#0c0c0c`  | `#f6f3ea` (Paper)  |

---

## Layout Anatomy (800×480)

```
┌──────────────────────────────────────────────────────────────┐  ← 6px outer bleed
│ ┌────────────────────────────────────────────────────────┐   │
│ │  Zone A · Masthead                          ~62 px     │   │
│ │  Zone B · Dateband                          ~30 px     │   │
│ │  Zone C · Body (weather left | quote right) flex       │   │
│ │  Zone D · Colophon                          ~26 px     │   │
│ └────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────┘
```

Frame: 2px ink border with 6px outer bleed. Decorative inner pinstripe 4px below top border, 4px above bottom border.

---

## Zone A — Masthead

| Element           | Classic                                                      | Modern                            |
|-------------------|--------------------------------------------------------------|-----------------------------------|
| Vol ribbon (TL)   | `Vol. III` — JetBrains Mono 12px, accent color              | Hidden                            |
| Issue ribbon (TR) | `№ 142` — JetBrains Mono 12px, accent color                 | Hidden                            |
| Title             | `The JDU Almanac` — Playfair Display 900, 38px, centered     | `JDU Almanac` — left-aligned, 34px|
| Subtitle          | `— a daily dashboard of weather & thought —` — Playfair Display Italic 700, 14px, accent color, centered | Hidden |

---

## Zone B — Dateband

Single row, bordered top (1.5px) and bottom (2px). JetBrains Mono 13px, +0.1em tracking, uppercase.

| Token            | Classic                                                      | Modern                            |
|------------------|--------------------------------------------------------------|-----------------------------------|
| Content          | `Friday · May 22 · MMXXVI · 22°W · 38°N` (centered, 5px accent-color dots) | `Friday · May 22 · MMXXVI` (left/right justified, no coordinates) |

---

## Zone C — Body

Remaining height after Masthead, Dateband, Colophon. Split left/right with a 1px ink/paper divider.

### Left panel — Of the Weather

1. **Section label:** `Of the Weather` — JetBrains Mono 13px, +0.18em tracking, uppercase, accent color, hairline rule below
2. **Weather icon:** Basmilius SVG via existing `select_icon_name()` + `icons` dict, rendered at 70px directly on background — no circle, no ellipse
3. **Temperature:** integer + `°` superscript — Source Serif 4 Bold 700, 120px, `tabular-nums lining-nums`; color = variant accent; `°` at 40px
4. **Stat line:** `{condition} · {precip}% rain` — JetBrains Mono 13px, uppercase, dots `·` in accent color. (`WeatherData` has no wind field; wind is omitted from the prototype stat line rather than parsing `detailed_forecast`.)
5. **Forecast description:** 1–2 sentence italic prose, truncated to ~120 chars — Source Serif 4 Italic 400, 15px, ink/paper color

### Right panel — Of the Mind

1. **Section label:** `Of the Mind` — same treatment as weather label
2. **Drop-cap:** first character of quote — Playfair Display 900, 62px, accent color, floated left
3. **Quote body:** Source Serif 4 Italic 400, 21px, line-height ~1.34, ink/paper color; ceiling ~160 chars
4. **Attribution:** `— {Author Name}` — JetBrains Mono 12px, +0.14em, uppercase, right-aligned; hairline rule above; author name in accent color, em-dash in ink/paper

---

## Zone D — Colophon

1.5px ink/paper rule above. Three tokens spread across the row. JetBrains Mono 11px, +0.14em, uppercase.

| Position | Classic                        | Modern              |
|----------|--------------------------------|---------------------|
| Left     | `Printed in Ink`               | `Printed in Ink`    |
| Center   | `✦ ✦ ✦` in accent color        | Hidden              |
| Right    | `Inky · 7.3″ · 800×480`        | `Inky · 7.3″ · 800×480` |

---

## Architecture

### New files

| File                         | Purpose                                                   |
|------------------------------|-----------------------------------------------------------|
| `app/proto_router.py`        | FastAPI router, 4 endpoints under `/proto` prefix         |
| `app/render_almanac.py`      | Single renderer: `render_almanac(weather, quote, icons, *, variant, inverted) -> bytes` |

### Modified files

| File              | Change                                                                  |
|-------------------|-------------------------------------------------------------------------|
| `app/cache.py`    | Add 4 proto slots: `classic`, `classic_inv`, `modern`, `modern_inv`     |
| `app/scheduler.py`| Call `render_almanac()` for all 4 variants during hourly refresh        |
| `app/main.py`     | `app.include_router(proto_router, prefix="/proto")`                     |

### Font files (already downloaded)

All five variable TTF files now live in `assets/fonts/`. No Dockerfile change needed — they are committed to the repo and copied by the existing `COPY assets/ assets/` step.

```
assets/fonts/
  PlayfairDisplay[wght].ttf
  PlayfairDisplay-Italic[wght].ttf
  SourceSerif4[opsz,wght].ttf
  SourceSerif4-Italic[opsz,wght].ttf
  JetBrainsMono[wght].ttf
```

---

## Data Inputs

All reused from existing production scheduler — no new API calls:
- `WeatherData` — temperature, short_forecast, precip_percent, detailed_forecast, period_name (wind omitted from stat line — not a field in `WeatherData`)
- `QuoteData` — text, author
- `icons: dict[str, Image.Image]` — existing Basmilius SVG icon set

Static config values (coordinates, vol/issue numbers) are hardcoded constants in `render_almanac.py`:
```python
LOCATION_COORDS = "112°W · 33°N"   # Phoenix, AZ
VOL_LABEL = "Vol. III"
ISSUE_LABEL = "№ 142"              # Update manually
```

---

## Edge Cases

- **Triple-digit temps:** tabular-nums on Source Serif 4 keeps layout stable at 108°F
- **Long forecast:** truncate `detailed_forecast` to ~120 chars before drawing
- **Long quotes:** wrap at ~160 chars, ~5 lines at 21px; truncate with ellipsis if over
- **Wind data:** `WeatherData` has no wind field; stat line uses `{condition} · {precip}% rain` only — wind omitted for the prototype

---

## Out of Scope

- Sam's layout (600×400) — prototype is Joe Pi only
- Changes to production `/dashboard/joe.png` or `/dashboard/sam.png`
- New weather API fields (use what's already in `WeatherData`)
- Automated vol/issue numbering
