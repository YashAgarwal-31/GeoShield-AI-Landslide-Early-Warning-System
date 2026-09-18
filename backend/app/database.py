import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

# Use DATABASE_URL env var if set (e.g. PostgreSQL for production),
# otherwise fall back to local SQLite for development.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./geoshield.db")

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
