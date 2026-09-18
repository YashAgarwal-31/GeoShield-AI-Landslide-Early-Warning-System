@echo off
setlocal
title GeoShield - Operational Local Runtime

echo.
echo ============================================
echo   GeoShield - Operational Local Runtime
echo   AI-Based Landslide Risk Monitoring
echo ============================================
echo.

where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python was not found in PATH.
    echo Install Python 3.12 and run this script again.
    exit /b 1
)

where node >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js was not found in PATH.
    echo Install Node.js 22 LTS and run this script again.
    exit /b 1
)

where npm >nul 2>&1
if errorlevel 1 (
    echo [ERROR] npm was not found in PATH.
    exit /b 1
)

if "%APP_ENV%"=="" set APP_ENV=demo
if "%ENABLE_DEMO_USERS%"=="" set ENABLE_DEMO_USERS=true
if "%WEATHER_LIVE_ENABLED%"=="" set WEATHER_LIVE_ENABLED=false
if "%MODEL_TRAINING_ENABLED%"=="" set MODEL_TRAINING_ENABLED=false
if "%TRUST_PROXY_HEADERS%"=="" set TRUST_PROXY_HEADERS=false
if "%RATE_LIMIT_ENABLED%"=="" set RATE_LIMIT_ENABLED=true
if "%GEOSHIELD_BIND_HOST%"=="" set GEOSHIELD_BIND_HOST=127.0.0.1
if "%GEOSHIELD_PORT%"=="" set GEOSHIELD_PORT=8000
if "%CORS_ALLOWED_ORIGINS%"=="" set CORS_ALLOWED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000

echo [1/6] Preparing Python environment...
pushd backend
if not exist "venv\Scripts\python.exe" (
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create Python virtual environment.
        popd
        exit /b 1
    )
)
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] Failed to activate Python virtual environment.
    popd
    exit /b 1
)

echo [2/6] Installing and validating backend dependencies...
python -m pip install --upgrade pip
if errorlevel 1 (
    popd
    exit /b 1
)
python -m pip install -r requirements.txt
if errorlevel 1 (
    popd
    exit /b 1
)
python -m pip check
if errorlevel 1 (
    echo [ERROR] Backend dependency validation failed.
    popd
    exit /b 1
)
python -m compileall -q app
if errorlevel 1 (
    echo [ERROR] Backend Python compilation failed.
    popd
    exit /b 1
)
popd

echo [3/6] Installing deterministic frontend dependencies...
pushd frontend
call npm ci
if errorlevel 1 (
    echo [ERROR] Frontend dependency installation failed.
    popd
    exit /b 1
)

echo [4/6] Building production frontend bundle...
call npm run build
if errorlevel 1 (
    echo [ERROR] Frontend production build failed.
    popd
    exit /b 1
)
popd

if not exist "frontend\dist\index.html" (
    echo [ERROR] frontend\dist\index.html was not produced.
    exit /b 1
)

echo [5/6] Runtime configuration ready.
echo   Environment : %APP_ENV%
echo   Bind host   : %GEOSHIELD_BIND_HOST%
echo   Port        : %GEOSHIELD_PORT%
echo   Database    : local persistent SQLite unless DATABASE_URL is set
echo   Weather API : %WEATHER_LIVE_ENABLED%
echo.

echo [6/6] Starting GeoShield...
echo   URL         : http://%GEOSHIELD_BIND_HOST%:%GEOSHIELD_PORT%
echo   Health      : http://%GEOSHIELD_BIND_HOST%:%GEOSHIELD_PORT%/api/health/ready
echo.
echo Press Ctrl+C to stop the server.
echo.

pushd backend
python -m uvicorn app.main:app --host %GEOSHIELD_BIND_HOST% --port %GEOSHIELD_PORT%
set EXIT_CODE=%errorlevel%
popd

if not "%EXIT_CODE%"=="0" (
    echo.
    echo [ERROR] GeoShield stopped with exit code %EXIT_CODE%.
)
exit /b %EXIT_CODE%
