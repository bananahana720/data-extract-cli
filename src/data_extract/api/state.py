"""API runtime state: queue + service orchestration."""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, cast

from sqlalchemy import delete, select

from data_extract.api.database import JOBS_HOME, SessionLocal, init_database
from data_extract.api.models import Job, JobEvent, JobFile, RetryRun, SessionRecord
from data_extract.contracts import JobStatus, ProcessJobRequest, RetryRequest
from data_extract.runtime import LocalJobQueue
from data_extract.services import JobService, RetryService
from data_extract.services.pathing import normalized_path_text
from data_extract.services.persistence_repository import (
    RUNNING_STATUSES,
    TERMINAL_STATUSES,
    PersistenceRepository,
)


class ApiRuntime:
    """Owns queue lifecycle and background job handlers."""

    def __init__(self) -> None:
        self.job_service = JobService()
        self.persistence = PersistenceRepository()
        self._worker_count = self._resolve_worker_count()
        self.queue = LocalJobQueue(self._handle_job, worker_count=self._worker_count)
        self._recovery_stats = {"requeued": 0, "failed": 0}
        self._readiness_report: dict[str, Any] = {
            "status": "unknown",
            "ready": False,
            "errors": [],
            "warnings": [],
            "checks": {},
            "checked_at": None,
        }

    def start(self) -> None:
        """Initialize schema and start background worker."""
        init_database()
        self.queue.start()
        self._recover_inflight_jobs()

    def stop(self) -> None:
        """Stop background worker."""
        self.queue.stop()

    @property
    def worker_count(self) -> int:
        """Configured queue worker count."""
        return self._worker_count

    @property
    def queue_backlog(self) -> int:
        """Approximate number of jobs pending in queue memory."""
        return self.queue.backlog

    @property
    def recovery_stats(self) -> dict[str, int]:
        """Snapshot of last startup recovery actions."""
        return dict(self._recovery_stats)

    def set_readiness_report(self, report: dict[str, Any]) -> None:
        """Store startup readiness report snapshot."""
        self._readiness_report = dict(report)

    @property
    def readiness_report(self) -> dict[str, Any]:
        """Return latest startup readiness report."""
        return dict(self._readiness_report)

    def enqueue_process(self, request: ProcessJobRequest, job_id: str | None = None) -> str:
        """Create queued process job and submit to worker."""
        effective_job_id = job_id or str(uuid.uuid4())[:12]
        job_dirs = self._job_dirs(effective_job_id)
        normalized_request = request.model_copy(
            update={
                "output_path": str(job_dirs["outputs"]),
            }
        )
        request_hash = self._compute_request_hash(normalized_request)
        if normalized_request.idempotency_key and request_hash:
            existing = self.persistence.find_idempotent_job(
                normalized_request.idempotency_key,
                request_hash,
            )
            if existing:
                existing_job_id, status, _payload = existing
                if status in TERMINAL_STATUSES or status in RUNNING_STATUSES:
                    return existing_job_id

        with SessionLocal() as db:
            job = Job(
                id=effective_job_id,
                status=JobStatus.QUEUED.value,
                input_path=normalized_request.input_path,
                output_dir=normalized_request.output_path or "",
                requested_format=normalized_request.output_format,
                chunk_size=normalized_request.chunk_size,
                request_payload=json.dumps(normalized_request.model_dump(), default=str),
                request_hash=request_hash,
                idempotency_key=normalized_request.idempotency_key,
                attempt=1,
                artifact_dir=str(job_dirs["root"]),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            db.add(job)
            db.add(
                JobEvent(
                    job_id=effective_job_id,
                    event_type="queued",
                    message="Job queued for processing",
                    payload="{}",
                    event_time=datetime.utcnow(),
                )
            )
            db.commit()

        self._write_job_log(effective_job_id, "Job queued for processing")
        self.queue.submit(
            effective_job_id, {"kind": "process", "request": normalized_request.model_dump()}
        )
        return effective_job_id

    def enqueue_retry(self, job_id: str, request: RetryRequest) -> None:
        """Submit retry action to worker for existing job id."""
        self._write_job_log(job_id, "Retry queued")
        self.queue.submit(job_id, {"kind": "retry", "request": request.model_dump()})

    def _handle_job(self, job_id: str, payload: Dict[str, Any]) -> None:
        """Worker callback for process/retry execution."""
        kind = payload.get("kind", "process")
        request_payload = payload.get("request", {})
        input_path = ""

        with SessionLocal() as db:
            job = db.get(Job, job_id)
            if not job:
                return
            input_path = job.input_path

            job.status = JobStatus.RUNNING.value
            job.started_at = datetime.utcnow()
            job.updated_at = datetime.utcnow()
            db.add(
                JobEvent(
                    job_id=job_id,
                    event_type="running",
                    message="Job is running",
                    payload="{}",
                    event_time=datetime.utcnow(),
                )
            )
            db.commit()
        self._write_job_log(job_id, "Job started")

        try:
            # Build fresh services per task to avoid shared mutable pipeline state
            # across concurrent queue workers.
            job_service = JobService()
            retry_service = RetryService(job_service=job_service)
            if kind == "retry":
                result = retry_service.run_retry(
                    RetryRequest(**request_payload),
                    work_dir=self._resolve_work_dir(input_path),
                )
            else:
                result = job_service.run_process(
                    ProcessJobRequest(**request_payload),
                    job_id=job_id,
                    work_dir=self._resolve_work_dir(input_path),
                )

            self._persist_result(job_id, result.model_dump())
        except Exception as exc:
            self._persist_exception(job_id, exc)

    def _persist_result(self, job_id: str, result: Dict[str, Any]) -> None:
        """Persist successful/partial/failed result data."""
        with SessionLocal() as db:
            job = db.get(Job, job_id)
            if not job:
                return

            raw_status = result.get("status", JobStatus.FAILED.value)
            status = raw_status.value if isinstance(raw_status, JobStatus) else str(raw_status)
            job.status = status
            job.result_payload = json.dumps(result, default=str)
            job.output_dir = result.get("output_dir", job.output_dir)
            job.request_hash = result.get("request_hash", job.request_hash)
            job.artifact_dir = result.get("artifact_dir", job.artifact_dir)
            job.session_id = result.get("session_id")
            job.finished_at = datetime.utcnow()
            job.updated_at = datetime.utcnow()

            db.execute(delete(JobFile).where(JobFile.job_id == job_id))

            for processed in result.get("processed_files", []):
                source_path = str(processed.get("path", ""))
                db.add(
                    JobFile(
                        job_id=job_id,
                        source_path=source_path,
                        normalized_source_path=(
                            normalized_path_text(source_path) if source_path else None
                        ),
                        output_path=processed.get("output_path"),
                        status="processed",
                        chunk_count=processed.get("chunk_count", 0),
                    )
                )

            for failed in result.get("failed_files", []):
                source_path = str(failed.get("path", ""))
                db.add(
                    JobFile(
                        job_id=job_id,
                        source_path=source_path,
                        normalized_source_path=(
                            normalized_path_text(source_path) if source_path else None
                        ),
                        output_path=None,
                        status="failed",
                        chunk_count=0,
                        retry_count=int(failed.get("retry_count", 0)),
                        error_type=failed.get("error_type"),
                        error_message=failed.get("error_message"),
                    )
                )

            if job.session_id:
                self._upsert_session(
                    db,
                    job.session_id,
                    job.input_path,
                    artifact_dir=job.artifact_dir,
                    is_archived=status in {JobStatus.PARTIAL.value, JobStatus.FAILED.value},
                    archived_at=(
                        datetime.utcnow()
                        if status in {JobStatus.PARTIAL.value, JobStatus.FAILED.value}
                        else None
                    ),
                )

            if status in {JobStatus.PARTIAL.value, JobStatus.FAILED.value}:
                db.add(
                    RetryRun(
                        job_id=job_id,
                        source_session_id=job.session_id,
                        status="available",
                        requested_at=datetime.utcnow(),
                    )
                )

            db.add(
                JobEvent(
                    job_id=job_id,
                    event_type="finished",
                    message=f"Job finished with status={status}",
                    payload="{}",
                    event_time=datetime.utcnow(),
                )
            )

            db.commit()
        self._write_job_artifact(job_id, result)
        self._write_job_log(job_id, f"Job finished with status={status}")

    def _persist_exception(self, job_id: str, exc: Exception) -> None:
        """Persist worker exception as terminal failed state."""
        with SessionLocal() as db:
            job = db.get(Job, job_id)
            if not job:
                return

            job.status = JobStatus.FAILED.value
            job.result_payload = json.dumps({"error": str(exc)})
            job.finished_at = datetime.utcnow()
            job.updated_at = datetime.utcnow()
            db.add(
                JobEvent(
                    job_id=job_id,
                    event_type="error",
                    message=str(exc),
                    payload="{}",
                    event_time=datetime.utcnow(),
                )
            )
            db.commit()
        self._write_job_log(job_id, f"Job failed: {exc}")

    @staticmethod
    def _upsert_session(
        db: Any,
        session_id: str,
        input_path: str,
        artifact_dir: str | None = None,
        is_archived: bool = False,
        archived_at: datetime | None = None,
    ) -> None:
        """Project session state into SQL table for fast UI listing."""
        from data_extract.services.session_service import load_session_details

        input_dir = Path(input_path).resolve()
        probe_dirs = [
            input_dir if input_dir.is_dir() else input_dir.parent,
            (input_dir if input_dir.is_dir() else input_dir.parent).parent,
            Path.cwd(),
        ]

        details: dict[str, Any] | None = None
        for directory in probe_dirs:
            details = load_session_details(directory, session_id)
            if details:
                break

        if not details:
            return

        stats = details.get("statistics", {})
        updated_at_raw = details.get("updated_at")
        if not updated_at_raw:
            return
        updated_at = datetime.fromisoformat(updated_at_raw)

        record = db.get(SessionRecord, session_id)
        if record is None:
            record = SessionRecord(
                session_id=session_id,
                source_directory=details.get("source_directory", ""),
                status=details.get("status", "unknown"),
                total_files=stats.get("total_files", details.get("total_files", 0)),
                processed_count=stats.get("processed_count", 0),
                failed_count=stats.get("failed_count", 0),
                artifact_dir=artifact_dir,
                is_archived=1 if is_archived else 0,
                archived_at=archived_at,
                updated_at=updated_at,
            )
            db.add(record)
        else:
            record.source_directory = details.get("source_directory", "")
            record.status = details.get("status", "unknown")
            record.total_files = stats.get("total_files", details.get("total_files", 0))
            record.processed_count = stats.get("processed_count", 0)
            record.failed_count = stats.get("failed_count", 0)
            record.artifact_dir = artifact_dir
            record.is_archived = 1 if is_archived else 0
            record.archived_at = archived_at
            record.updated_at = updated_at

    @staticmethod
    def _job_dirs(job_id: str) -> dict[str, Path]:
        root = JOBS_HOME / job_id
        inputs = root / "inputs"
        outputs = root / "outputs"
        logs = root / "logs"
        for path in [root, inputs, outputs, logs]:
            path.mkdir(parents=True, exist_ok=True)
        return {"root": root, "inputs": inputs, "outputs": outputs, "logs": logs}

    def _write_job_artifact(self, job_id: str, payload: dict[str, Any]) -> None:
        """Persist canonical per-job artifact payload."""
        job_dirs = self._job_dirs(job_id)
        artifact_path = job_dirs["root"] / "result.json"
        artifact_path.write_text(json.dumps(payload, default=str, indent=2), encoding="utf-8")

    def _write_job_log(self, job_id: str, message: str) -> None:
        job_dirs = self._job_dirs(job_id)
        log_path = job_dirs["logs"] / "events.log"
        timestamp = datetime.utcnow().isoformat()
        with log_path.open("a", encoding="utf-8") as handle:
            handle.write(f"{timestamp} {message}\n")

    def _compute_request_hash(self, request: ProcessJobRequest) -> str | None:
        """Compute request hash for idempotency checks."""
        try:
            files, _source_dir = self.job_service._resolve_files(request)
        except Exception:
            return None
        request_hash = self.job_service._compute_request_hash(request, files)
        return cast(str | None, request_hash)

    def _recover_inflight_jobs(self) -> None:
        """Recover jobs stranded in queued/running after unclean shutdown."""
        recovered_requeued = 0
        recovered_failed = 0

        with SessionLocal() as db:
            stale_jobs = list(
                db.scalars(
                    select(Job)
                    .where(Job.status.in_(RUNNING_STATUSES))
                    .order_by(Job.created_at.asc())
                )
            )
            if not stale_jobs:
                self._recovery_stats = {"requeued": 0, "failed": 0}
                return

            for job in stale_jobs:
                if job.status == JobStatus.QUEUED.value:
                    request_payload = self._load_request_payload(job.request_payload)
                    if request_payload is None:
                        recovered_failed += self._mark_recovery_failed(
                            db,
                            job,
                            "Failed to recover queued job: invalid request payload",
                        )
                        continue

                    job.updated_at = datetime.utcnow()
                    db.add(
                        JobEvent(
                            job_id=job.id,
                            event_type="queued",
                            message="Recovered queued job after restart",
                            payload="{}",
                            event_time=datetime.utcnow(),
                        )
                    )
                    self.queue.submit(job.id, {"kind": "process", "request": request_payload})
                    self._write_job_log(job.id, "Recovered queued job after restart")
                    recovered_requeued += 1
                    continue

                recovered_failed += self._mark_recovery_failed(
                    db,
                    job,
                    "Recovered running job after restart; marked failed for consistency",
                )

            db.commit()

        self._recovery_stats = {"requeued": recovered_requeued, "failed": recovered_failed}

    @staticmethod
    def _load_request_payload(raw_payload: str | None) -> dict[str, Any] | None:
        if not raw_payload:
            return None
        try:
            payload = json.loads(raw_payload)
        except json.JSONDecodeError:
            return None
        if not isinstance(payload, dict):
            return None
        try:
            validated = ProcessJobRequest.model_validate(payload)
        except Exception:
            return None
        return validated.model_dump()

    def _mark_recovery_failed(self, db: Any, job: Job, message: str) -> int:
        job.status = JobStatus.FAILED.value
        job.finished_at = datetime.utcnow()
        job.updated_at = datetime.utcnow()
        job.result_payload = json.dumps(
            {
                "error": message,
                "recovered_at": datetime.utcnow().isoformat(),
            }
        )
        db.add(
            JobEvent(
                job_id=job.id,
                event_type="error",
                message=message,
                payload="{}",
                event_time=datetime.utcnow(),
            )
        )
        self._write_job_log(job.id, message)
        return 1

    @staticmethod
    def _resolve_worker_count() -> int:
        raw_value = os.environ.get("DATA_EXTRACT_API_WORKERS", "2").strip()
        try:
            return max(1, int(raw_value))
        except ValueError:
            return 2

    @staticmethod
    def _resolve_work_dir(input_path: str) -> Path:
        """Resolve session work dir from an input path."""
        resolved = Path(input_path).resolve()
        return resolved if resolved.is_dir() else resolved.parent


runtime = ApiRuntime()
