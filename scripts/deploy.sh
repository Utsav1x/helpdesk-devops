#!/usr/bin/env bash
# A deployment and its smoke gate share a lock and an environment-specific snapshot.
set -euo pipefail
# shellcheck source=scripts/common.sh
source "$(dirname "$0")/common.sh"
export IMAGE_TAG=${3:?Supply a unique immutable image tag}
[[ "$IMAGE_TAG" =~ ^[a-zA-Z0-9][a-zA-Z0-9_.-]{0,127}$ && "$IMAGE_TAG" != previous ]] || exit 2
exec 9>"$STATE/deploy.lock"
flock -w 300 9
dc config --quiet
# Pull the smoke runner before changing anything in the application.
docker image inspect python:3.12.8-alpine >/dev/null 2>&1 || docker pull python:3.12.8-alpine
for service in backend frontend; do docker image inspect "todo-$ENVIRONMENT-$service:$IMAGE_TAG" >/dev/null; done
count=0
for service in backend frontend; do
  id=$(dc ps -q "$service")
  if [[ -n "$id" ]]; then
    [[ $(docker inspect --format '{{.State.Health.Status}}' "$id") == healthy ]] || { echo "Current $service is unhealthy; repair it before deploying" >&2; exit 1; }
    count=$((count + 1))
  fi
done
[[ "$count" == 0 || "$count" == 2 ]] || { echo 'Partial existing deployment; refusing an incomplete snapshot' >&2; exit 1; }
# Reset stale state: a failed first deployment must never restore old unrelated images.
printf '%s\n' "$count" > "$STATE/previous-count"
if [[ "$count" == 2 ]]; then
  for service in backend frontend; do
    id=$(dc ps -q "$service")
    image_id=$(docker inspect --format '{{.Image}}' "$id")
    docker tag "$image_id" "todo-$ENVIRONMENT-$service:previous"
  done
fi
mkdir -p "$ROOT/reports"
: > "$ROOT/reports/smoke.txt"
if dc up -d --no-build --wait --wait-timeout 180 && bash "$ROOT/scripts/smoke-test.sh" --network "${PROJECT}_app" > "$ROOT/reports/smoke.txt" 2>&1; then
  printf '%s\n' "$IMAGE_TAG" > "$STATE/current-tag"
  cat "$ROOT/reports/smoke.txt"
  echo "Deployed $PROJECT:$IMAGE_TAG"
else
  cat "$ROOT/reports/smoke.txt" 2>/dev/null || true
  echo 'Deployment failed; attempting rollback' >&2
  if DEPLOY_LOCK_HELD=1 bash "$ROOT/scripts/rollback.sh" "$ENVIRONMENT" "$ENV_FILE"; then
    echo 'Rollback completed; failing this build because the candidate failed.' >&2
  else
    echo 'ROLLBACK FAILED: manual recovery required; inspect compose logs.' >&2
  fi
  exit 1
fi
