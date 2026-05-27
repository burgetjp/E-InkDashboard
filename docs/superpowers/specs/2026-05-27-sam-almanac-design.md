# Sam's Almanac — Design Spec
**Date:** 2026-05-27

## Goal

Adapt the Almanac Modern Inverted layout for Sam's 600×400 e-ink display. Key changes from the JDU version: smaller canvas, "Joy of My Life" title, and a quote-favored 45/55 column split. Served at `/proto/almanac-sam.png` for local preview before deploying to Sam's Pi.

---

## Visual Style

- **Palette:** Inverted — black background (`#0c0c0c`), cream foreground (`#f6f3ea`), cream accent
- **Border:** 2px rectangle inset 5px from edge, with pinstripe lines 3px inside the border (top + bottom)
- **Typography:** Same font stack as `render_almanac.py` — Playfair Display (masthead), JetBrains Mono (labels/colophon/dateband), Source Serif 4 (temp, quotes), Source Serif 4 Italic (forecast, quote body)

---

## Canvas & Zone Geometry (600×400)

All constants are local to `render_almanac_sam()` or a `SAM_*` prefix block at the top of the function.

| Constant | Value | Notes |
|---|---|---|
| `W, H` | 600, 400 | Sam's display |
| `OUTER_BLEED` | 5 | |
| `FRAME_W` | 2 | |
| `PINSTRIPE_OFFSET` | 3 | |
| `MASTHEAD_H` | 72 | Single-line modern title only |
| `DATEBAND_H` | 25 | |
| `COLOPHON_H` | 22 | |
| `PAD` | 10 | Content padding inside border |
| `INNER_X` | 7 | `OUTER_BLEED + FRAME_W` |
| `CONTENT_X` | 17 | `INNER_X + PAD` |
| `CONTENT_RIGHT` | 583 | `W - INNER_X - PAD` |
| `CONTENT_W` | 566 | |
| `BODY_Y` | 104 | `MAST_Y + MASTHEAD_H + DATEBAND_H` |
| `BODY_H` | ~267 | `COLON_Y - BODY_Y` |
| `WX_W` | ~255 | `round(CONTENT_W * 0.45)` — 45% weather |
| `DIVIDER_X` | ~272 | `CONTENT_X + WX_W` |

---

## Zone A — Masthead

- Font: Playfair Display ~28pt weight 900, left-aligned at `(CONTENT_X, MAST_Y + 14)`
- Title: **"Joy of My Life"** (no issue number, no subtitle)
- No pinstripe line below masthead (modern style)

---

## Zone B — Dateband

Same layout as `render_almanac.py` modern variant:
- 2px top rule, 1px bottom rule
- Day-of-week left (`WEDNESDAY`), `MONTH D · ROMAN YEAR` right
- Font: JetBrains Mono ~11pt

---

## Zone C — Body (two columns)

Vertical divider line from `BODY_Y + 8` to `COLON_Y - 8` at `DIVIDER_X`.

### Left — "Of the Weather" (45% width, ~255px)

- Section label: `OF THE WEATHER` in JetBrains Mono ~10pt, accent color
- 1px rule below label
- Weather icon: 60px, pasted directly onto canvas — **no circle underlay**
- Temperature: Source Serif 4 ~80pt weight 700, side-by-side with icon; degree symbol in ~28pt
- Stat line: `SHORT_FORECAST · X% RAIN` in JetBrains Mono ~10pt
- Forecast text: Source Serif 4 Italic ~12pt, up to 3 wrapped lines

### Right — "Of the Mind" (55% width, ~311px)

- Section label: `OF THE MIND` in JetBrains Mono ~10pt, accent color
- 1px rule below label
- Quote body: Source Serif 4 Italic ~17pt, wrapped, with `"…"` delimiters
- Attribution: `— AUTHOR NAME` right-aligned, JetBrains Mono ~11pt, accent color

---

## Zone D — Colophon

- 1px top rule
- Left: `PRINTED IN E-INK at H:MM AM/PM` — JetBrains Mono ~9pt
- Right: `INKY · 600×400` — JetBrains Mono ~9pt

---

## Implementation Architecture

### `render_almanac.py`

Add a new public function `render_almanac_sam(weather, quote, icons)` at the bottom of the file. It:
- Defines its own local geometry constants (600×400 numbers above)
- Calls `_colors("modern", inverted=True)` to get the inverted palette
- Draws the border + pinstripes inline (same pattern as `render_almanac`)
- Calls `_draw_dateband(draw, "modern", fg, accent)` — reused as-is
- Draws its own masthead inline (simpler than abstracting: one `draw.text` call)
- Draws the weather section **inline** with scaled sizes (`icon_size=60`, temp font `~80pt`) — `_draw_weather_panel` hardcodes `icon_size=70` and `f_temp=120pt`, which would clip in a 255px column; drawing inline keeps the shared helper unchanged
- Calls `_draw_quote_panel(draw, quote, x=..., y=..., w=..., h=..., fg=fg, accent=accent)` — reused as-is (311px column is wide enough for the existing font sizes)
- Draws its own colophon inline (one-liner with "600×400" label)
- Returns `bytes`

### `app/cache.py`

- Add `almanac_sam: Optional[bytes] = field(default=None)` to `DashboardCache`
- Add `store_almanac_sam(sam: bytes)` method
- Add `get_almanac_sam()` method with fallback `_make_fallback_png(600, 400, "Almanac starting…")`

### `app/scheduler.py`

In `refresh_dashboard()`, after the existing `cache.store_almanac(...)` block:
```python
cache.store_almanac_sam(
    render_almanac_sam(weather, quote, icons)
)
```

### `app/proto_router.py`

Add one new endpoint:
```python
@proto_router.get("/almanac-sam.png")
async def almanac_sam() -> Response:
    return Response(content=cache.get_almanac_sam(), media_type="image/png")
```

---

## Preview & Deploy Path

1. Run server locally (`venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000`)
2. Open `http://localhost:8000/proto/almanac-sam.png` to preview
3. Once approved, update `/dashboard/sam.png` to use `render_almanac_sam` (replacing `render_sam`)
4. rsync → NAS → Docker rebuild → update Sam's Pi script

---

## Out of Scope

- No changes to Joe's display or `/dashboard/joe.png`
- No changes to the existing four almanac proto variants
- No rotation/scheduling for Sam's display (Pi script change comes after approval)
- No subtitle line under "Joy of My Life" (clean modern style)
