#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${REPO_ROOT}/local-api"

export X2_API_ROLE="${X2_API_ROLE:-robot-gateway}"
export X2_ROBOT_ADAPTER="${X2_ROBOT_ADAPTER:-aimdk}"

HOST="${X2_ROBOT_GATEWAY_HOST:-0.0.0.0}"
PORT="${X2_ROBOT_GATEWAY_PORT:-8766}"

python -m uvicorn app.main:app --host "${HOST}" --port "${PORT}"
