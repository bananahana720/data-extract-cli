"""SQLite persistence for local UI/API runtime."""

from __future__ import annotations

import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


APP_HOME = Path(os.environ.get("DATA_EXTRACT_UI_HOME", Path.home() / ".data-extract-ui")).expanduser()
APP_HOME.mkdir(parents=True, exist_ok=True)
DB_PATH = APP_HOME / "app.db"
JOBS_HOME = APP_HOME / "jobs"
JOBS_HOME.mkdir(parents=True, exist_ok=True)
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    future=True,
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


class Base(DeclarativeBase):
    """Base declarative class for API persistence models."""



def init_database() -> None:
    """Create database schema if it does not already exist."""
    from data_extract.api import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
