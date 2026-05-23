#!/bin/bash
# Fetch dashboard PNG from NAS and push to e-ink display.
# Replaces the old Firefox headless screenshot approach.

SERVER="http://10.0.10.123:8000"
PROFILE="joe"           # change to "sam" for Sam's display
TMP_PNG="/tmp/dashboard.png"

curl -sf --retry 3 --retry-delay 5 --max-time 30 "${SERVER}/proto/almanac-classic.png" > "${TMP_PNG}" || exit 1
/home/red/Dev/scripts/dailyClear.py
/home/red/Dev/scripts/dailyEink.py "${TMP_PNG}"
rm -f "${TMP_PNG}"
