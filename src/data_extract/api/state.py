"""API runtime state: queue + service orchestration."""

from __future__ import annotations

import json
import os
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any, Dict, cast

from sqlalchemy import delete, select

from data_extract.api.database import (
    JOBS_HOME,
    SessionLocal,
    init_database,
    sqlite_lock_retry_stats,
    with_sqlite_lock_retry,
)
from data_extract.api.models import Job, JobEvent, JobFile, RetryRun, SessionRecord
from data_extract.contracts import JobStatus, ProcessJobRequest, RetryRequest
from data_extract.runtime import LocalJobQueue, QueueFullError
from data_extract.services import JobService, RetryService
from data_extract.services.pathing import normalized_path_text
from data_extract.services.persistence_repository import (
    RUNNING_STATUSES,
    TERMINAL_STATUSES,
    PersistenceRepository,
)


class QueueCapacityError(RuntimeError):
    """Raised when queue capacity is exhausted and request cannot be accepted."""

    def __init__(
        self,
        message: str,
        *,
        retry_after_seconds: int | None = None,
        reason: str = "queue_capacity",
    ) -> None:
        normalized = message.strip()
        if retry_after_seconds is not None and "retry after" not in normalized.lower():
            normalized = f"{normalized.rstrip('.')} Retry after ~{retry_after_seconds}s."
        super().__init__(normalized)
        self.retry_after_seconds = retry_after_seconds
        self.reason = reason


