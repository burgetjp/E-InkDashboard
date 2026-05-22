---
name: push-sam-pi
description: Use when pushing a new dailyDash.sh script to Sam's Raspberry Pi (10.0.10.91). Run after changes to eink-dashboard/pi/dailyDash.sh — e.g. new server URL, updated curl flags, or profile config changes.
---

# Push E-Ink Script to Sam's Pi

## Overview

Pipes `eink-dashboard/pi/dailyDash.sh` through `sed` to substitute `PROFILE="sam"` and streams it to Sam's Raspberry Pi.

| Pi  | User  | Host         | Script path                          |
|-----|-------|--------------|--------------------------------------|
| Sam | `red` | `10.0.10.91` | `/home/red/Dev/scripts/dailyDash.sh` |

Pi credentials are read from `.env` at the project root (`PI_USER`, `PI_PASS`, `SAM_PI`).

Cron is already configured on Sam's Pi at `:30` — this skill only updates the script file, not the crontab.

## .env Requirements

```
PI_USER=red
PI_PASS=<pi-password>
SAM_PI=10.0.10.91
```

## Steps

```bash
bash /Users/joeburgett/Working/E-InkDashboard/.claude/scripts/pi-deploy-sam.sh
```

The script:
1. Connects to Sam's Pi via `sshpass`
2. Pipes `eink-dashboard/pi/dailyDash.sh` through `sed 's/PROFILE="joe"/PROFILE="sam"/'` and streams it to `/home/red/Dev/scripts/dailyDash.sh`
3. `chmod +x` the script
4. Greps `PROFILE=` to confirm `sam` landed correctly

## Expected Output

```
=== Connectivity check ===
Sam Pi: connected
=== Deploying to Sam's Pi (10.0.10.91) ===
=== Verifying profile ===
Sam: PROFILE="sam"
=== Sam Pi deployment complete ===
```

## Troubleshooting

| Symptom | Check |
|---------|-------|
| `sshpass: command not found` | `brew install hudochenkov/sshpass/sshpass` |
| `Connection refused` | Pi off or IP changed — verify with `ping 10.0.10.91` |
| `Permission denied` | Wrong password in `.env` `PI_PASS=` |
| Display shows "Dashboard starting…" | NAS container not running — run `/push-eink-prod` first |
