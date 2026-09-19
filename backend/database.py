"""
TenderPulse 4IR AI - Database Session & Connection Engine
SQLAlchemy 2.0 ORM Engine with PostgreSQL & SQLite Multi-Mode Support.
"""

import os
from typing import Generator
from urllib.parse import quote
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from backend.settings import get_settings

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

DEFAULT_SQLITE_PATH = os.path.join(DATA_DIR, "tenderpulse.db")


def resolve_database_url() -> str:
    """Resolve the database URL without exposing credentials in configuration.

    Compose supplies PostgreSQL credentials as separate variables so passwords
    containing URL-reserved characters (for example ``@`` or ``/``) remain
    valid. An explicit DATABASE_URL still takes precedence for local tooling.
    """
    explicit_url = os.environ.get("DATABASE_URL", "").strip()
    if explicit_url:
        return explicit_url

    postgres_host = os.environ.get("POSTGRES_HOST", "").strip()
    if postgres_host:
        user = quote(os.environ.get("POSTGRES_USER", "tenderpulse"), safe="")
        password = quote(os.environ.get("POSTGRES_PASSWORD", ""), safe="")
        database = quote(os.environ.get("POSTGRES_DB", "tenderpulse"), safe="")
        port = os.environ.get("POSTGRES_PORT", "5432").strip() or "5432"
        return f"postgresql+psycopg://{user}:{password}@{postgres_host}:{port}/{database}"

    return f"sqlite:///{DEFAULT_SQLITE_PATH}"


DATABASE_URL = resolve_database_url()

# Normalize PostgreSQL schema URI for SQLAlchemy 2.0 if needed
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg://", 1)
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)

# Configure engine connection arguments based on dialect
engine_kwargs = {}
if DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    engine_kwargs["pool_size"] = 10
    engine_kwargs["max_overflow"] = 20
    engine_kwargs["pool_pre_ping"] = True

engine = create_engine(DATABASE_URL, **engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency yielding database session per request.
    Ensures safe rollback and session teardown.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initializes local development schemas. Production schemas are managed by
    Alembic; Docker runs ``alembic upgrade head`` before starting FastAPI.
    """
    if get_settings().environment in {"development", "test"}:
        Base.metadata.create_all(bind=engine)
