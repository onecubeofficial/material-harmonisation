"""
db.py – SQLAlchemy engine and session factory.
"""
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from config import DATABASE_URL

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,          # discard stale connections before use
    pool_recycle=300,            # recycle connections every 5 min (Supabase drops idle ones)
    pool_timeout=30,             # wait max 30s for a connection from the pool
    connect_args={
        "connect_timeout": 10,   # TCP connect timeout in seconds
        "options": "-c statement_timeout=60000",  # 60s max per statement
    },
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""
    pass


def get_db():
    """FastAPI dependency: yields a DB session and closes it after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
