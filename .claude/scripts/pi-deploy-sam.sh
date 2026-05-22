#!/usr/bin/env bash
set -euo pipefail

ENV_FILE="/Users/joeburgett/Working/E-InkDashboard/.env"
SCRIPT_SRC="/Users/joeburgett/Working/E-InkDashboard/eink-dashboard/pi/dailyDash.sh"
PI_SCRIPT_PATH="/home/red/Dev/scripts/dailyDash.sh"

PI_PASS="$(grep '^PI_PASS=' "$ENV_FILE" | cut -d= -f2-)"
PI_USER="$(grep '^PI_USER=' "$ENV_FILE" | cut -d= -f2-)"
SAM_PI="$(grep '^SAM_PI=' "$ENV_FILE" | cut -d= -f2-)"

export SSHPASS="$PI_PASS"
SSH_OPTS="-o StrictHostKeyChecking=no -o LogLevel=ERROR"
SSH="sshpass -e ssh $SSH_OPTS"

echo "=== Connectivity check ==="
$SSH "${PI_USER}@${SAM_PI}" "echo Sam Pi: connected"

echo "=== Deploying to Sam's Pi (${SAM_PI}) ==="
sed 's/PROFILE="joe"/PROFILE="sam"/' "$SCRIPT_SRC" \
  | sshpass -e ssh $SSH_OPTS "${PI_USER}@${SAM_PI}" \
      "cat > '${PI_SCRIPT_PATH}' && chmod +x '${PI_SCRIPT_PATH}'"

echo "=== Verifying profile ==="
echo -n "Sam: "
$SSH "${PI_USER}@${SAM_PI}" "grep '^PROFILE=' '${PI_SCRIPT_PATH}'"

echo "=== Sam Pi deployment complete ==="
