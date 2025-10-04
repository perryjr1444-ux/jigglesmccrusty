#!/usr/bin/env bash
set -euo pipefail

PORT="${PORT:-9000}"
HOST="${HOST:-0.0.0.0}"
APP="ai_soc.main:app"

python -m venv .venv >/dev/null 2>&1 || true
source .venv/bin/activate
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

exec uvicorn "$APP" --host "$HOST" --port "$PORT"
