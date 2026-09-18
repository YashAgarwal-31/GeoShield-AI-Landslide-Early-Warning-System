"""
GeoShield - AI-Based Early Warning and Landslide Risk Monitoring System
Backend API Server for Smart India Hackathon 2026
"""
import os
import sys
from datetime import datetime, timezone

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.staticfiles import StaticFiles
from starlette.responses import FileResponse
from app.middleware.rate_limiter import RateLimiter


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


APP_ENV = os.getenv("APP_ENV", "demo").strip().lower()
IS_PRODUCTION = APP_ENV in {"prod", "production"}

# Fail closed before importing routers/auth, because those modules load the JWT
# secret during import. Local demo mode keeps the existing zero-config flow.
if IS_PRODUCTION:
    _jwt_secret = os.getenv("JWT_SECRET", "").strip()
    if len(_jwt_secret) < 32:
        raise RuntimeError(
            "APP_ENV=production requires JWT_SECRET with at least 32 characters."
        )


def _cors_origins() -> list[str]:
    raw = os.getenv("CORS_ALLOWED_ORIGINS", "").strip()
    if raw:
        return [origin.strip() for origin in raw.split(",") if origin.strip()]
    if IS_PRODUCTION:
        return []
    return [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "https://localhost",
        "capacitor://localhost",
    ]


from app.database import engine, Base, SessionLocal
from app.routers import sensors, dashboard, alerts, reports, weather, simulator, satellite, predict, alerts_timeline, flood, ml_enhanced, users
from app.auth import authenticate_user, create_token, ensure_bootstrap_admin, resolve_token_user
from app.realtime import alert_manager
from app.database import get_db


def init_database():
    """Apply schema migrations, optional reference seed data, and auth bootstrap."""
    import subprocess
    from sqlalchemy import inspect

    backend_dir = os.path.dirname(os.path.dirname(__file__))

    def _run_alembic(*args: str) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "alembic", *args],
            cwd=backend_dir,
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"Alembic {' '.join(args)} failed: "
                f"{result.stderr.strip() or result.stdout.strip()}"
            )

    try:
        existing_tables = set(inspect(engine).get_table_names())

        # Older local GeoShield databases were created with SQLAlchemy create_all
        # and therefore have no alembic_version table. Their schema corresponds
        # to the 0001 baseline, so stamp that revision before applying upgrades.
        if existing_tables and "alembic_version" not in existing_tables:
            if "sensor_stations" not in existing_tables:
                raise RuntimeError(
                    "Existing database has an unknown schema and cannot be auto-migrated."
                )
            _run_alembic("stamp", "0001")
            print("[GeoShield] Legacy database stamped at migration 0001")

        _run_alembic("upgrade", "head")
        print("[GeoShield] Database migrations applied")
    except Exception as exc:
        raise RuntimeError(f"Database initialization failed: {exc}") from exc

    db = SessionLocal()
    try:
        from app.models import SensorStation

        auto_seed = _env_bool("AUTO_SEED_REFERENCE_DATA", default=not IS_PRODUCTION)
        station_count = db.query(SensorStation).count()
        if station_count == 0 and auto_seed:
            from app.seed_data import seed_database

            seed_database()
        elif station_count == 0:
            print("[GeoShield] Reference station seeding is disabled; database starts empty.")
        else:
            print("[GeoShield] Reference station data already present, skipping seed.")

        ensure_bootstrap_admin(db)

        if IS_PRODUCTION and not _env_bool("ENABLE_DEMO_USERS", False):
            from app.models import UserAccount

            if db.query(UserAccount).filter(UserAccount.is_active == True).count() == 0:
                raise RuntimeError(
                    "Production database has no active user. Configure the bootstrap admin "
                    "for the first startup or restore an existing user database."
                )
    finally:
        db.close()

    print("[GeoShield] Database ready")

    # Report snapshot status without claiming or attempting an automatic refresh.
    try:
        sat_data, sat_source = satellite.satellite_adapter.load()
        freshness = "stale" if sat_source["is_stale"] else "fresh"
        print(
            f"[GeoShield] Satellite snapshot: {len(sat_data)} stations, "
            f"mode={sat_source['mode']}, freshness={freshness}, "
            f"observed_at={sat_source['observed_at']}"
        )
    except Exception as exc:
        print(f"[GeoShield] Satellite status check skipped: {exc}")


init_database()

FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist"))

app = FastAPI(
    title="GeoShield API",
    description="AI-Based Early Warning and Landslide Risk Monitoring System for NER",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)
app.add_middleware(RateLimiter)


@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=(self)"
    if request.url.path.startswith("/api/auth/"):
        response.headers["Cache-Control"] = "no-store"
    return response

