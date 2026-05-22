#!/usr/bin/env bash
set -euo pipefail

ENV_FILE="/Users/joeburgett/Working/E-InkDashboard/.env"
COMPOSE_DIR="/volume1/docker/E-INK-Dashboard"
DOCKER=/usr/local/bin/docker
IMAGE_NAME="inky-dashboard"
BUILD_CONTEXT="/Users/joeburgett/Working/E-InkDashboard/eink-dashboard/synology"
COMPOSE_FILE="${BUILD_CONTEXT}/docker-compose.yml"
TARBALL="/tmp/${IMAGE_NAME}.tar.gz"

NAS_PASS="$(grep '^NAS_PASS=' "$ENV_FILE" | cut -d= -f2-)"
NAS_USER="$(grep '^NAS_USER=' "$ENV_FILE" | cut -d= -f2-)"
NAS_HOST="$(grep '^NAS_HOST=' "$ENV_FILE" | cut -d= -f2-)"

SSH="sshpass -p $NAS_PASS ssh -o StrictHostKeyChecking=no -o LogLevel=ERROR ${NAS_USER}@${NAS_HOST}"
SCP="sshpass -p $NAS_PASS scp -o StrictHostKeyChecking=no -o LogLevel=ERROR"

echo "=== Connectivity check ==="
$SSH "echo connected"

echo "=== Building image locally ==="
docker build -t "${IMAGE_NAME}:latest" "$BUILD_CONTEXT"

echo "=== Saving image ==="
docker save "${IMAGE_NAME}:latest" | gzip > "$TARBALL"

echo "=== Uploading to NAS ==="
$SCP "$TARBALL" "${NAS_USER}@${NAS_HOST}:/tmp/${IMAGE_NAME}.tar.gz"
$SSH "
  PASS='$NAS_PASS'
  echo \"\$PASS\" | sudo -S mkdir -p '$COMPOSE_DIR'
"
$SCP "$COMPOSE_FILE" "${NAS_USER}@${NAS_HOST}:${COMPOSE_DIR}/docker-compose.yml"

echo "=== Loading image on NAS ==="
$SSH "
  PASS='$NAS_PASS'
  echo \"\$PASS\" | sudo -S $DOCKER load -i /tmp/${IMAGE_NAME}.tar.gz
  rm /tmp/${IMAGE_NAME}.tar.gz
"

echo "=== Recreating container ==="
$SSH "
  PASS='$NAS_PASS'
  cd '$COMPOSE_DIR'
  echo \"\$PASS\" | sudo -S $DOCKER compose up -d --force-recreate ${IMAGE_NAME}
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
