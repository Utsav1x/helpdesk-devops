#!/usr/bin/env bash
# Shared validation and Compose invocation; env files are data, never sourced.
set -euo pipefail
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
ENVIRONMENT=${1:?Usage: script ENVIRONMENT ENV_FILE [IMAGE_TAG]}
case "$ENVIRONMENT" in production|staging) ;; *) echo 'Use production or staging' >&2; exit 2;; esac
ENV_FILE=${2:?Supply an environment file}
[[ -f "$ENV_FILE" ]] || { echo 'Environment file does not exist' >&2; exit 2; }
ENV_FILE=$(cd "$(dirname "$ENV_FILE")" && pwd)/$(basename "$ENV_FILE")
export APP_ENV="$ENVIRONMENT"
PROJECT="todo-$ENVIRONMENT"
STATE_ROOT=${DEPLOY_STATE_DIR:-${JENKINS_HOME:-$ROOT}/.deploy}
STATE="$STATE_ROOT/$ENVIRONMENT"
mkdir -p "$STATE"
dc() { docker compose -p "$PROJECT" --env-file "$ENV_FILE" -f "$ROOT/docker-compose.yml" "$@"; }
