#!/usr/bin/env bash
set -euo pipefail

ENV_FILE="/Users/joeburgett/Working/E-InkDashboard/.env"
BUILD_CONTEXT="/Users/joeburgett/Working/E-InkDashboard/eink-dashboard/synology"
COMPOSE_DIR="/volume1/docker/E-INK-Dashboard"
DOCKER=/usr/local/bin/docker

NAS_PASS="$(grep '^NAS_PASS=' "$ENV_FILE" | cut -d= -f2-)"
NAS_USER="$(grep '^NAS_USER=' "$ENV_FILE" | cut -d= -f2-)"
NAS_HOST="$(grep '^NAS_HOST=' "$ENV_FILE" | cut -d= -f2-)"

SSH="sshpass -p $NAS_PASS ssh -o StrictHostKeyChecking=no -o LogLevel=ERROR ${NAS_USER}@${NAS_HOST}"

echo "=== Connectivity check ==="
$SSH "echo connected"

echo "=== Creating compose directory on NAS ==="
$SSH "
  PASS='$NAS_PASS'
  echo \"\$PASS\" | sudo -S mkdir -p '$COMPOSE_DIR'
"

echo "=== Copying source files to NAS ==="
# Pipe tar to /tmp first (no sudo needed); extract separately so sudo -S can read password from stdin
tar -C "$BUILD_CONTEXT" -czf - \
  Dockerfile requirements.txt docker-compose.yml app/ assets/ \
  | sshpass -p "$NAS_PASS" ssh \
      -o StrictHostKeyChecking=no -o LogLevel=ERROR \
      "${NAS_USER}@${NAS_HOST}" \
      "cat > /tmp/eink-deploy.tar.gz"

$SSH "
  PASS='$NAS_PASS'
  echo \"\$PASS\" | sudo -S tar -xzf /tmp/eink-deploy.tar.gz -C '$COMPOSE_DIR'
  rm /tmp/eink-deploy.tar.gz
"

echo "=== Stopping existing containers on NAS ==="
$SSH "
  PASS='$NAS_PASS'
  cd '$COMPOSE_DIR'
  echo \"\$PASS\" | sudo -S $DOCKER compose down --remove-orphans || true
  echo \"\$PASS\" | sudo -S $DOCKER stop e-ink-dashboard-prod-inky-dashboard-1 2>/dev/null || true
  echo \"\$PASS\" | sudo -S $DOCKER rm e-ink-dashboard-prod-inky-dashboard-1 2>/dev/null || true
"

echo "=== Building and recreating container on NAS ==="
$SSH "
  PASS='$NAS_PASS'
  cd '$COMPOSE_DIR'
  echo \"\$PASS\" | sudo -S $DOCKER compose up --build -d inky-dashboard
"

echo "=== Running containers ==="
$SSH "
  PASS='$NAS_PASS'
  echo \"\$PASS\" | sudo -S $DOCKER ps --format 'table {{.Names}}\t{{.Status}}'
"

echo "=== Waiting for dashboard (up to 60s) ==="
i=0
until curl -s -o /dev/null -w "%{http_code}" "http://${NAS_HOST}:8000/dashboard/joe.png" | grep -q "200"; do
  sleep 2
  i=$((i + 1))
  if [ $i -ge 30 ]; then
    echo "Timed out — dashboard not responding on port 8000"
    exit 1
  fi
done

echo "Dashboard: live"
echo "  Joe:  http://${NAS_HOST}:8000/dashboard/joe.png"
echo "  Sam:  http://${NAS_HOST}:8000/dashboard/sam.png"
echo "=== Deployment complete ==="
