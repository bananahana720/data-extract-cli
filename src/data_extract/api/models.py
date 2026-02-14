"""SQLAlchemy models for UI/API runtime persistence."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from data_extract.api.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Job(Base):
    """Primary processing job record."""

    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    status: Mapped[str] = mapped_column(String(32), index=True)
    input_path: Mapped[str] = mapped_column(Text)
    output_dir: Mapped[str] = mapped_column(Text)
    requested_format: Mapped[str] = mapped_column(String(32), default="json")
    chunk_size: Mapped[int] = mapped_column(Integer, default=512)
    request_payload: Mapped[str] = mapped_column(Text, default="{}")
    dispatch_payload: Mapped[str] = mapped_column(Text, default="{}")
    result_payload: Mapped[str] = mapped_column(Text, default="{}")
    request_hash: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    attempt: Mapped[int] = mapped_column(Integer, default=1)
    dispatch_state: Mapped[str] = mapped_column(String(32), default="pending_dispatch")
    dispatch_attempts: Mapped[int] = mapped_column(Integer, default=0)
    dispatch_last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    dispatch_last_attempt_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    dispatch_next_attempt_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    artifact_sync_state: Mapped[str] = mapped_column(String(32), default="pending")
    artifact_sync_attempts: Mapped[int] = mapped_column(Integer, default=0)
    artifact_sync_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    artifact_last_synced_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    result_checksum: Mapped[str | None] = mapped_column(String(128), nullable=True)
    artifact_dir: Mapped[str | None] = mapped_column(Text, nullable=True)
    session_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    files: Mapped[list[JobFile]] = relationship(back_populates="job", cascade="all, delete-orphan")
    events: Mapped[list[JobEvent]] = relationship(
        back_populates="job", cascade="all, delete-orphan"
    )


class JobFile(Base):
    """Per-file outcome linked to a job."""

    __tablename__ = "job_files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[str] = mapped_column(ForeignKey("jobs.id"), index=True)
    source_path: Mapped[str] = mapped_column(Text)
    output_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(16), index=True)
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    normalized_source_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    error_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    job: Mapped[Job] = relationship(back_populates="files")

    __table_args__ = (
        UniqueConstraint("job_id", "normalized_source_path", name="uq_job_files_job_norm_path"),
    )


class JobEvent(Base):
    """Append-only event stream for job progress."""

    __tablename__ = "job_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[str] = mapped_column(ForeignKey("jobs.id"), index=True)
    event_type: Mapped[str] = mapped_column(String(64), index=True)
    message: Mapped[str] = mapped_column(Text)
    payload: Mapped[str] = mapped_column(Text, default="{}")
    event_time: Mapped[datetime] = mapped_column(DateTime, default=utc_now, index=True)

    job: Mapped[Job] = relationship(back_populates="events")


class SessionRecord(Base):
    """Projected session summary for UI listing and filtering."""

    __tablename__ = "sessions"

    session_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    source_directory: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), index=True)
    total_files: Mapped[int] = mapped_column(Integer, default=0)
    processed_count: Mapped[int] = mapped_column(Integer, default=0)
    failed_count: Mapped[int] = mapped_column(Integer, default=0)
    artifact_dir: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_archived: Mapped[int] = mapped_column(Integer, default=0)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    projection_source: Mapped[str | None] = mapped_column(String(64), nullable=True)
    projection_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_reconciled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


class RetryRun(Base):
    """Retry operation history for auditing and UI traceability."""

    __tablename__ = "retry_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[str] = mapped_column(ForeignKey("jobs.id"), index=True)
    source_session_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(32), index=True)
    requested_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class AppSetting(Base):
    """Simple key-value app settings table."""

    __tablename__ = "app_settings"

    key: Mapped[str] = mapped_column(String(128), primary_key=True)
    value: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


Index(
    "ix_jobs_idempotency_hash",
    Job.idempotency_key,
    Job.request_hash,
    unique=True,
    sqlite_where=Job.idempotency_key.is_not(None),
)
Index(
    "ix_jobs_dispatch_state_next_attempt_at",
    Job.dispatch_state,
    Job.dispatch_next_attempt_at,
)
Index(
    "ix_jobs_artifact_sync_state_updated_at",
    Job.artifact_sync_state,
    Job.updated_at,
)
Index(
    "ix_job_events_job_id_event_time",
    JobEvent.job_id,
    JobEvent.event_time,
)
