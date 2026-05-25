# JDU Almanac Round-Robin Rotation

**Date:** 2026-05-25  
**Scope:** Joe's Pi only (`eink-dashboard/pi/dailyDash.sh`)

## Problem

`dailyDash.sh` is hardcoded to fetch `almanac-classic.png`, preventing any testing of the three other prototype variants (`almanac-classic-inv`, `almanac-modern`, `almanac-modern-inv`).

## Solution

Replace the hardcoded endpoint with a time-based variant selector using `hour % 4`. Stateless, deterministic, no server changes required.

## Change

**File:** `eink-dashboard/pi/dailyDash.sh`

Replace:
```bash
curl -sf --retry 3 --retry-delay 5 --max-time 30 "${SERVER}/proto/almanac-classic.png" > "${TMP_PNG}" || exit 1
```

With:
```bash
VARIANTS=("almanac-classic" "almanac-classic-inv" "almanac-modern" "almanac-modern-inv")
INDEX=$(( $(date +%-H) % 4 ))
curl -sf --retry 3 --retry-delay 5 --max-time 30 "${SERVER}/proto/${VARIANTS[$INDEX]}.png" > "${TMP_PNG}" || exit 1
```

## Rotation Schedule

| Hours (24h)           | Variant           |
|-----------------------|-------------------|
| 0, 4, 8, 12, 16, 20  | almanac-classic   |
| 1, 5, 9, 13, 17, 21  | almanac-classic-inv |
| 2, 6, 10, 14, 18, 22 | almanac-modern    |
| 3, 7, 11, 15, 19, 23 | almanac-modern-inv |

## Out of Scope

- Sam's Pi — the updated script is only deployed to Joe's Pi via `/push-joe-pi`; Sam's Pi is left unchanged
- Server-side changes
- State persistence
