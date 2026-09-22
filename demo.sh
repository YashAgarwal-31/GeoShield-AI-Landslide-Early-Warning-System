#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════════
# GeoShield Live Demo Script for SIH 2026 Judges
# Polished 3-minute walkthrough
# ════════════════════════════════════════════════════════════════
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
HOST="127.0.0.1"
PORT="${GEOSHIELD_PORT:-8000}"
BASE_URL="http://$HOST:$PORT"

export APP_ENV="demo"
export ENABLE_DEMO_USERS="true"
export WEATHER_LIVE_ENABLED="${WEATHER_LIVE_ENABLED:-false}"
export MODEL_TRAINING_ENABLED="false"
export TRUST_PROXY_HEADERS="false"
export CORS_ALLOWED_ORIGINS="$BASE_URL,http://localhost:$PORT"
export JWT_SECRET="${JWT_SECRET:-geoshield-local-demo-key-do-not-deploy}"

if [ -x "$BACKEND_DIR/venv/bin/python" ]; then
  PYTHON="$BACKEND_DIR/venv/bin/python"
else
  PYTHON="${PYTHON_BIN:-python3}"
fi

cleanup() {
  if [ -n "${BACKEND_PID:-}" ]; then
    kill "$BACKEND_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT INT TERM

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║          🛡️  GeoShield Live Demo — SIH 2026                ║"
echo "║     AI-Based Landslide Risk Monitoring System              ║"
echo "║         North Eastern Region, India                        ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Start backend
echo "⚙️  Starting backend server..."
cd "$BACKEND_DIR"
"$PYTHON" -m uvicorn app.main:app --host "$HOST" --port "$PORT" &
BACKEND_PID=$!
cd "$ROOT_DIR"

# Wait for backend
echo "⏳ Waiting for backend..."
for _ in {1..30}; do
  if curl --fail --silent "$BASE_URL/api/health" | grep -q '"status":"healthy"'; then
    echo "✅ Backend is healthy!"
    break
  fi
  if ! kill -0 "$BACKEND_PID" 2>/dev/null; then
    echo "❌ Backend exited before becoming healthy"
    exit 1
  fi
  sleep 1
done

if ! curl --fail --silent "$BASE_URL/api/health" | grep -q '"status":"healthy"'; then
  echo "❌ Backend did not become healthy within 30 seconds"
  exit 1
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  DEMO SEQUENCE (3 minutes)"
echo "═══════════════════════════════════════════════════════════════"
echo ""

echo "📊 Step 1 (30s): Dashboard Overview"
echo "   → Show 20 stations, risk pie chart, rainfall trends"
echo "   → Point out clearly labelled cached/live/fallback source badges"
echo "   → Open $BASE_URL"
echo ""
read -p "   Press Enter when ready for next step..."

echo ""
echo "🗺️  Step 2 (30s): GIS Risk Map"
echo "   → Show interactive map with heatmap"
echo "   → Click Cherrapunji station (known hotspot)"
echo "   → Show road status and village markers"
echo ""
read -p "   Press Enter when ready for next step..."

echo ""
echo "⚡ Step 3 (60s): Landslide Simulator"
echo "   → Navigate to Simulator page"
echo "   → Select Cherrapunji, intensity = CRITICAL"
echo "   → Click 'Run Simulation'"
echo "   → Show: returned prototype risk score and risk level"
echo "   → Show: generated alert and persisted timeline entry"
echo "   → Show: Contributing factors and recommendation"
echo ""

# Authenticate and run the protected simulation API.
echo "   🔧 Running simulation via API..."
LOGIN_RESULT=$(curl --fail --silent -X POST "$BASE_URL/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  --data-urlencode "email=admin@geoshield.gov.in" \
  --data-urlencode "password=admin123")
TOKEN=$(printf '%s' "$LOGIN_RESULT" | "$PYTHON" -c "import json,sys; print(json.load(sys.stdin)['token'])")

SIM_RESULT=$(curl --fail --silent -X POST "$BASE_URL/api/simulate/landslide" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"station_id": "NER-011", "intensity": "critical"}')

if echo "$SIM_RESULT" | grep -q "risk_score"; then
    RISK_SCORE=$(printf '%s' "$SIM_RESULT" | "$PYTHON" -c "import sys,json; print(json.load(sys.stdin)['risk_assessment']['risk_score'])")
    echo "   ✅ Simulation complete! Risk score: $RISK_SCORE/100"
else
    echo "   ❌ Authenticated simulation did not return a risk score."
    exit 1
fi

echo ""
read -p "   Press Enter when ready for next step..."

echo ""
echo "🛰️  Step 4 (30s): Satellite Data"
echo "   → Navigate to Satellite Data page"
echo "   → Show elevation, soil moisture and NDVI with source/provenance labels"
echo "   → Compare Tawang (2791m) vs Agartala (12m)"
echo ""
read -p "   Press Enter when ready for next step..."

echo ""
echo "🌐 Step 5 (30s): Multilingual Support"
echo "   → Switch language across English, Hindi, Bengali, Assamese and Odia"
echo "   → Show all labels translate correctly"
echo ""
read -p "   Press Enter when ready for next step..."

echo ""
echo "📡 Step 6 (30s): Station Deep Dive"
echo "   → Click any station"
echo "   → Show sensor charts, AI gauge, weather data"
echo "   → Show contributing factors and recommendation"
echo ""
read -p "   Press Enter when ready for next step..."

echo ""
echo "🌊 Step 7 (30s): Flood Risk"
echo "   → Navigate to Flood Risk page"
echo "   → Show 19 districts with flood-landslide correlation"
echo "   → Show scatter plot"
echo ""
read -p "   Press Enter when ready for next step..."

echo ""
echo "🎯 Step 8: Key Metrics"
echo "   → Prototype dataset: 12,000 mixed/derived regional samples"
echo "   → Validation: district-grouped; not field accuracy"
echo "   → Stations: 20 across 8 NER states"
echo "   → Languages: 5 (EN, HI, BN, AS, OR)"
echo "   → Communication: WebSocket works locally; SMS/ntfy need provider configuration"
echo ""

echo "═══════════════════════════════════════════════════════════════"
echo "  🎉 Demo Complete!"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "  Backend running at: $BASE_URL"
echo "  Press Ctrl+C to stop"
echo ""

# Keep running
wait $BACKEND_PID
