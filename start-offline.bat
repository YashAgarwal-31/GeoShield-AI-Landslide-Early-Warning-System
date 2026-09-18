@echo off
setlocal
title GeoShield - Offline Presentation Mode

echo.
echo ============================================
echo   GeoShield - Offline Presentation Mode
echo ============================================
echo.

if not exist "backend\venv\Scripts\python.exe" (
  echo [ERROR] Prepared Python environment not found.
  echo Run prepare-demo.bat once while internet is available.
  exit /b 1
)

if not exist "frontend\dist\index.html" (
  echo [ERROR] Prepared frontend build not found.
  echo Run prepare-demo.bat once while internet is available.
  exit /b 1
)

if not exist "datasets\processed\real_satellite_data.json" (
  echo [ERROR] Cached satellite data is missing.
  exit /b 1
)

set APP_ENV=demo
set ENABLE_DEMO_USERS=true
set WEATHER_LIVE_ENABLED=false
set MODEL_TRAINING_ENABLED=false
set TRUST_PROXY_HEADERS=false
set CORS_ALLOWED_ORIGINS=http://127.0.0.1:8000,http://localhost:8000
set JWT_SECRET=geoshield-offline-demo-localhost-only-key

echo [GeoShield] Offline-safe data mode enabled.
echo [GeoShield] Live weather disabled.
echo [GeoShield] Model retraining disabled.
echo [GeoShield] Server restricted to localhost.
echo.
echo Open:
echo   http://127.0.0.1:8000
echo.
echo Press Ctrl+C to stop.
echo.

pushd backend
venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
set EXIT_CODE=%errorlevel%
popd
endlocal & exit /b %EXIT_CODE%
