#!/usr/bin/env bash
# Deploy monitoring with configuration packaged inside images for remote Docker hosts.
set -euo pipefail
source "$(dirname "$0")/common.sh"
export MONITOR_TAG=${IMAGE_TAG:-local}
docker build -f "$ROOT/monitoring/prometheus.Dockerfile" -t "todo-monitor-prometheus:$MONITOR_TAG" "$ROOT/monitoring"
docker build -f "$ROOT/monitoring/grafana.Dockerfile" -t "todo-monitor-grafana:$MONITOR_TAG" "$ROOT/monitoring"
mc() { docker compose -p "$PROJECT" --env-file "$ENV_FILE" -f "$ROOT/docker-compose.yml" -f "$ROOT/docker-compose.monitoring.yml" "$@"; }
mc config --quiet
mc run --rm --no-deps --entrypoint promtool prometheus check config /etc/prometheus/prometheus.yml
mc up -d --no-build --wait --wait-timeout 240 prometheus grafana cadvisor
mc ps
