"""SQLAlchemy engine/session setup and pgvector-aware DB initialization."""
from __future__ import annotations

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from ..config import get_settings

Base = declarative_base()

_engine = None
_SessionLocal: sessionmaker | None = None


def normalize_db_url(url: str) -> str:
    """Normalize a Postgres URL to the SQLAlchemy + psycopg (v3) driver form."""
    if url.startswith("postgresql+psycopg://"):
        return url
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    if url.startswith("postgresql://"):
        return "postgresql+psycopg://" + url[len("postgresql://"):]
    return url


def init_engine():
    global _engine, _SessionLocal
    if _engine is None:
        settings = get_settings()
        if not settings.database_url:
            raise RuntimeError("DATABASE_URL is not set. Add it to backend/.env.")
        _engine = create_engine(normalize_db_url(settings.database_url), pool_pre_ping=True)
        _SessionLocal = sessionmaker(bind=_engine, autoflush=False, autocommit=False)
    return _engine


def init_db() -> None:
    """Enable the pgvector extension and create all tables."""
    from . import models  # noqa: F401  (register models on Base)

    engine = init_engine()
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()
    Base.metadata.create_all(engine)


def get_session() -> Session:
    """FastAPI dependency yielding a database session."""
    if _SessionLocal is None:
        init_engine()
    assert _SessionLocal is not None
    session = _SessionLocal()
    try:
        yield session
    finally:
        session.close()
