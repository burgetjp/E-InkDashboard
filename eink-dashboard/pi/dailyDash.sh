#!/bin/bash
# Fetch dashboard PNG from NAS and push to e-ink display.
# Replaces the old Firefox headless screenshot approach.

SERVER="http://10.0.10.123:8000"
PROFILE="joe"
TMP_PNG="/tmp/dashboard.png"

# Wait for NAS to wake from deep sleep (up to 120s)
_elapsed=0
until curl -sf --max-time 5 "${SERVER}/health" > /dev/null 2>&1; do
    if [ $_elapsed -ge 120 ]; then
        echo "NAS did not respond after 120s — aborting" >&2
        exit 1
    fi
    sleep 10
    _elapsed=$((_elapsed + 10))
done

curl -sf --retry 3 --retry-delay 5 --max-time 30 "${SERVER}/proto/almanac-classic-inv.png" > "${TMP_PNG}" || exit 1
/home/red/Dev/scripts/dailyClear.py
/home/red/Dev/scripts/dailyEink.py "${TMP_PNG}"
rm -f "${TMP_PNG}"
