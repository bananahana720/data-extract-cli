"""SQLite persistence for local UI/API runtime."""

from __future__ import annotations

import os
import time
from pathlib import Path
from threading import Lock
from typing import Any, Callable, Protocol, TypeVar

from sqlalchemy import create_engine, event
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import DeclarativeBase, sessionmaker

APP_HOME = Path(
    os.environ.get("DATA_EXTRACT_UI_HOME", Path.home() / ".data-extract-ui")
).expanduser()
APP_HOME.mkdir(parents=True, exist_ok=True)
DB_PATH = APP_HOME / "app.db"
JOBS_HOME = APP_HOME / "jobs"
JOBS_HOME.mkdir(parents=True, exist_ok=True)
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    DATABASE_URL,
    connect_args={
        "check_same_thread": False,
        "timeout": 30,
    },
    future=True,
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

T = TypeVar("T")
_DB_RETRY_STATS_LOCK = Lock()
_DB_RETRY_STATS: dict[str, int] = {
    "attempts": 0,
    "retries": 0,
    "successes": 0,
    "failures": 0,
}


class _DBCursor(Protocol):
    def execute(self, sql: str) -> object: ...

    def close(self) -> None: ...


class _SQLiteConnection(Protocol):
    def cursor(self) -> _DBCursor: ...


@event.listens_for(engine, "connect")
def _configure_sqlite_pragmas(
    dbapi_connection: _SQLiteConnection, _connection_record: object
) -> None:
    """Apply SQLite pragmas that reduce lock contention under concurrent access."""
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.execute("PRAGMA synchronous=NORMAL;")
        cursor.execute("PRAGMA busy_timeout=5000;")
        cursor.execute("PRAGMA foreign_keys=ON;")
    finally:
        cursor.close()


class Base(DeclarativeBase):
    """Base declarative class for API persistence models."""


def init_database() -> None:
    """Create database schema if it does not already exist."""
    from data_extract.api import models  # noqa: F401

    Base.metadata.create_all(bind=engine)


def _is_sqlite_locked_error(exc: Exception) -> bool:
    if isinstance(exc, OperationalError):
        return "database is locked" in str(exc).lower()
    return "database is locked" in str(exc).lower()


def _resolve_db_lock_retries(explicit_value: int | None = None) -> int:
    if explicit_value is not None:
        return max(0, int(explicit_value))
    raw = os.environ.get("DATA_EXTRACT_API_DB_LOCK_RETRIES", "5").strip()
    try:
        return max(0, int(raw))
    except ValueError:
        return 5


def _resolve_db_lock_backoff_ms(explicit_value: int | None = None) -> int:
    if explicit_value is not None:
        return max(1, int(explicit_value))
    raw = os.environ.get("DATA_EXTRACT_API_DB_LOCK_BACKOFF_MS", "100").strip()
    try:
        return max(1, int(raw))
    except ValueError:
        return 100


def with_sqlite_lock_retry(
    operation: Callable[[], T],
    retries: int | None = None,
    backoff_ms: int | None = None,
) -> T:
    """Run an operation with bounded retry/backoff for transient sqlite locks."""
    max_retries = _resolve_db_lock_retries(retries)
    delay_ms = _resolve_db_lock_backoff_ms(backoff_ms)
    attempt = 0
    while True:
        with _DB_RETRY_STATS_LOCK:
            _DB_RETRY_STATS["attempts"] += 1
        try:
            result = operation()
            with _DB_RETRY_STATS_LOCK:
                _DB_RETRY_STATS["successes"] += 1
            return result
        except Exception as exc:
            if not _is_sqlite_locked_error(exc) or attempt >= max_retries:
                with _DB_RETRY_STATS_LOCK:
                    _DB_RETRY_STATS["failures"] += 1
                raise
            attempt += 1
            with _DB_RETRY_STATS_LOCK:
                _DB_RETRY_STATS["retries"] += 1
            time.sleep((delay_ms / 1000.0) * attempt)


def sqlite_lock_retry_stats() -> dict[str, Any]:
    """Return aggregated lock retry stats for health reporting."""
    with _DB_RETRY_STATS_LOCK:
        return dict(_DB_RETRY_STATS)
