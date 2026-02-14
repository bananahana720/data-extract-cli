"""SQLite persistence for local UI/API runtime."""

from __future__ import annotations

import os
import time
from pathlib import Path
from threading import Lock
from typing import Any, Callable, Protocol, TypeVar

from sqlalchemy import create_engine, event, inspect, text
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
_DB_SERIALIZE_WRITE_LOCK = Lock()
_DB_RETRY_STATS: dict[str, Any] = {
    "attempts": 0,
    "retries": 0,
    "successes": 0,
    "failures": 0,
    "serialized_acquires": 0,
    "serialized_waits": 0,
    "operations": {},
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
    _ensure_runtime_schema_compatibility()


def _ensure_runtime_schema_compatibility() -> None:
    """Apply additive runtime columns/indexes for legacy sqlite databases."""
    jobs_columns = {
        "dispatch_payload": "TEXT NOT NULL DEFAULT '{}'",
        "dispatch_state": "VARCHAR(32) NOT NULL DEFAULT 'pending_dispatch'",
        "dispatch_attempts": "INTEGER NOT NULL DEFAULT 0",
        "dispatch_last_error": "TEXT",
        "dispatch_last_attempt_at": "DATETIME",
        "dispatch_next_attempt_at": "DATETIME",
        "artifact_sync_state": "VARCHAR(32) NOT NULL DEFAULT 'pending'",
        "artifact_sync_attempts": "INTEGER NOT NULL DEFAULT 0",
        "artifact_sync_error": "TEXT",
        "artifact_last_synced_at": "DATETIME",
        "result_checksum": "VARCHAR(128)",
    }
    sessions_columns = {
        "projection_source": "VARCHAR(64)",
        "projection_error": "TEXT",
        "last_reconciled_at": "DATETIME",
    }
    indexes = (
        (
            "ix_jobs_dispatch_state_next_attempt_at",
            "CREATE INDEX IF NOT EXISTS ix_jobs_dispatch_state_next_attempt_at "
            "ON jobs (dispatch_state, dispatch_next_attempt_at)",
        ),
        (
            "ix_jobs_artifact_sync_state_updated_at",
            "CREATE INDEX IF NOT EXISTS ix_jobs_artifact_sync_state_updated_at "
            "ON jobs (artifact_sync_state, updated_at)",
        ),
        (
            "ix_job_events_job_id_event_time",
            "CREATE INDEX IF NOT EXISTS ix_job_events_job_id_event_time "
            "ON job_events (job_id, event_time)",
        ),
    )

    with engine.begin() as conn:
        inspector = inspect(conn)
        existing_tables = set(inspector.get_table_names())
        if "jobs" in existing_tables:
            existing = {column["name"] for column in inspector.get_columns("jobs")}
            for name, ddl in jobs_columns.items():
                if name in existing:
                    continue
                conn.execute(text(f"ALTER TABLE jobs ADD COLUMN {name} {ddl}"))

        if "sessions" in existing_tables:
            existing = {column["name"] for column in inspector.get_columns("sessions")}
            for name, ddl in sessions_columns.items():
                if name in existing:
                    continue
                conn.execute(text(f"ALTER TABLE sessions ADD COLUMN {name} {ddl}"))

        for _name, ddl in indexes:
            conn.execute(text(ddl))


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


def _resolve_db_serialize_writes(explicit_value: bool | None = None) -> bool:
    if explicit_value is not None:
        return bool(explicit_value)
    raw = os.environ.get("DATA_EXTRACT_API_DB_SERIALIZE_WRITES", "1").strip().lower()
    return raw in {"1", "true", "yes", "on"}


def _normalize_operation_name(
    operation: Callable[[], Any], explicit_value: str | None = None
) -> str:
    if explicit_value:
        normalized = explicit_value.strip()
        if normalized:
            return normalized
    inferred = getattr(operation, "__name__", "") or ""
    normalized = inferred.strip()
    return normalized or "anonymous"


def _operation_stats_locked(operation_name: str) -> dict[str, Any]:
    operations = _DB_RETRY_STATS.setdefault("operations", {})
    if not isinstance(operations, dict):
        operations = {}
        _DB_RETRY_STATS["operations"] = operations
    current = operations.get(operation_name)
    if isinstance(current, dict):
        return current
    current = {
        "attempts": 0,
        "retries": 0,
        "successes": 0,
        "failures": 0,
        "serialized_acquires": 0,
        "serialized_waits": 0,
        "last_error": None,
        "last_attempt_at": None,
        "last_retry_at": None,
    }
    operations[operation_name] = current
    return current


def with_sqlite_lock_retry(
    operation: Callable[[], T],
    retries: int | None = None,
    backoff_ms: int | None = None,
    operation_name: str | None = None,
    serialize_writes: bool | None = None,
) -> T:
    """Run an operation with bounded retry/backoff for transient sqlite locks."""
    max_retries = _resolve_db_lock_retries(retries)
    delay_ms = _resolve_db_lock_backoff_ms(backoff_ms)
    op_name = _normalize_operation_name(operation, operation_name)
    should_serialize = _resolve_db_serialize_writes(serialize_writes)
    attempt = 0
    while True:
        now = time.time()
        with _DB_RETRY_STATS_LOCK:
            _DB_RETRY_STATS["attempts"] += 1
            op_stats = _operation_stats_locked(op_name)
            op_stats["attempts"] += 1
            op_stats["last_attempt_at"] = now
        try:
            if should_serialize:
                with _DB_RETRY_STATS_LOCK:
                    _DB_RETRY_STATS["serialized_acquires"] += 1
                    _operation_stats_locked(op_name)["serialized_acquires"] += 1
                with _DB_SERIALIZE_WRITE_LOCK:
                    result = operation()
            else:
                result = operation()
            with _DB_RETRY_STATS_LOCK:
                _DB_RETRY_STATS["successes"] += 1
                _operation_stats_locked(op_name)["successes"] += 1
            return result
        except Exception as exc:
            if not _is_sqlite_locked_error(exc) or attempt >= max_retries:
                with _DB_RETRY_STATS_LOCK:
                    _DB_RETRY_STATS["failures"] += 1
                    op_stats = _operation_stats_locked(op_name)
                    op_stats["failures"] += 1
                    op_stats["last_error"] = f"{type(exc).__name__}: {exc}"
                raise
            attempt += 1
            with _DB_RETRY_STATS_LOCK:
                _DB_RETRY_STATS["retries"] += 1
                op_stats = _operation_stats_locked(op_name)
                op_stats["retries"] += 1
                op_stats["last_retry_at"] = time.time()
                op_stats["last_error"] = f"{type(exc).__name__}: {exc}"
                if should_serialize:
                    _DB_RETRY_STATS["serialized_waits"] += 1
                    op_stats["serialized_waits"] += 1
            time.sleep((delay_ms / 1000.0) * attempt)


def sqlite_lock_retry_stats() -> dict[str, Any]:
    """Return aggregated lock retry stats for health reporting."""
    with _DB_RETRY_STATS_LOCK:
        snapshot = dict(_DB_RETRY_STATS)
        operations = _DB_RETRY_STATS.get("operations", {})
        if isinstance(operations, dict):
            snapshot["operations"] = {
                str(name): dict(stats) if isinstance(stats, dict) else {}
                for name, stats in operations.items()
            }
        else:
            snapshot["operations"] = {}
        return snapshot
