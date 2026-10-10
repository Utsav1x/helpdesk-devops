#!/usr/bin/env bash
# Bounded authenticated requests make the Prometheus graphs move.
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
if command -v python3 >/dev/null 2>&1; then runner=python3; else runner=python; fi
exec "$runner" "$ROOT/scripts/load.py" "${1:-http://localhost:8080}" "${2:-300}"
