@echo off
setlocal
title GeoShield - Prepare Offline Demo

echo.
echo ============================================
echo   GeoShield - One-Time Demo Preparation
echo ============================================
echo.
echo Internet is required only for this preparation step.
echo After this succeeds, use start-offline.bat without internet.
echo.

python --version >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Python 3.10+ is required.
  exit /b 1
)

node --version >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Node.js is required.
  exit /b 1
)

echo [1/6] Creating backend virtual environment...
if not exist "backend\venv\Scripts\python.exe" (
  python -m venv backend\venv
  if errorlevel 1 exit /b 1
)

echo [2/6] Installing backend dependencies...
backend\venv\Scripts\python.exe -m pip install --upgrade pip
if errorlevel 1 exit /b 1
backend\venv\Scripts\python.exe -m pip install -r backend\requirements.txt pytest
if errorlevel 1 exit /b 1
backend\venv\Scripts\python.exe -m pip check
if errorlevel 1 exit /b 1

echo [3/6] Installing locked frontend dependencies...
pushd frontend
call npm ci
if errorlevel 1 (
  popd
  exit /b 1
)

echo [4/6] Building frontend...
call npm run build
if errorlevel 1 (
  popd
  exit /b 1
)
popd

echo [5/6] Running complete backend test suite...
pushd backend
set APP_ENV=demo
set WEATHER_LIVE_ENABLED=false
set MODEL_TRAINING_ENABLED=false
set TRUST_PROXY_HEADERS=false
venv\Scripts\python.exe -m pytest tests -q
if errorlevel 1 (
  popd
  exit /b 1
)
popd

echo [6/6] Verifying offline artifacts...
if not exist "frontend\dist\index.html" (
  echo [ERROR] frontend\dist\index.html is missing.
  exit /b 1
)
if not exist "datasets\processed\real_satellite_data.json" (
  echo [ERROR] Cached satellite snapshot is missing.
  exit /b 1
)

echo.
echo ============================================
echo   PREPARATION COMPLETE
echo ============================================
echo Use start-offline.bat on presentation day.
echo.
endlocal
