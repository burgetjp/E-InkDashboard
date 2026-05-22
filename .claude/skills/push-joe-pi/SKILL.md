---
name: push-joe-pi
description: Use when pushing a new dailyDash.sh script to Joe's Raspberry Pi (10.0.10.88). Run after changes to eink-dashboard/pi/dailyDash.sh — e.g. new server URL, updated curl flags, or profile config changes.
---

# Push E-Ink Script to Joe's Pi

## Overview

SCPs `eink-dashboard/pi/dailyDash.sh` to Joe's Raspberry Pi unchanged (`PROFILE="joe"`).

| Pi  | User  | Host         | Script path                          |
|-----|-------|--------------|--------------------------------------|
| Joe | `red` | `10.0.10.88` | `/home/red/Dev/scripts/dailyDash.sh` |

Pi credentials are read from `.env` at the project root (`PI_USER`, `PI_PASS`, `JOE_PI`).

Cron is already configured on Joe's Pi at `:30` — this skill only updates the script file, not the crontab.

## .env Requirements

```
PI_USER=red
PI_PASS=<pi-password>
JOE_PI=10.0.10.88
```

## Steps

```bash
bash /Users/joeburgett/Working/E-InkDashboard/.claude/scripts/pi-deploy-joe.sh
```

The script:
1. Connects to Joe's Pi via `sshpass`
2. SCPs `eink-dashboard/pi/dailyDash.sh` to `/home/red/Dev/scripts/dailyDash.sh`
3. `chmod +x` the script
4. Greps `PROFILE=` to confirm it landed correctly

## Expected Output

```
=== Connectivity check ===
Joe Pi: connected
=== Deploying to Joe's Pi (10.0.10.88) ===
=== Verifying profile ===
Joe: PROFILE="joe"
=== Joe Pi deployment complete ===
```

## Troubleshooting

| Symptom | Check |
|---------|-------|
| `sshpass: command not found` | `brew install hudochenkov/sshpass/sshpass` |
| `Connection refused` | Pi off or IP changed — verify with `ping 10.0.10.88` |
| `Permission denied` | Wrong password in `.env` `PI_PASS=` |
| Display shows "Dashboard starting…" | NAS container not running — run `/push-eink-prod` first |
