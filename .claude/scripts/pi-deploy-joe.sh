#!/usr/bin/env bash
set -euo pipefail

ENV_FILE="/Users/joeburgett/Working/E-InkDashboard/.env"
SCRIPT_SRC="/Users/joeburgett/Working/E-InkDashboard/eink-dashboard/pi/dailyDash.sh"
PI_SCRIPT_PATH="/home/red/Dev/scripts/dailyDash.sh"

PI_PASS="$(grep '^PI_PASS=' "$ENV_FILE" | cut -d= -f2-)"
PI_USER="$(grep '^PI_USER=' "$ENV_FILE" | cut -d= -f2-)"
JOE_PI="$(grep '^JOE_PI=' "$ENV_FILE" | cut -d= -f2-)"

export SSHPASS="$PI_PASS"
SSH_OPTS="-o StrictHostKeyChecking=no -o LogLevel=ERROR"
SSH="sshpass -e ssh $SSH_OPTS"
SCP="sshpass -e scp $SSH_OPTS"

echo "=== Connectivity check ==="
$SSH "${PI_USER}@${JOE_PI}" "echo Joe Pi: connected"

echo "=== Deploying to Joe's Pi (${JOE_PI}) ==="
$SCP "$SCRIPT_SRC" "${PI_USER}@${JOE_PI}:${PI_SCRIPT_PATH}"
$SSH "${PI_USER}@${JOE_PI}" "chmod +x '${PI_SCRIPT_PATH}'"

echo "=== Verifying profile ==="
echo -n "Joe: "
$SSH "${PI_USER}@${JOE_PI}" "grep '^PROFILE=' '${PI_SCRIPT_PATH}'"

echo "=== Joe Pi deployment complete ==="
