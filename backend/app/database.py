import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

# Use DATABASE_URL when set (for example PostgreSQL in production). The local
# SQLite fallback is anchored to backend/ so migrations and the application use
# the same database even when GeoShield is launched or tested from the repo root.
BACKEND_DIR = Path(__file__).resolve().parents[1]
DEFAULT_SQLITE_PATH = (BACKEND_DIR / "geoshield.db").as_posix()
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_SQLITE_PATH}")

# SQLite-specific args (not needed for PostgreSQL/MySQL)
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
