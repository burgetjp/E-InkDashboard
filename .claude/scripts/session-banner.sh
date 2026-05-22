#!/bin/bash
MSG="

  ╔══════════════════════════════════════════╗
  ║              E-INK DASHBOARD             ║
  ╚══════════════════════════════════════════╝

  FastAPI server that renders personalized daily
  dashboard images for Joe & Sam's Raspberry Pi
  e-ink displays. Runs on Synology NAS via Docker.
  Pi fetches a fresh image via cron at :30 each hour.

  CUSTOM SKILLS
  /push-joe-pi           Push script to Joe's Pi (10.0.10.88)
  /push-sam-pi           Push script to Sam's Pi (10.0.10.91)
  /push-eink-prod        Deploy server changes to Synology NAS
  /commit-push-burgetjp  Stage, commit & push all changes
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

jq -n --arg msg "$MSG" '{"systemMessage": $msg}'
