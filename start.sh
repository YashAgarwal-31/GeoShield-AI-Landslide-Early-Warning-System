#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
HOST="${GEOSHIELD_HOST:-127.0.0.1}"
PORT="${GEOSHIELD_PORT:-8000}"

export APP_ENV="${APP_ENV:-demo}"
export ENABLE_DEMO_USERS="${ENABLE_DEMO_USERS:-true}"
export WEATHER_LIVE_ENABLED="${WEATHER_LIVE_ENABLED:-false}"
export MODEL_TRAINING_ENABLED="${MODEL_TRAINING_ENABLED:-false}"
export TRUST_PROXY_HEADERS="${TRUST_PROXY_HEADERS:-false}"

if [ -x "$BACKEND_DIR/venv/bin/python" ]; then
  PYTHON="$BACKEND_DIR/venv/bin/python"
else
  PYTHON="${PYTHON_BIN:-python3}"
fi

echo "GeoShield - starting local demo"
echo "URL: http://$HOST:$PORT"
echo "Live weather: $WEATHER_LIVE_ENABLED"
echo "Model retraining: $MODEL_TRAINING_ENABLED"

cd "$BACKEND_DIR"
exec "$PYTHON" -m uvicorn app.main:app --host "$HOST" --port "$PORT"
