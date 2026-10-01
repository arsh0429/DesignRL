#!/usr/bin/env bash
set -euo pipefail

# Reliable server launcher for environments without system python/uvicorn.
HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-7860}"
RELOAD="${RELOAD:-false}"
ENABLE_WEB_INTERFACE="${ENABLE_WEB_INTERFACE:-false}"

CMD=(
  uv run --locked
  python -m uvicorn server.app:app
  --host "${HOST}"
  --port "${PORT}"
)

if [[ "${RELOAD}" == "true" ]]; then
  CMD+=(--reload)
fi

# Pass through extra CLI args to uvicorn.
CMD+=("$@")

echo "Starting DesignRL server on ${HOST}:${PORT} (reload=${RELOAD}, web=${ENABLE_WEB_INTERFACE})"
ENABLE_WEB_INTERFACE="${ENABLE_WEB_INTERFACE}" "${CMD[@]}"