class ApiRuntime:
    """Owns queue lifecycle and background job handlers."""

    def __init__(self) -> None:
        self.job_service = JobService()
        self.persistence = PersistenceRepository()
        self._worker_count = self._resolve_worker_count()
        self._max_backlog = self._resolve_max_backlog()
        self._queue_high_watermark = self._resolve_queue_high_watermark()
        self._queue_retry_hint_seconds = self._resolve_queue_retry_hint_seconds()
        self.queue: LocalJobQueue = LocalJobQueue(
            self._handle_job,
            worker_count=self._worker_count,
            max_backlog=self._max_backlog,
            error_handler=self._handle_queue_error,
        )
        self._overload_stats_lock = Lock()
        self._overload_stats: dict[str, Any] = {
            "throttle_rejections": 0,
            "queue_full_rejections": 0,
            "last_reason": None,
            "last_rejected_at": None,
            "last_retry_after_seconds": None,
            "last_backlog": 0,
            "last_capacity": self._max_backlog,
            "last_utilization": 0.0,
        }
        self._recovery_stats = {"requeued": 0, "failed": 0}
        self._startup_stats_lock = Lock()
        self._terminal_reconciliation_stats: dict[str, Any] = {
            "scanned": 0,
            "repaired": 0,
            "failed": 0,
            "db_repairs": 0,
            "artifact_repairs": 0,
            "mismatch_repairs": 0,
            "last_run_at": None,
        }
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
        self._reconcile_terminal_artifacts()

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
        return int(self.queue.backlog)

    @property
    def queue_capacity(self) -> int:
        """Maximum in-memory queue capacity."""
        return int(self.queue.capacity)

    @property
    def queue_utilization(self) -> float:
        """Queue utilization ratio."""
        return float(self.queue.utilization)

    @property
    def alive_workers(self) -> int:
        """Number of currently alive worker threads."""
        return int(self.queue.alive_workers)

    @property
    def dead_workers(self) -> int:
        """Number of workers currently not alive."""
        return int(self.queue.dead_workers)

    @property
    def worker_restarts(self) -> int:
        """Number of worker restarts handled by watchdog."""
        return int(self.queue.worker_restarts)

    @property
    def db_lock_retry_stats(self) -> dict[str, Any]:
        """SQLite lock retry counters."""
        return cast(dict[str, Any], sqlite_lock_retry_stats())

    @property
    def recovery_stats(self) -> dict[str, int]:
        """Snapshot of last startup recovery actions."""
        return dict(self._recovery_stats)

    @property
    def overload_stats(self) -> dict[str, Any]:
        """Queue overload/throttle counters and latest snapshot."""
        with self._overload_stats_lock:
            snapshot = dict(self._overload_stats)
        snapshot["high_watermark"] = self._queue_high_watermark
        snapshot["retry_hint_seconds"] = self._queue_retry_hint_seconds
        snapshot["backlog"] = self.queue_backlog
        snapshot["capacity"] = self.queue_capacity
        snapshot["utilization"] = self.queue_utilization
        snapshot["throttled"] = self._is_queue_above_high_watermark()
        return snapshot

    @property
    def terminal_reconciliation_stats(self) -> dict[str, Any]:
        """Startup terminal payload/artifact reconciliation stats."""
        with self._startup_stats_lock:
            return dict(self._terminal_reconciliation_stats)

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
                resolved_job_id = str(existing_job_id)
                resolved_status = str(status)
                if resolved_status in TERMINAL_STATUSES or resolved_status in RUNNING_STATUSES:
                    return resolved_job_id

        self._raise_if_queue_throttled(reason="process")

        def _persist_queue_record() -> None:
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
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                )
                db.add(job)
                db.add(
                    JobEvent(
                        job_id=effective_job_id,
                        event_type="queued",
                        message="Job queued for processing",
                        payload="{}",
                        event_time=datetime.now(timezone.utc),
                    )
                )
                db.commit()

        with_sqlite_lock_retry(
            _persist_queue_record,
            operation_name="enqueue_process.persist_queue_record",
            serialize_writes=True,
        )

        self._write_job_log(effective_job_id, "Job queued for processing")
        try:
            self.queue.submit(
                effective_job_id, {"kind": "process", "request": normalized_request.model_dump()}
            )
        except QueueFullError as exc:
            self._discard_unaccepted_process_job(effective_job_id)
            retry_after_seconds = self._record_queue_rejection(reason="queue_full")
            raise QueueCapacityError(
                str(exc),
                retry_after_seconds=retry_after_seconds,
                reason="queue_full",
            ) from exc
        return effective_job_id

    def enqueue_retry(self, job_id: str, request: RetryRequest) -> None:
        """Submit retry action to worker for existing job id."""
        self._raise_if_queue_throttled(reason="retry")
        self._write_job_log(job_id, "Retry queued")
        try:
            self.queue.submit(job_id, {"kind": "retry", "request": request.model_dump()})
        except QueueFullError as exc:
            retry_after_seconds = self._record_queue_rejection(reason="queue_full")
            raise QueueCapacityError(
                str(exc),
                retry_after_seconds=retry_after_seconds,
                reason="queue_full",
            ) from exc

    def _handle_job(self, job_id: str, payload: Dict[str, Any]) -> None:
        """Worker callback for process/retry execution."""
        kind = payload.get("kind", "process")
        request_payload = payload.get("request", {})
        input_path = ""

        def _mark_running() -> str:
            with SessionLocal() as db:
                job = db.get(Job, job_id)
                if not job:
                    return ""

                input_path_value = job.input_path
                job.status = JobStatus.RUNNING.value
                job.started_at = datetime.now(timezone.utc)
                job.updated_at = datetime.now(timezone.utc)
                db.add(
                    JobEvent(
                        job_id=job_id,
                        event_type="running",
                        message="Job is running",
                        payload="{}",
                        event_time=datetime.now(timezone.utc),
                    )
                )
                db.commit()
                return str(input_path_value or "")

        input_path = with_sqlite_lock_retry(
            _mark_running,
            operation_name="worker.mark_running",
            serialize_writes=True,
        )
        if not input_path:
            return
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
        raw_status = result.get("status", JobStatus.FAILED.value)
        status = raw_status.value if isinstance(raw_status, JobStatus) else str(raw_status)
        # Artifact durability must succeed before terminal DB commit.
        self._write_job_artifact(job_id, result)

        def _persist_terminal_state() -> None:
            with SessionLocal() as db:
                job = db.get(Job, job_id)
                if not job:
                    return

                job.status = status
                job.result_payload = json.dumps(result, default=str)
                job.output_dir = result.get("output_dir", job.output_dir)
                job.request_hash = result.get("request_hash", job.request_hash)
                job.artifact_dir = result.get("artifact_dir", job.artifact_dir)
                job.session_id = result.get("session_id")
                job.finished_at = datetime.now(timezone.utc)
                job.updated_at = datetime.now(timezone.utc)

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
                            datetime.now(timezone.utc)
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
                            requested_at=datetime.now(timezone.utc),
                        )
                    )

                db.add(
                    JobEvent(
                        job_id=job_id,
                        event_type="finished",
                        message=f"Job finished with status={status}",
                        payload="{}",
                        event_time=datetime.now(timezone.utc),
                    )
                )

                db.commit()

        with_sqlite_lock_retry(
            _persist_terminal_state,
            operation_name="worker.persist_terminal_state",
            serialize_writes=True,
        )
        self._write_job_log(job_id, f"Job finished with status={status}")

    def _persist_exception(self, job_id: str, exc: Exception) -> None:
        """Persist worker exception as terminal failed state."""

        def _persist_error() -> None:
            with SessionLocal() as db:
                job = db.get(Job, job_id)
                if not job:
                    return

                job.status = JobStatus.FAILED.value
                job.result_payload = json.dumps({"error": str(exc)})
                job.finished_at = datetime.now(timezone.utc)
                job.updated_at = datetime.now(timezone.utc)
                db.add(
                    JobEvent(
                        job_id=job_id,
                        event_type="error",
                        message=str(exc),
                        payload="{}",
                        event_time=datetime.now(timezone.utc),
                    )
                )
                db.commit()

        with_sqlite_lock_retry(
            _persist_error,
            operation_name="worker.persist_exception",
            serialize_writes=True,
        )
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

    @staticmethod
    def _resolve_artifact_root(job_id: str, artifact_dir: str | None = None) -> Path:
        if artifact_dir:
            root = Path(artifact_dir).expanduser()
            if not root.is_absolute():
                root = JOBS_HOME / root
            return root.resolve()
        return cast(Path, (JOBS_HOME / job_id).resolve())

    @staticmethod
    def _read_json_object_from_path(path: Path) -> tuple[dict[str, Any] | None, str | None]:
        if not path.exists():
            return None, "missing"
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            return None, f"invalid_json:{exc}"
        if not isinstance(payload, dict):
            return None, "not_object"
        return payload, None

    @staticmethod
    def _load_json_object(raw_payload: str | None) -> tuple[dict[str, Any] | None, str | None]:
        if raw_payload is None:
            return None, "missing"
        text = raw_payload.strip()
        if not text:
            return None, "missing"
        try:
            payload = json.loads(text)
        except Exception as exc:
            return None, f"invalid_json:{exc}"
        if not isinstance(payload, dict):
            return None, "not_object"
        return payload, None

    def _write_job_artifact(
        self,
        job_id: str,
        payload: dict[str, Any],
        artifact_dir: str | None = None,
    ) -> None:
        """Persist canonical per-job artifact payload."""
        artifact_root = self._resolve_artifact_root(job_id, artifact_dir=artifact_dir)
        artifact_root.mkdir(parents=True, exist_ok=True)
        artifact_path = artifact_root / "result.json"
        temp_path = artifact_path.with_suffix(".tmp")
        try:
            with temp_path.open("w", encoding="utf-8") as handle:
                json.dump(payload, handle, default=str, indent=2)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_path, artifact_path)
        finally:
            if temp_path.exists():
                temp_path.unlink(missing_ok=True)

    def _write_job_log(self, job_id: str, message: str) -> None:
        job_dirs = self._job_dirs(job_id)
        log_path = job_dirs["logs"] / "events.log"
        timestamp = datetime.now(timezone.utc).isoformat()
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

        def _stage_recovery() -> tuple[int, list[tuple[str, dict[str, Any], str]]]:
            recovered_failed = 0
            staged_submissions: list[tuple[str, dict[str, Any], str]] = []
            with SessionLocal() as db:
                stale_jobs = list(
                    db.scalars(
                        select(Job)
                        .where(Job.status.in_(RUNNING_STATUSES))
                        .order_by(Job.created_at.asc())
                    )
                )
                if not stale_jobs:
                    return 0, []

                for job in stale_jobs:
                    request_payload = self._load_request_payload(job.request_payload)
                    if request_payload is None:
                        recovered_failed += self._mark_recovery_failed(
                            db,
                            job,
                            "Failed to recover job after restart: invalid request payload",
                        )
                        continue

                    was_running = job.status == JobStatus.RUNNING.value
                    if was_running:
                        request_payload["resume"] = True
                        request_payload["force"] = False
                        if job.session_id:
                            request_payload["resume_session"] = job.session_id

                    job.status = JobStatus.QUEUED.value
                    job.started_at = None
                    job.finished_at = None
                    job.updated_at = datetime.now(timezone.utc)
                    message = (
                        "Recovered running job after restart; requeued with resume"
                        if was_running
                        else "Recovered queued job after restart"
                    )

                    db.add(
                        JobEvent(
                            job_id=job.id,
                            event_type="queued",
                            message=message,
                            payload="{}",
                            event_time=datetime.now(timezone.utc),
                        )
                    )
                    staged_submissions.append(
                        (
                            job.id,
                            {"kind": "process", "request": request_payload},
                            message,
                        )
                    )

                db.commit()
            return recovered_failed, staged_submissions

        recovered_failed, staged_submissions = with_sqlite_lock_retry(
            _stage_recovery,
            operation_name="startup.recover_inflight.stage",
            serialize_writes=True,
        )
        recovered_requeued = 0
        for job_id, payload, message in staged_submissions:
            try:
                self.queue.submit(job_id, payload)
            except QueueFullError:
                recovered_failed += self._mark_recovery_submission_failed(
                    job_id,
                    "Failed to recover job after restart: queue at capacity",
                )
                continue
            self._write_job_log(job_id, message)
            recovered_requeued += 1

        self._recovery_stats = {"requeued": recovered_requeued, "failed": recovered_failed}

    def _reconcile_terminal_artifacts(self) -> None:
        """Reconcile terminal job result_payload rows against result.json artifacts."""

        def _load_terminal_job_ids() -> list[str]:
            with SessionLocal() as db:
                return list(
                    db.scalars(
                        select(Job.id)
                        .where(Job.status.in_(TERMINAL_STATUSES))
                        .order_by(Job.created_at.asc())
                    )
                )

        job_ids = with_sqlite_lock_retry(
            _load_terminal_job_ids,
            operation_name="startup.reconcile_terminal.list",
            serialize_writes=False,
        )
        stats: dict[str, Any] = {
            "scanned": 0,
            "repaired": 0,
            "failed": 0,
            "db_repairs": 0,
            "artifact_repairs": 0,
            "mismatch_repairs": 0,
            "last_run_at": datetime.now(timezone.utc).isoformat(),
        }
        for job_id in job_ids:
            stats["scanned"] += 1
            try:
                outcome = self._reconcile_terminal_artifact_for_job(job_id)
            except Exception as exc:
                stats["failed"] += 1
                self._write_job_log(
                    job_id,
                    f"Startup reconciliation failed with exception: {exc}",
                )
                continue
            if outcome == "repair_db":
                stats["repaired"] += 1
                stats["db_repairs"] += 1
            elif outcome == "repair_artifact":
                stats["repaired"] += 1
                stats["artifact_repairs"] += 1
            elif outcome == "repair_mismatch":
                stats["repaired"] += 1
                stats["db_repairs"] += 1
                stats["mismatch_repairs"] += 1
            elif outcome == "failed":
                stats["failed"] += 1
        with self._startup_stats_lock:
            self._terminal_reconciliation_stats = stats

    def _reconcile_terminal_artifact_for_job(self, job_id: str) -> str:
        """Reconcile a single terminal job row and artifact, returning outcome key."""

        def _load_snapshot() -> tuple[str | None, str | None] | None:
            with SessionLocal() as db:
                job = db.get(Job, job_id)
                if job is None or job.status not in TERMINAL_STATUSES:
                    return None
                return job.result_payload, job.artifact_dir

        snapshot = with_sqlite_lock_retry(
            _load_snapshot,
            operation_name="startup.reconcile_terminal.snapshot",
            serialize_writes=False,
        )
        if snapshot is None:
            return "noop"
        raw_result_payload, artifact_dir = snapshot
        db_payload, db_error = self._load_json_object(raw_result_payload)
        artifact_path = (
            self._resolve_artifact_root(job_id, artifact_dir=artifact_dir) / "result.json"
        )
        artifact_payload, artifact_error = self._read_json_object_from_path(artifact_path)

        if db_payload is not None and artifact_payload is not None:
            if self._canonical_payload(db_payload) == self._canonical_payload(artifact_payload):
                return "noop"
            self._record_terminal_repair_event(
                job_id,
                message="Startup reconciliation repaired result_payload from artifact mismatch",
                payload={
                    "phase": "startup_terminal_reconciliation",
                    "repair": "db_from_artifact_mismatch",
                },
                repaired_payload=artifact_payload,
            )
            self._write_job_log(
                job_id,
                "Startup reconciliation repaired result_payload from artifact mismatch",
            )
            return "repair_mismatch"

        if db_payload is not None and artifact_payload is None:
            try:
                self._write_job_artifact(job_id, db_payload, artifact_dir=artifact_dir)
            except Exception as exc:
                self._record_terminal_failure_event(
                    job_id,
                    message="Startup reconciliation failed to repair result.json from result_payload",
                    payload={
                        "phase": "startup_terminal_reconciliation",
                        "failure": "artifact_write_failed",
                        "artifact_error": artifact_error,
                        "exception": str(exc),
                    },
                )
                self._write_job_log(
                    job_id,
                    "Startup reconciliation failed to repair result.json from result_payload",
                )
                return "failed"
            self._record_terminal_repair_event(
                job_id,
                message="Startup reconciliation repaired missing result.json from result_payload",
                payload={
                    "phase": "startup_terminal_reconciliation",
                    "repair": "artifact_from_db",
                    "artifact_error": artifact_error,
                },
            )
            self._write_job_log(
                job_id,
                "Startup reconciliation repaired missing result.json from result_payload",
            )
            return "repair_artifact"

        if db_payload is None and artifact_payload is not None:
            self._record_terminal_repair_event(
                job_id,
                message="Startup reconciliation repaired result_payload from result.json",
                payload={
                    "phase": "startup_terminal_reconciliation",
                    "repair": "db_from_artifact",
                    "result_payload_error": db_error,
                },
                repaired_payload=artifact_payload,
            )
            self._write_job_log(
                job_id,
                "Startup reconciliation repaired result_payload from result.json",
            )
            return "repair_db"

        self._record_terminal_failure_event(
            job_id,
            message="Startup reconciliation failed: no valid terminal result payload/artifact",
            payload={
                "phase": "startup_terminal_reconciliation",
                "failure": "both_missing_or_invalid",
                "result_payload_error": db_error,
                "artifact_error": artifact_error,
            },
        )
        self._write_job_log(
            job_id,
            "Startup reconciliation failed: no valid terminal result payload/artifact",
        )
        return "failed"

    def _handle_queue_error(self, job_id: str, payload: dict[str, Any], exc: Exception) -> None:
        """Persist uncaught queue worker failures as terminal errors."""
        kind = payload.get("kind", "process")
        wrapped = RuntimeError(f"Queue worker {kind} handler failure: {exc}")
        self._persist_exception(job_id, wrapped)

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
        return cast(dict[str, Any], validated.model_dump())

    @staticmethod
    def _canonical_payload(payload: dict[str, Any]) -> str:
        return json.dumps(payload, default=str, sort_keys=True, separators=(",", ":"))

    def _record_terminal_repair_event(
        self,
        job_id: str,
        *,
        message: str,
        payload: dict[str, Any],
        repaired_payload: dict[str, Any] | None = None,
    ) -> None:
        def _persist() -> None:
            with SessionLocal() as db:
                job = db.get(Job, job_id)
                if job is None:
                    return
                if repaired_payload is not None:
                    job.result_payload = json.dumps(repaired_payload, default=str)
                    job.updated_at = datetime.now(timezone.utc)
                db.add(
                    JobEvent(
                        job_id=job_id,
                        event_type="repair",
                        message=message,
                        payload=json.dumps(payload, default=str),
                        event_time=datetime.now(timezone.utc),
                    )
                )
                db.commit()

        with_sqlite_lock_retry(
            _persist,
            operation_name="startup.reconcile_terminal.repair_event",
            serialize_writes=True,
        )

    def _record_terminal_failure_event(
        self,
        job_id: str,
        *,
        message: str,
        payload: dict[str, Any],
    ) -> None:
        def _persist() -> None:
            with SessionLocal() as db:
                job = db.get(Job, job_id)
                if job is None:
                    return
                db.add(
                    JobEvent(
                        job_id=job_id,
                        event_type="error",
                        message=message,
                        payload=json.dumps(payload, default=str),
                        event_time=datetime.now(timezone.utc),
                    )
                )
                db.commit()

        with_sqlite_lock_retry(
            _persist,
            operation_name="startup.reconcile_terminal.failure_event",
            serialize_writes=True,
        )

    def _mark_recovery_failed(self, db: Any, job: Job, message: str) -> int:
        job.status = JobStatus.FAILED.value
        job.finished_at = datetime.now(timezone.utc)
        job.updated_at = datetime.now(timezone.utc)
        job.result_payload = json.dumps(
            {
                "error": message,
                "recovered_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        db.add(
            JobEvent(
                job_id=job.id,
                event_type="error",
                message=message,
                payload="{}",
                event_time=datetime.now(timezone.utc),
            )
        )
        self._write_job_log(job.id, message)
        return 1

    def _mark_recovery_submission_failed(self, job_id: str, message: str) -> int:
        """Persist recovery failure when queue submit is rejected after staging."""

        def _persist() -> int:
            with SessionLocal() as db:
                job = db.get(Job, job_id)
                if not job:
                    return 0
                job.status = JobStatus.FAILED.value
                job.finished_at = datetime.now(timezone.utc)
                job.updated_at = datetime.now(timezone.utc)
                job.result_payload = json.dumps(
                    {
                        "error": message,
                        "recovered_at": datetime.now(timezone.utc).isoformat(),
                    }
                )
                db.add(
                    JobEvent(
                        job_id=job_id,
                        event_type="error",
                        message=message,
                        payload="{}",
                        event_time=datetime.now(timezone.utc),
                    )
                )
                db.commit()
                return 1

        failed_count = cast(
            int,
            with_sqlite_lock_retry(
                _persist,
                operation_name="startup.recover_inflight.persist_submission_failure",
                serialize_writes=True,
            ),
        )
        if failed_count:
            self._write_job_log(job_id, message)
        return failed_count

    def _discard_unaccepted_process_job(self, job_id: str) -> None:
        """Remove queued DB/filesystem artifacts when submission was never accepted."""

        def _discard() -> None:
            with SessionLocal() as db:
                job = db.get(Job, job_id)
                if job is None:
                    return
                db.execute(delete(JobFile).where(JobFile.job_id == job_id))
                db.execute(delete(JobEvent).where(JobEvent.job_id == job_id))
                db.delete(job)
                db.commit()

        with_sqlite_lock_retry(
            _discard,
            operation_name="enqueue_process.discard_unaccepted",
            serialize_writes=True,
        )
        shutil.rmtree(JOBS_HOME / job_id, ignore_errors=True)

    def _raise_if_queue_throttled(self, reason: str) -> None:
        if not self._is_queue_above_high_watermark():
            return
        retry_after_seconds = self._record_queue_rejection(reason="high_watermark")
        raise QueueCapacityError(
            (
                "Queue backlog is above throttle watermark "
                f"({self.queue_backlog}/{self.queue_capacity}, "
                f"utilization={self.queue_utilization:.2f}, "
                f"watermark={self._queue_high_watermark:.2f}); try again later."
            ),
            retry_after_seconds=retry_after_seconds,
            reason=reason,
        )

    def _is_queue_above_high_watermark(self) -> bool:
        if self.queue_capacity <= 0:
            return False
        return self.queue_utilization >= self._queue_high_watermark

    def _record_queue_rejection(self, reason: str) -> int:
        retry_after_seconds = self._estimate_retry_after_seconds()
        now = datetime.now(timezone.utc).isoformat()
        with self._overload_stats_lock:
            if reason == "queue_full":
                self._overload_stats["queue_full_rejections"] += 1
            else:
                self._overload_stats["throttle_rejections"] += 1
            self._overload_stats["last_reason"] = reason
            self._overload_stats["last_rejected_at"] = now
            self._overload_stats["last_retry_after_seconds"] = retry_after_seconds
            self._overload_stats["last_backlog"] = self.queue_backlog
            self._overload_stats["last_capacity"] = self.queue_capacity
            self._overload_stats["last_utilization"] = self.queue_utilization
        return retry_after_seconds

    def _estimate_retry_after_seconds(self) -> int:
        workers = max(1, self.worker_count)
        backlog = max(1, self.queue_backlog)
        estimated = (backlog // workers) + 1
        return max(self._queue_retry_hint_seconds, min(estimated, 60))

    @staticmethod
    def _resolve_worker_count() -> int:
        raw_value = os.environ.get("DATA_EXTRACT_API_WORKERS", "2").strip()
        try:
            return max(1, int(raw_value))
        except ValueError:
            return 2

    @staticmethod
    def _resolve_max_backlog() -> int:
        raw_value = os.environ.get("DATA_EXTRACT_API_QUEUE_MAX_BACKLOG", "1000").strip()
        try:
            return max(1, int(raw_value))
        except ValueError:
            return 1000

    @staticmethod
    def _resolve_queue_high_watermark() -> float:
        raw_value = os.environ.get("DATA_EXTRACT_API_QUEUE_HIGH_WATERMARK", "0.9").strip()
        try:
            value = float(raw_value)
        except ValueError:
            return 0.9
        if value <= 0.0:
            return 0.9
        return min(1.0, max(0.1, value))

    @staticmethod
    def _resolve_queue_retry_hint_seconds() -> int:
        raw_value = os.environ.get("DATA_EXTRACT_API_QUEUE_RETRY_HINT_SECONDS", "2").strip()
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
