"""
SQLAlchemy engine + session management.

We use a single shared engine per process and hand out short-lived
sessions per request via the `get_db` FastAPI dependency (see api/deps.py).
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import get_settings

settings = get_settings()

engine = create_engine(settings.database_url, pool_pre_ping=True, future=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)

Base = declarative_base()
