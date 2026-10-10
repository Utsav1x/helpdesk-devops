#!/usr/bin/env bash
# Test through nginx from the host or from the selected Docker network.
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
if [[ ${1:-} == --network ]]; then
  exec docker run --rm -i --network "${2:?Supply network}" python:3.12.8-alpine python - http://frontend:8080 < "$ROOT/scripts/smoke.py"
fi
if command -v python3 >/dev/null 2>&1; then runner=python3; else runner=python; fi
exec "$runner" "$ROOT/scripts/smoke.py" "${1:-http://localhost:8080}"
