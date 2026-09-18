"""
GeoShield - AI-Based Early Warning and Landslide Risk Monitoring System
Backend API Server for Smart India Hackathon 2026
"""
import os
import sys
from datetime import datetime, timezone
from typing import List

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
    ]


from app.database import engine, Base, SessionLocal
from app.routers import sensors, dashboard, alerts, reports, weather, simulator, satellite, predict, alerts_timeline, flood, ml_enhanced, users
from app.auth import authenticate_user, create_token, ensure_bootstrap_admin
from app.database import get_db


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except WebSocketDisconnect:
                disconnected.append(connection)
            except RuntimeError as e:
                # Connection closed or other runtime error
                disconnected.append(connection)
        
        # Remove disconnected connections after iteration
        for conn in disconnected:
            self.disconnect(conn)


manager = ConnectionManager()


def init_database():
    # Use Alembic for production (PostgreSQL), create_all for local dev (SQLite)
    database_url = os.getenv("DATABASE_URL", "")
    if database_url and not database_url.startswith("sqlite"):
        # Production: run Alembic migrations
        try:
            import subprocess
            alembic_ini = os.path.join(os.path.dirname(__file__), "..", "alembic.ini")
            result = subprocess.run(
                [sys.executable, "-m", "alembic", "upgrade", "head"],
                cwd=os.path.dirname(os.path.dirname(__file__)),
                capture_output=True, text=True, timeout=30
            )
            if result.returncode != 0:
                print(f"[GeoShield] ⚠️  Alembic error: {result.stderr}")
            else:
                print("[GeoShield] ✅ Alembic migrations applied")
        except Exception as e:
            print(f"[GeoShield] ⚠️  Alembic failed: {e}, falling back to create_all")
            Base.metadata.create_all(bind=engine)
    else:
        # Development: create_all for instant setup
        Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        from app.models import SensorStation
        if db.query(SensorStation).count() == 0:
            from app.seed_data import seed_database
            seed_database()
        else:
            print("[GeoShield] Database already seeded, skipping.")
    finally:
        db.close()
    print("[GeoShield] ✅ Database ready")

    # Report snapshot status without claiming or attempting an automatic refresh.
    try:
        sat_data, sat_source = satellite.satellite_adapter.load()
        freshness = "stale" if sat_source["is_stale"] else "fresh"
        print(
            f"[GeoShield] Satellite snapshot: {len(sat_data)} stations, "
            f"mode={sat_source['mode']}, freshness={freshness}, "
            f"observed_at={sat_source['observed_at']}"
        )
    except Exception as e:
        print(f"[GeoShield] Satellite status check skipped: {e}")


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
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).replace(tzinfo=None).isoformat()}


@app.post("/api/auth/login")
def login(email: str = Form(...), password: str = Form(...)):
    user = authenticate_user(email, password)
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
async def websocket_alerts(websocket: WebSocket, district: str = "all"):
    """District-scoped WebSocket for real-time alert broadcasting."""
    await manager.connect(websocket)
    try:
        await websocket.send_json({"type": "connected", "district": district, "message": f"Connected to {district} alert stream"})
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_json({"type": "pong"})
            elif data.startswith("subscribe:"):
                new_district = data.split(":", 1)[1]
                await websocket.send_json({"type": "subscribed", "district": new_district})
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@app.websocket("/ws/alerts")
async def websocket_alerts_all(websocket: WebSocket):
    """Legacy endpoint - connects to all districts."""
    await manager.connect(websocket)
    try:
        await websocket.send_json({"type": "connected", "district": "all"})
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        manager.disconnect(websocket)


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
