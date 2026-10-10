#!/usr/bin/env bash
# Restore only application images; keep the database and its volume intact.
set -euo pipefail
# shellcheck source=scripts/common.sh
source "$(dirname "$0")/common.sh"
if [[ ${DEPLOY_LOCK_HELD:-0} != 1 ]]; then exec 9>"$STATE/deploy.lock"; flock -w 300 9; fi
[[ -f "$STATE/previous-count" ]] || { echo 'No deployment snapshot found' >&2; exit 1; }
if [[ $(cat "$STATE/previous-count") == 0 ]]; then
  dc stop frontend backend
  dc rm -f frontend backend
  echo 'First deployment failed: removed candidate application containers; database retained.'
  exit 0
fi
export IMAGE_TAG=previous
for service in backend frontend; do docker image inspect "todo-$ENVIRONMENT-$service:previous" >/dev/null; done
dc up -d --no-build --wait --wait-timeout 180
bash "$ROOT/scripts/smoke-test.sh" --network "${PROJECT}_app"
printf 'previous\n' > "$STATE/current-tag"
echo "Restored previous images for $PROJECT"
