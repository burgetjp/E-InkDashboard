---
name: push-eink-prod
description: Use when deploying a new build of the e-ink dashboard to the Synology NAS, after code changes to the FastAPI server, renderer, or assets. Copies source files to the NAS and builds the Docker image there, then restarts the container.
---

# Push E-Ink Dashboard to Prod

## Overview

SCPs the source files to the NAS and builds the Docker image on the Synology. No local Docker required.

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
2. Creates the compose directory on the NAS (`/volume1/docker/E-INK-Dashboard/`)
3. SCPs `Dockerfile`, `requirements.txt`, `docker-compose.yml`, `app/*.py`, and `assets/fonts/*` to the NAS
4. SSHs in and runs `docker compose up --build -d --force-recreate`
5. Polls `GET /dashboard/joe.png` up to 60s until it returns HTTP 200

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