app.include_router(sensors.router)
app.include_router(dashboard.router)
app.include_router(alerts.router)
app.include_router(reports.router)
app.include_router(weather.router)
app.include_router(simulator.router)
app.include_router(satellite.router)
app.include_router(predict.router)
app.include_router(alerts_timeline.router)
app.include_router(flood.router)
app.include_router(ml_enhanced.router)
app.include_router(users.router)


@app.get("/health", response_class=JSONResponse)
@app.get("/api/health", response_class=JSONResponse)
def health_check():
    return {
        "status": "healthy",
        "service": "geoshield-api",
        "timestamp": datetime.now(timezone.utc).replace(tzinfo=None).isoformat(),
    }


@app.get("/api/health/ready", response_class=JSONResponse)
def readiness_check(db=Depends(get_db)):
    from sqlalchemy import text
    from app.ai_engine.risk_predictor import TRAINING_DATA_PATH

    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Database unavailable: {exc}")

    training_data_available = os.path.isfile(TRAINING_DATA_PATH)
    synthetic_fallback_allowed = _env_bool(
        "ALLOW_SYNTHETIC_MODEL_FALLBACK",
        default=not IS_PRODUCTION,
    )
    if IS_PRODUCTION and not training_data_available and not synthetic_fallback_allowed:
        raise HTTPException(
            status_code=503,
            detail="ML training data unavailable and synthetic fallback is disabled",
        )

    return {
        "status": "ready",
        "database": "connected",
        "ml_training_data": "available" if training_data_available else "fallback_allowed",
        "synthetic_model_fallback": synthetic_fallback_allowed,
        "environment": APP_ENV,
        "timestamp": datetime.now(timezone.utc).replace(tzinfo=None).isoformat(),
    }


@app.post("/api/auth/login")
def login(email: str = Form(...), password: str = Form(...), db=Depends(get_db)):
    user = authenticate_user(email, password, db=db)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = create_token(user)
    return {
        "token": token,
        "user": {
            "email": user["email"],
            "name": user["name"],
            "role": user["role"],
        },
    }


@app.websocket("/ws/alerts/{district}")
async def websocket_alerts(
    websocket: WebSocket,
    district: str = "all",
    token: str | None = None,
):
    """Authenticated district-scoped stream for operational alert events."""
    if not token:
        await websocket.close(code=4401, reason="Authentication required")
        return

    db = SessionLocal()
    try:
        user = resolve_token_user(token, db)
    except HTTPException:
        await websocket.close(code=4401, reason="Invalid, expired, or revoked token")
        return
    finally:
        db.close()

    await alert_manager.connect(websocket, district=district, user=user)
    try:
        await websocket.send_json({
            "type": "connected",
            "district": district,
            "role": user.get("role"),
            "message": f"Connected to {district} alert stream",
        })
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_json({"type": "pong"})
            elif data.startswith("subscribe:"):
                new_district = await alert_manager.subscribe(
                    websocket, data.split(":", 1)[1]
                )
                await websocket.send_json({
                    "type": "subscribed",
                    "district": new_district,
                })
    except WebSocketDisconnect:
        pass
    finally:
        await alert_manager.disconnect(websocket)


@app.websocket("/ws/alerts")
async def websocket_alerts_all(websocket: WebSocket, token: str | None = None):
    """Authenticated legacy all-district alert stream."""
    await websocket_alerts(websocket=websocket, district="all", token=token)


# Serve frontend static files
if os.path.exists(os.path.join(FRONTEND_DIR, "assets")):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIR, "assets")), name="assets")

if os.path.exists(FRONTEND_DIR):
    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_frontend(full_path: str):
        # Skip ALL API, WebSocket, and health routes - never return HTML for these
        if (full_path.startswith("api/") or full_path.startswith("ws") 
            or full_path == "health" or full_path == "api"):
            return JSONResponse({"message": "API endpoint not found", "path": full_path}, status_code=404)
        # Sanitize path to prevent path traversal attacks
        if full_path:
            normalized = os.path.normpath(full_path).lstrip(os.sep)
            if normalized.startswith("..") or os.path.isabs(normalized):
                return {"message": "Not found", "version": "1.0.0"}
            file_path = os.path.abspath(os.path.join(FRONTEND_DIR, normalized))
            # Use commonpath rather than a string prefix check so sibling paths
            # such as "dist-evil" can never pass containment validation.
            try:
                if os.path.commonpath([FRONTEND_DIR, file_path]) != FRONTEND_DIR:
                    return {"message": "Not found", "version": "1.0.0"}
            except ValueError:
                return {"message": "Not found", "version": "1.0.0"}
            if os.path.isfile(file_path):
                return FileResponse(file_path)
        # Serve index.html for all other routes (SPA routing)
        index_path = os.path.join(FRONTEND_DIR, "index.html")
        if os.path.isfile(index_path):
            return FileResponse(index_path)
        return {"message": "GeoShield API", "version": "1.0.0"}
