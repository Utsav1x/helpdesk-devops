#!/usr/bin/env bash
# Explicit staging-only recovery exercises. Always restore the backend on exit.
set -euo pipefail
source "$(dirname "$0")/common.sh"
[[ "$ENVIRONMENT" == staging ]] || { echo 'Rehearsal is staging-only'; exit 2; }
mkdir -p "$ROOT/reports" "$ROOT/.deploy/rehearsal"
cp "$ROOT/reports/smoke.txt" "$ROOT/reports/deployment-smoke.txt"
trap 'dc start backend >/dev/null 2>&1 || true' EXIT
backend_id=$(dc ps -q backend)
frontend_id=$(dc ps -q frontend)
backend_image=$(docker inspect --format '{{.Image}}' "$backend_id")
frontend_image=$(docker inspect --format '{{.Image}}' "$frontend_id")
probe="rehearsal-${BUILD_NUMBER:-manual}"
# A dedicated marker in the actual PostgreSQL database proves volume persistence.
dc exec -T backend python -c "from portal import create_app; from sqlalchemy import text; a=create_app(); c=a.extensions['db'].connect(); c.execute(text('CREATE TABLE IF NOT EXISTS devops_persistence_probe (id text PRIMARY KEY)')); c.execute(text('INSERT INTO devops_persistence_probe VALUES (:id) ON CONFLICT DO NOTHING'), {'id':'$probe'}); c.commit(); c.close()"
dc restart db
dc up -d --no-build --wait --wait-timeout 180
dc exec -T backend python -c "from portal import create_app; from sqlalchemy import text; a=create_app(); c=a.extensions['db'].connect(); assert c.execute(text('SELECT count(*) FROM devops_persistence_probe WHERE id=:id'), {'id':'$probe'}).scalar()==1; c.execute(text('DELETE FROM devops_persistence_probe WHERE id=:id'), {'id':'$probe'}); c.commit(); c.close(); print('PASS: PostgreSQL marker survived database container restart; probe row cleaned')"
candidate="rehearsal-${BUILD_NUMBER:-manual}"
docker tag "$backend_image" "todo-staging-backend:$candidate"
printf 'FROM %s\nCOPY broken.conf /etc/nginx/conf.d/default.conf\n' "$frontend_image" > "$ROOT/.deploy/rehearsal/Dockerfile"
printf "server { listen 8080; root /usr/share/nginx/html; location = /health { return 200 'ok'; } location /api/ { return 503; } location / { try_files \$uri /index.html; } }\n" > "$ROOT/.deploy/rehearsal/broken.conf"
docker build -t "todo-staging-frontend:$candidate" "$ROOT/.deploy/rehearsal"
if bash "$ROOT/scripts/deploy.sh" staging "$ENV_FILE" "$candidate"; then
  echo 'FAIL: deliberately broken API candidate unexpectedly passed'; exit 1
fi
[[ $(docker inspect --format '{{.Image}}' "$(dc ps -q backend)") == "$backend_image" ]]
[[ $(docker inspect --format '{{.Image}}' "$(dc ps -q frontend)") == "$frontend_image" ]]
bash "$ROOT/scripts/smoke-test.sh" --network "${PROJECT}_app"
echo 'PASS: broken candidate failed its smoke gate; automatic rollback restored both original image IDs and the working API'
prometheus=$(docker ps -q --filter label=com.docker.compose.project=todo-staging --filter label=com.docker.compose.service=prometheus)
[[ -n "$prometheus" ]]
dc stop backend
fired=0
for attempt in $(seq 1 24); do
  docker exec "$prometheus" wget -q -O - http://localhost:9090/api/v1/alerts > "$ROOT/reports/alert-firing.json"
  if python3 -c "import json,sys; a=json.load(open('$ROOT/reports/alert-firing.json'))['data']['alerts']; sys.exit(not any(x['labels'].get('alertname')=='BackendDown' and x['state']=='firing' for x in a))"; then fired=1; break; fi
  sleep 5
done
dc start backend
dc up -d --no-build --wait --wait-timeout 180
[[ "$fired" == 1 ]] || { echo 'FAIL: alert did not fire within two minutes'; exit 1; }
echo 'PASS: BackendDown fired during the controlled staging outage'
recovered=0
for attempt in $(seq 1 18); do
  docker exec "$prometheus" wget -q -O - http://localhost:9090/api/v1/alerts > "$ROOT/reports/alert-recovered.json"
  if python3 -c "import json,sys; a=json.load(open('$ROOT/reports/alert-recovered.json'))['data']['alerts']; sys.exit(any(x['labels'].get('alertname')=='BackendDown' for x in a))"; then recovered=1; break; fi
  sleep 5
done
[[ "$recovered" == 1 ]]
bash "$ROOT/scripts/smoke-test.sh" --network "${PROJECT}_app" > "$ROOT/reports/smoke.txt"
echo 'PASS: backend recovered, alert cleared and final authenticated smoke test passed'
