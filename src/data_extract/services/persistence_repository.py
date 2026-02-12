"""Canonical SQLite persistence helpers for runtime services."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

TERMINAL_STATUSES = {"completed", "partial", "failed"}
RUNNING_STATUSES = {"queued", "running"}


class PersistenceRepository:
    """Repository facade for canonical persistence operations."""

    def __init__(self) -> None:
        self._import_error: Exception | None = None

    def _deps(self) -> tuple[Any, Any, Any, Any, Any, Any] | None:
        """Load persistence dependencies lazily to keep CLI usable in restricted envs."""
        if self._import_error is not None:
            return None
        try:
            from sqlalchemy import func, select

            from data_extract.api.database import SessionLocal, init_database
            from data_extract.api.models import Job, JobFile, SessionRecord

            init_database()
        except Exception as exc:
            self._import_error = exc
            return None
        return SessionLocal, Job, JobFile, SessionRecord, select, func

    def find_idempotent_job(
        self, idempotency_key: str, request_hash: str
    ) -> tuple[str, str, dict[str, Any]] | None:
        """Return existing idempotent job tuple when available."""
        deps = self._deps()
        if deps is None:
            return None
        session_local, job_model, _job_file_model, _session_record_model, select_stmt, _func = deps
        try:
            with session_local() as db:
                stmt = (
                    select_stmt(job_model)
                    .where(
                        job_model.idempotency_key == idempotency_key,
                        job_model.request_hash == request_hash,
                    )
                    .order_by(job_model.updated_at.desc())
                )
                job = db.scalar(stmt)
                if job is None:
                    return None
                payload = self._load_json(job.result_payload)
                return job.id, job.status, payload
        except Exception:
            return None

    def update_job_metadata(
        self,
        job_id: str,
        request_hash: str | None,
        idempotency_key: str | None,
        artifact_dir: str | None,
        attempt: int = 1,
    ) -> None:
        """Persist canonical metadata fields onto a job row."""
        deps = self._deps()
        if deps is None:
            return
        session_local, job_model, _job_file_model, _session_record_model, _select, _func = deps
        try:
            with session_local() as db:
                job = db.get(job_model, job_id)
                if job is None:
                    return
                job.request_hash = request_hash
                job.idempotency_key = idempotency_key
                job.attempt = attempt
                job.artifact_dir = artifact_dir
                db.commit()
        except Exception:
            return

    def max_retry_count(self, normalized_source_path: str) -> int:
        """Return max retry count for a normalized source path."""
        deps = self._deps()
        if deps is None:
            return 0
        session_local, _job_model, job_file_model, _session_record_model, select_stmt, func_stmt = (
            deps
        )
        try:
            with session_local() as db:
                stmt = select_stmt(func_stmt.max(job_file_model.retry_count)).where(
                    job_file_model.normalized_source_path == normalized_source_path
                )
                value = db.scalar(stmt)
            return int(value or 0)
        except Exception:
            return 0

    def upsert_session_record(
        self,
        payload: dict[str, Any],
        artifact_dir: str | None = None,
        is_archived: bool = False,
        archived_at: datetime | None = None,
    ) -> None:
        """Write/refresh canonical session projection from payload."""
        deps = self._deps()
        if deps is None:
            return
        session_local, _job_model, _job_file_model, session_record_model, _select, _func = deps
        session_id = str(payload.get("session_id") or "")
        if not session_id:
            return

        stats = payload.get("statistics", {})
        updated_raw = payload.get("updated_at")
        if not isinstance(updated_raw, str):
            return

        try:
            updated_at = datetime.fromisoformat(updated_raw)
        except ValueError:
            return

        try:
            with session_local() as db:
                record = db.get(session_record_model, session_id)
                if record is None:
                    record = session_record_model(
                        session_id=session_id,
                        source_directory=str(payload.get("source_directory", "")),
                        status=str(payload.get("status", "unknown")),
                        total_files=int(
                            stats.get("total_files", payload.get("total_files", 0) or 0)
                        ),
                        processed_count=int(stats.get("processed_count", 0)),
                        failed_count=int(stats.get("failed_count", 0)),
                        artifact_dir=artifact_dir,
                        is_archived=1 if is_archived else 0,
                        archived_at=archived_at,
                        updated_at=updated_at,
                    )
                    db.add(record)
                else:
                    record.source_directory = str(payload.get("source_directory", ""))
                    record.status = str(payload.get("status", "unknown"))
                    record.total_files = int(
                        stats.get("total_files", payload.get("total_files", 0) or 0)
                    )
                    record.processed_count = int(stats.get("processed_count", 0))
                    record.failed_count = int(stats.get("failed_count", 0))
                    record.artifact_dir = artifact_dir
                    record.is_archived = 1 if is_archived else 0
                    record.archived_at = archived_at
                    record.updated_at = updated_at
                db.commit()
        except Exception:
            return

    def session_payload(self, session_id: str) -> dict[str, Any] | None:
        """Build retry/session payload from canonical job records."""
        deps = self._deps()
        if deps is None:
            return None
        session_local, job_model, _job_file_model, _session_record_model, select_stmt, _func = deps
        try:
            with session_local() as db:
                stmt = (
                    select_stmt(job_model)
                    .where(job_model.session_id == session_id)
                    .order_by(job_model.updated_at.desc())
                )
                jobs = list(db.scalars(stmt))
            for job in jobs:
                payload = self._session_payload_from_job(job)
                if payload:
                    return payload
            return None
        except Exception:
            return None

    def latest_session_payload(self) -> dict[str, Any] | None:
        """Return most recently updated canonical session payload."""
        deps = self._deps()
        if deps is None:
            return None
        session_local, _job_model, _job_file_model, session_record_model, select_stmt, _func = deps
        try:
            with session_local() as db:
                records = list(
                    db.scalars(
                        select_stmt(session_record_model).order_by(
                            session_record_model.updated_at.desc()
                        )
                    )
                )

            for record in records:
                payload = self.session_payload(record.session_id)
                if payload:
                    return payload
            return None
        except Exception:
            return None

    @staticmethod
    def _load_json(raw: str | None) -> dict[str, Any]:
        if not raw:
            return {}
        try:
            value = json.loads(raw)
        except json.JSONDecodeError:
            return {}
        return value if isinstance(value, dict) else {}

    def _session_payload_from_job(self, job: Any) -> dict[str, Any] | None:
        result = self._load_json(job.result_payload)
        processed = result.get("processed_files", [])
        failed = result.get("failed_files", [])

        if not processed and not failed and job.status not in TERMINAL_STATUSES:
            return None

        started_at = result.get("started_at")
        finished_at = result.get("finished_at")
        started = (
            started_at
            if isinstance(started_at, str)
            else (job.started_at or job.created_at).isoformat()
        )
        updated = finished_at if isinstance(finished_at, str) else job.updated_at.isoformat()

        source_path = Path(job.input_path)
        source_directory = source_path if source_path.is_dir() else source_path.parent

        total_files = int(result.get("total_files", len(processed) + len(failed)))
        processed_count = int(result.get("processed_count", len(processed)))
        failed_count = int(result.get("failed_count", len(failed)))
        skipped_count = int(result.get("skipped_count", 0))

        return {
            "session_id": job.session_id or "",
            "status": str(result.get("status", job.status)),
            "source_directory": str(source_directory),
            "output_directory": str(result.get("output_dir", job.output_dir)),
            "total_files": total_files,
            "processed_files": processed,
            "failed_files": failed,
            "started_at": started,
            "updated_at": updated,
            "configuration": {
                "output_path": str(result.get("output_dir", job.output_dir)),
                "format": job.requested_format,
                "chunk_size": job.chunk_size,
            },
            "schema_version": "2.0",
            "statistics": {
                "total_files": total_files,
                "processed_count": processed_count,
                "failed_count": failed_count,
                "skipped_count": skipped_count,
            },
        }
