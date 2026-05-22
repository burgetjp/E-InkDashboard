---
name: push-eink-prod
description: Use when deploying a new build of the e-ink dashboard to the Synology NAS, after code changes to the FastAPI server, renderer, or assets. Builds the image locally from eink-dashboard/synology/, transfers it to the NAS, and restarts the container.
---

# Push E-Ink Dashboard to Prod

## Overview

Builds the Docker image locally from the synology build context, ships the tarball to the NAS via SCP, loads it, and recreates the container. No registry required.

NAS: `10.0.10.123`  
Docker project dir: `/volume1/docker/E-INK-Dashboard/`  
Service name: `inky-dashboard` (port 8000)

NAS credentials are read from `.env` at the project root. Copy `NAS_USER`, `NAS_PASS`, and `NAS_HOST` from the KR app's `.env` if not already present.

## Steps

Run via the deploy script:

```bash
bash /Users/joeburgett/Working/E-InkDashboard/.claude/scripts/nas-deploy-eink.sh
```

The script:
1. Connects via `sshpass` (no SSH password prompt)
2. Builds `inky-dashboard:latest` from `eink-dashboard/synology/`
3. Saves the image as a gzipped tarball and SCPs it to `/tmp/` on the NAS
4. Creates the compose directory if it doesn't exist, SCPs `docker-compose.yml`
5. Loads the image and removes the temp tarball
6. Recreates the container (`--force-recreate`)
7. Polls `GET /dashboard/joe.png` up to 60s until it returns HTTP 200

## Expected Results

| Response | Meaning |
|----------|---------|
| `Dashboard: live` | Container healthy, both endpoints serving |
| `Timed out — dashboard not responding` | Container failed to start — check `docker logs inky-dashboard` on NAS |

## Verifying After Deploy

```
http://10.0.10.123:8000/dashboard/joe.png   — Joe's 800×480 display
http://10.0.10.123:8000/dashboard/sam.png   — Sam's 600×400 display
```

## .env Requirements

The project root `.env` must contain:

```
NAS_USER=<synology username>
NAS_PASS=<synology password>
NAS_HOST=10.0.10.123
```
