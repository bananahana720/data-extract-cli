"""API runtime state: queue + service orchestration."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from threading import Event, Lock, Thread
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


DISPATCH_STATE_PENDING = "pending_dispatch"
DISPATCH_STATE_PENDING_LEGACY = "pending"
DISPATCH_STATE_DISPATCHING = "dispatching"
DISPATCH_STATE_SUBMITTED = "submitted"
DISPATCH_STATE_RUNNING = "running"
DISPATCH_STATE_DONE = "done"

ARTIFACT_SYNC_PENDING = "pending"
ARTIFACT_SYNC_SYNCED = "synced"
ARTIFACT_SYNC_FAILED = "failed"


class ApiRuntime:
    """Owns queue lifecycle and background job handlers."""

    def __init__(self) -> None:
        self.job_service = JobService()
        self.persistence = PersistenceRepository()
        self._worker_count = self._resolve_worker_count()
        self._max_backlog = self._resolve_max_backlog()
        self._queue_high_watermark = self._resolve_queue_high_watermark()
        self._queue_retry_hint_seconds = self._resolve_queue_retry_hint_seconds()
        self._disk_pressure_threshold = self._resolve_disk_pressure_threshold()
        self._storage_stats_lock = Lock()
        self._storage_stats: dict[str, Any] = {
            "disk_pressure_rejections": 0,
            "threshold": self._disk_pressure_threshold,
            "last_total_bytes": 0,
            "last_free_bytes": 0,
            "last_used_ratio": 0.0,
            "last_checked_at": None,
            "last_error": None,
        }
        self.queue: LocalJobQueue = LocalJobQueue(
            self._handle_job,
            worker_count=self._worker_count,
            max_backlog=self._max_backlog,
            error_handler=self._handle_queue_error,
        )
        self._dispatch_poll_interval_seconds = self._resolve_dispatch_poll_interval_seconds()
        self._dispatch_batch_size = self._resolve_dispatch_batch_size()
        self._artifact_sync_interval_seconds = self._resolve_artifact_sync_interval_seconds()
        self._last_artifact_sync_at = 0.0
        self._dispatcher_stop = Event()
        self._dispatcher_thread: Thread | None = None
        self._overload_stats_lock = Lock()
        self._overload_stats: dict[str, Any] = {
            "throttle_rejections": 0,
            "queue_full_rejections": 0,
            "disk_pressure_rejections": 0,
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
        self._runtime_counters_lock = Lock()
        self._runtime_counters: dict[str, int] = {
            "pending_dispatch_count": 0,
            "artifact_sync_backlog_count": 0,
            "session_projection_drift_count": 0,
        }

    def start(self) -> None:
        """Initialize schema and start background worker."""
        init_database()
        self.queue.start()
        self._recover_inflight_jobs()
        self._reconcile_terminal_artifacts()
        self._reconcile_session_projections()
        self._dispatcher_stop.clear()
        self._start_dispatcher_loop()
        self._dispatch_pending_jobs_once(source="startup_bootstrap")
        self._refresh_runtime_counters()

    def stop(self) -> None:
        """Stop background worker."""
        self._stop_dispatcher_loop()
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
        return sqlite_lock_retry_stats()

    @property
    def recovery_stats(self) -> dict[str, int]:
        """Snapshot of last startup recovery actions."""
        return dict(self._recovery_stats)

    @property
    def overload_stats(self) -> dict[str, Any]:
        """Queue overload/throttle counters and latest snapshot."""
        with self._overload_stats_lock:
            snapshot = dict(self._overload_stats)
        snapshot["disk_pressure_threshold"] = self._disk_pressure_threshold
        snapshot["storage_stats"] = self.storage_stats
        snapshot["high_watermark"] = self._queue_high_watermark
        snapshot["retry_hint_seconds"] = self._queue_retry_hint_seconds
        snapshot["backlog"] = self.queue_backlog
        snapshot["capacity"] = self.queue_capacity
        snapshot["utilization"] = self.queue_utilization
        snapshot["throttled"] = self._is_queue_above_high_watermark()
        return snapshot

    @property
    def storage_stats(self) -> dict[str, Any]:
        """Snapshot of the latest storage usage measurements."""
        with self._storage_stats_lock:
            return dict(self._storage_stats)

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

    @property
    def pending_dispatch_count(self) -> int:
        """Count of queued jobs waiting for queue submission."""
        with self._runtime_counters_lock:
            return int(self._runtime_counters["pending_dispatch_count"])

    @property
    def artifact_sync_backlog_count(self) -> int:
        """Count of terminal jobs with unsynced artifacts."""
        with self._runtime_counters_lock:
            return int(self._runtime_counters["artifact_sync_backlog_count"])

    @property
    def session_projection_drift_count(self) -> int:
        """Count of session records diverging from canonical job payloads."""
        with self._runtime_counters_lock:
            return int(self._runtime_counters["session_projection_drift_count"])

    @property
    def runtime_counters(self) -> dict[str, int]:
        """Health-consumable runtime counters."""
        with self._runtime_counters_lock:
            return dict(self._runtime_counters)

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

        self._assert_storage_available()
        self._raise_if_queue_throttled(reason="process")
        dispatch_payload = {"kind": "process", "request": normalized_request.model_dump()}

        def _persist_queue_record() -> None:
            with SessionLocal() as db:
                now = datetime.now(timezone.utc)
                job = Job(
                    id=effective_job_id,
                    status=JobStatus.QUEUED.value,
                    input_path=normalized_request.input_path,
                    output_dir=normalized_request.output_path or "",
                    requested_format=normalized_request.output_format,
                    chunk_size=normalized_request.chunk_size,
                    request_payload=json.dumps(normalized_request.model_dump(), default=str),
                    dispatch_payload=json.dumps(dispatch_payload, default=str),
                    request_hash=request_hash,
                    idempotency_key=normalized_request.idempotency_key,
                    attempt=1,
                    dispatch_state=DISPATCH_STATE_PENDING,
                    dispatch_attempts=0,
                    dispatch_last_error=None,
                    dispatch_last_attempt_at=None,
                    dispatch_next_attempt_at=now,
                    artifact_dir=str(job_dirs["root"]),
                    created_at=now,
                    updated_at=now,
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
        self._submit_or_defer_dispatch(effective_job_id, dispatch_payload, source="process_enqueue")
        self._refresh_runtime_counters()
        return effective_job_id

    def enqueue_retry(self, job_id: str, request: RetryRequest) -> None:
        """Submit retry action to worker for existing job id."""
        self._assert_storage_available()
        self._raise_if_queue_throttled(reason="retry")
        dispatch_payload = {"kind": "retry", "request": request.model_dump()}

        def _persist_retry_intent() -> bool:
            with SessionLocal() as db:
                job = db.get(Job, job_id)
                if job is None:
                    return False

                now = datetime.now(timezone.utc)
                should_add_queued_event = job.status != JobStatus.QUEUED.value
                job.status = JobStatus.QUEUED.value
                job.started_at = None
                job.finished_at = None
                job.dispatch_payload = json.dumps(dispatch_payload, default=str)
                job.dispatch_state = DISPATCH_STATE_PENDING
                job.dispatch_last_error = None
                job.dispatch_next_attempt_at = now
                job.updated_at = now
                if should_add_queued_event:
                    db.add(
                        JobEvent(
                            job_id=job_id,
                            event_type="queued",
                            message="Retry queued",
                            payload="{}",
                            event_time=now,
                        )
                    )
                db.commit()
                return True

        persisted = with_sqlite_lock_retry(
            _persist_retry_intent,
            operation_name="enqueue_retry.persist_queue_intent",
            serialize_writes=True,
        )
        if not persisted:
            raise ValueError(f"Job not found for retry dispatch: {job_id}")

        self._write_job_log(job_id, "Retry queued")
        self._submit_or_defer_dispatch(job_id, dispatch_payload, source="retry_enqueue")
        self._refresh_runtime_counters()

    def _start_dispatcher_loop(self) -> None:
        if self._dispatcher_thread is not None and self._dispatcher_thread.is_alive():
            return
        self._dispatcher_thread = Thread(
            target=self._dispatch_loop,
            name="data-extract-dispatcher",
            daemon=True,
        )
        self._dispatcher_thread.start()

    def _stop_dispatcher_loop(self) -> None:
        self._dispatcher_stop.set()
        if self._dispatcher_thread is not None and self._dispatcher_thread.is_alive():
            self._dispatcher_thread.join(timeout=2)
        self._dispatcher_thread = None

    def _dispatch_loop(self) -> None:
        while not self._dispatcher_stop.is_set():
            try:
                self._dispatch_pending_jobs_once(source="background_dispatch")
                self._maybe_sync_pending_artifacts()
            except Exception:
                pass
            self._dispatcher_stop.wait(self._dispatch_poll_interval_seconds)

    def _dispatch_pending_jobs_once(self, source: str) -> int:
        capacity_remaining = max(0, self.queue_capacity - self.queue_backlog)
        if capacity_remaining <= 0:
            self._refresh_runtime_counters()
            return 0

        dispatch_budget = min(capacity_remaining, self._dispatch_batch_size)
        pending_job_ids = self._load_pending_dispatch_job_ids(limit=dispatch_budget)
        submitted = 0
        for pending_job_id in pending_job_ids:
            payload = self._load_dispatch_payload_for_job(pending_job_id)
            if payload is None:
                self._mark_dispatch_pending(
                    pending_job_id,
                    error="Dispatch payload missing; awaiting next retry",
                )
                continue
            if self._submit_or_defer_dispatch(pending_job_id, payload, source=source):
                submitted += 1
            if self.queue_backlog >= self.queue_capacity:
                break

        self._refresh_runtime_counters()
        return submitted

    def _maybe_sync_pending_artifacts(self) -> None:
        now_monotonic = time.monotonic()
        if (now_monotonic - self._last_artifact_sync_at) < self._artifact_sync_interval_seconds:
            return
        self._last_artifact_sync_at = now_monotonic
        self._sync_pending_artifacts_once(source="background_artifact_sync")

    def _sync_pending_artifacts_once(self, source: str, limit: int | None = None) -> int:
        batch_limit = max(1, int(limit if limit is not None else self._dispatch_batch_size))

        def _load_unsynced_terminal_job_ids() -> list[str]:
            with SessionLocal() as db:
                return list(
                    db.scalars(
                        select(Job.id)
                        .where(
                            Job.status.in_(TERMINAL_STATUSES),
                            (Job.artifact_sync_state.is_(None))
                            | (Job.artifact_sync_state != ARTIFACT_SYNC_SYNCED),
                        )
                        .order_by(Job.updated_at.asc(), Job.created_at.asc())
                        .limit(batch_limit)
                    )
                )

        job_ids = with_sqlite_lock_retry(
            _load_unsynced_terminal_job_ids,
            operation_name=f"{source}.list_unsynced_terminal_jobs",
            serialize_writes=False,
        )
        repaired = 0
        for job_id in job_ids:
            try:
                outcome = self._reconcile_terminal_artifact_for_job(job_id)
            except Exception as exc:
                self._write_job_log(job_id, f"Background artifact sync failed: {exc}")
                continue
            if outcome in {"repair_artifact", "repair_mismatch"}:
                repaired += 1
        if job_ids:
            self._refresh_runtime_counters()
        return repaired

    def _load_pending_dispatch_job_ids(self, limit: int) -> list[str]:
        if limit <= 0:
            return []
        now = datetime.now(timezone.utc)

        def _load() -> list[str]:
            with SessionLocal() as db:
                return list(
                    db.scalars(
                        select(Job.id)
                        .where(
                            Job.status == JobStatus.QUEUED.value,
                            (Job.dispatch_state.is_(None))
                            | (
                                Job.dispatch_state.in_(
                                    [
                                        DISPATCH_STATE_PENDING,
                                        DISPATCH_STATE_PENDING_LEGACY,
                                        DISPATCH_STATE_DISPATCHING,
                                    ]
                                )
                            ),
                            (Job.dispatch_next_attempt_at.is_(None))
                            | (Job.dispatch_next_attempt_at <= now),
                        )
                        .order_by(Job.updated_at.asc())
                        .limit(limit)
                    )
                )

        return with_sqlite_lock_retry(
            _load,
            operation_name="dispatch.load_pending_job_ids",
            serialize_writes=False,
        )

    def _load_dispatch_payload_for_job(self, job_id: str) -> dict[str, Any] | None:
        def _load() -> tuple[str | None, str | None, str | None]:
            with SessionLocal() as db:
                job = db.get(Job, job_id)
                if job is None:
                    return None, None, None
                return job.dispatch_payload, job.request_payload, job.session_id

        raw_dispatch_payload, raw_request_payload, session_id = with_sqlite_lock_retry(
            _load,
            operation_name="dispatch.load_payload",
            serialize_writes=False,
        )
        payload = self._load_dispatch_payload(raw_dispatch_payload)
        if payload is not None:
            return payload

        request_payload = self._load_request_payload(raw_request_payload)
        if request_payload is not None:
            return {"kind": "process", "request": request_payload}
        if session_id:
            retry_payload = RetryRequest(
                session=str(session_id),
                last=False,
                non_interactive=True,
            ).model_dump()
            return {"kind": "retry", "request": retry_payload}
        return None

    def _submit_or_defer_dispatch(
        self,
        job_id: str,
        payload: dict[str, Any],
        *,
        source: str,
    ) -> bool:
        claimed = self._claim_dispatch_for_submit(job_id, payload)
        if not claimed:
            return False
        try:
            self.queue.submit(job_id, payload)
        except QueueFullError as exc:
            self._record_queue_rejection(reason="queue_full")
            self._mark_dispatch_pending(job_id, error=str(exc))
            self._write_job_log(job_id, "Dispatch deferred; queue at capacity")
            return False

        self._mark_dispatch_submitted(job_id, source=source)
        return True

    def _claim_dispatch_for_submit(self, job_id: str, payload: dict[str, Any]) -> bool:
        def _claim() -> bool:
            with SessionLocal() as db:
                job = db.get(Job, job_id)
                if job is None:
                    return False
                if job.status != JobStatus.QUEUED.value:
                    if job.status in TERMINAL_STATUSES:
                        job.dispatch_state = DISPATCH_STATE_DONE
                        job.updated_at = datetime.now(timezone.utc)
                        db.commit()
                    return False
                if job.dispatch_state not in {
                    DISPATCH_STATE_PENDING,
                    DISPATCH_STATE_PENDING_LEGACY,
                    DISPATCH_STATE_DISPATCHING,
                    None,
                }:
                    return False

                now = datetime.now(timezone.utc)
                job.dispatch_payload = json.dumps(payload, default=str)
                job.dispatch_state = DISPATCH_STATE_DISPATCHING
                job.dispatch_attempts = int(job.dispatch_attempts or 0) + 1
                job.dispatch_last_attempt_at = now
                job.dispatch_last_error = None
                job.dispatch_next_attempt_at = None
                job.updated_at = now
                db.commit()
                return True

        return with_sqlite_lock_retry(
            _claim,
            operation_name="dispatch.claim_for_submit",
            serialize_writes=True,
        )

    def _mark_dispatch_submitted(self, job_id: str, *, source: str) -> None:
        def _mark() -> None:
            with SessionLocal() as db:
                job = db.get(Job, job_id)
                if job is None:
                    return
                now = datetime.now(timezone.utc)
                if job.status == JobStatus.RUNNING.value:
                    job.dispatch_state = DISPATCH_STATE_RUNNING
                elif job.status in TERMINAL_STATUSES:
                    job.dispatch_state = DISPATCH_STATE_DONE
                elif job.status == JobStatus.QUEUED.value:
                    job.dispatch_state = DISPATCH_STATE_SUBMITTED
                    db.add(
                        JobEvent(
                            job_id=job_id,
                            event_type="dispatch",
                            message="Job submitted to in-memory worker queue",
                            payload=json.dumps({"source": source}),
                            event_time=now,
                        )
                    )
                job.dispatch_last_error = None
                job.dispatch_next_attempt_at = None
                job.updated_at = now
                db.commit()

        with_sqlite_lock_retry(
            _mark,
            operation_name="dispatch.mark_submitted",
            serialize_writes=True,
        )

    def _mark_dispatch_pending(self, job_id: str, *, error: str | None) -> None:
        def _mark() -> None:
            with SessionLocal() as db:
                job = db.get(Job, job_id)
                if job is None:
                    return
                if job.status in TERMINAL_STATUSES:
                    job.dispatch_state = DISPATCH_STATE_DONE
                    job.updated_at = datetime.now(timezone.utc)
                    db.commit()
                    return
                now = datetime.now(timezone.utc)
                job.dispatch_state = DISPATCH_STATE_PENDING
                job.dispatch_last_error = error
                job.dispatch_last_attempt_at = now
                job.dispatch_next_attempt_at = now + timedelta(
                    seconds=self._queue_retry_hint_seconds
                )
                job.updated_at = now
                db.commit()

        with_sqlite_lock_retry(
            _mark,
            operation_name="dispatch.mark_pending",
            serialize_writes=True,
        )

    def _load_dispatch_payload(self, raw_payload: str | None) -> dict[str, Any] | None:
        if not raw_payload:
            return None
        try:
            payload = json.loads(raw_payload)
        except Exception:
            return None
        if not isinstance(payload, dict):
            return None
        kind = payload.get("kind")
        request_payload = payload.get("request")
        if kind not in {"process", "retry"}:
            return None
        if not isinstance(request_payload, dict):
            return None
        return {"kind": str(kind), "request": request_payload}

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
                if job.status != JobStatus.QUEUED.value:
                    return ""

                input_path_value = job.input_path
                job.status = JobStatus.RUNNING.value
                job.dispatch_state = DISPATCH_STATE_RUNNING
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
        checksum = self._payload_checksum(result)

        def _persist_terminal_state() -> str | None:
            with SessionLocal() as db:
                job = db.get(Job, job_id)
                if not job:
                    return None

                now = datetime.now(timezone.utc)
                job.status = status
                job.result_payload = json.dumps(result, default=str)
                job.output_dir = result.get("output_dir", job.output_dir)
                job.request_hash = result.get("request_hash", job.request_hash)
                job.artifact_dir = result.get("artifact_dir", job.artifact_dir)
                job.session_id = result.get("session_id")
                job.dispatch_state = DISPATCH_STATE_DONE
                job.result_checksum = checksum
                job.artifact_sync_state = ARTIFACT_SYNC_PENDING
                job.artifact_sync_error = None
                job.artifact_last_synced_at = None
                job.finished_at = now
                job.updated_at = now

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
                        result_payload=result,
                        artifact_dir=job.artifact_dir,
                        is_archived=status in {JobStatus.PARTIAL.value, JobStatus.FAILED.value},
                        archived_at=(
                            now
                            if status in {JobStatus.PARTIAL.value, JobStatus.FAILED.value}
                            else None
                        ),
                        projection_source="result_payload",
                    )

                if status in {JobStatus.PARTIAL.value, JobStatus.FAILED.value}:
                    db.add(
                        RetryRun(
                            job_id=job_id,
                            source_session_id=job.session_id,
                            status="available",
                            requested_at=now,
                        )
                    )

                db.add(
                    JobEvent(
                        job_id=job_id,
                        event_type="finished",
                        message=f"Job finished with status={status}",
                        payload="{}",
                        event_time=now,
                    )
                )

                db.commit()
                return job.artifact_dir

        artifact_dir = with_sqlite_lock_retry(
            _persist_terminal_state,
            operation_name="worker.persist_terminal_state",
            serialize_writes=True,
        )
        if artifact_dir is None:
            return
        self._sync_artifact_from_canonical_db(
            job_id,
            result,
            artifact_dir=cast(str | None, artifact_dir),
        )
        self._write_job_log(job_id, f"Job finished with status={status}")
        self._refresh_runtime_counters(refresh_session_drift=True)

    def _persist_exception(self, job_id: str, exc: Exception) -> None:
        """Persist worker exception as terminal failed state."""
        payload = {
            "job_id": job_id,
            "status": JobStatus.FAILED.value,
            "error": str(exc),
            "finished_at": datetime.now(timezone.utc).isoformat(),
        }
        checksum = self._payload_checksum(payload)

        def _persist_error() -> str | None:
            with SessionLocal() as db:
                job = db.get(Job, job_id)
                if not job:
                    return None

                now = datetime.now(timezone.utc)
                job.status = JobStatus.FAILED.value
                job.dispatch_state = DISPATCH_STATE_DONE
                job.result_payload = json.dumps(payload, default=str)
                job.result_checksum = checksum
                job.artifact_sync_state = ARTIFACT_SYNC_PENDING
                job.artifact_sync_error = None
                job.artifact_last_synced_at = None
                job.finished_at = now
                job.updated_at = now
                db.add(
                    JobEvent(
                        job_id=job_id,
                        event_type="error",
                        message=str(exc),
                        payload="{}",
                        event_time=now,
                    )
                )
                db.commit()
                return job.artifact_dir

        artifact_dir = with_sqlite_lock_retry(
            _persist_error,
            operation_name="worker.persist_exception",
            serialize_writes=True,
        )
        if artifact_dir is not None:
            self._sync_artifact_from_canonical_db(
                job_id,
                payload,
                artifact_dir=cast(str | None, artifact_dir),
            )
        self._write_job_log(job_id, f"Job failed: {exc}")
        self._refresh_runtime_counters(refresh_session_drift=True)

    def _sync_artifact_from_canonical_db(
        self,
        job_id: str,
        payload: dict[str, Any],
        *,
        artifact_dir: str | None,
    ) -> bool:
        try:
            self._write_job_artifact(job_id, payload, artifact_dir=artifact_dir)
        except Exception as exc:
            self._mark_artifact_sync_failed(job_id, error=str(exc))
            self._write_job_log(job_id, f"Artifact sync failed: {exc}")
            return False
        self._mark_artifact_sync_synced(job_id)
        return True

    def _mark_artifact_sync_synced(self, job_id: str) -> None:
        def _mark() -> None:
            with SessionLocal() as db:
                job = db.get(Job, job_id)
                if job is None:
                    return
                now = datetime.now(timezone.utc)
                job.artifact_sync_state = ARTIFACT_SYNC_SYNCED
                job.artifact_sync_attempts = int(job.artifact_sync_attempts or 0) + 1
                job.artifact_sync_error = None
                job.artifact_last_synced_at = now
                job.updated_at = now
                db.add(
                    JobEvent(
                        job_id=job_id,
                        event_type="artifact",
                        message="Canonical result payload synced to artifact store",
                        payload="{}",
                        event_time=now,
                    )
                )
                db.commit()

        with_sqlite_lock_retry(
            _mark,
            operation_name="worker.mark_artifact_synced",
            serialize_writes=True,
        )

    def _mark_artifact_sync_failed(self, job_id: str, *, error: str) -> None:
        def _mark() -> None:
            with SessionLocal() as db:
                job = db.get(Job, job_id)
                if job is None:
                    return
                now = datetime.now(timezone.utc)
                job.artifact_sync_state = ARTIFACT_SYNC_FAILED
                job.artifact_sync_attempts = int(job.artifact_sync_attempts or 0) + 1
                job.artifact_sync_error = error
                job.updated_at = now
                db.add(
                    JobEvent(
                        job_id=job_id,
                        event_type="artifact",
                        message="Artifact sync failed",
                        payload=json.dumps({"error": error}),
                        event_time=now,
                    )
                )
                db.commit()

        with_sqlite_lock_retry(
            _mark,
            operation_name="worker.mark_artifact_failed",
            serialize_writes=True,
        )

    @staticmethod
    def _upsert_session(
        db: Any,
        session_id: str,
        input_path: str,
        result_payload: dict[str, Any] | None = None,
        artifact_dir: str | None = None,
        is_archived: bool = False,
        archived_at: datetime | None = None,
        projection_source: str | None = None,
    ) -> None:
        """Project session state into SQL table for fast UI listing."""
        from data_extract.services.session_service import load_session_details

        input_dir = Path(input_path).resolve()
        source_dir = input_dir if input_dir.is_dir() else input_dir.parent

        payload = result_payload if isinstance(result_payload, dict) else {}
        processed_files = payload.get("processed_files")
        failed_files = payload.get("failed_files")
        processed_list = processed_files if isinstance(processed_files, list) else []
        failed_list = failed_files if isinstance(failed_files, list) else []

        status = str(payload.get("status", "unknown"))
        total_files = int(payload.get("total_files", len(processed_list) + len(failed_list)))
        processed_count = int(payload.get("processed_count", len(processed_list)))
        failed_count = int(payload.get("failed_count", len(failed_list)))
        source_directory = str(source_dir)
        updated_at: datetime | None = None
        projection_error: str | None = None
        projection_origin = projection_source or "result_payload"

        updated_at_raw = payload.get("finished_at") or payload.get("updated_at")
        if isinstance(updated_at_raw, str):
            try:
                updated_at = datetime.fromisoformat(updated_at_raw)
            except ValueError:
                projection_error = "invalid_result_payload_timestamp"

        needs_fallback = (
            not payload
            or updated_at is None
            or (total_files <= 0 and processed_count == 0 and failed_count == 0)
        )
        if needs_fallback:
            probe_dirs = [source_dir, source_dir.parent, Path.cwd()]
            details: dict[str, Any] | None = None
            for directory in probe_dirs:
                details = load_session_details(directory, session_id)
                if details:
                    break
            if details:
                stats = details.get("statistics", {})
                projection_origin = "filesystem_fallback" if payload else "filesystem"
                if not source_directory:
                    source_directory = str(details.get("source_directory", source_directory))
                if status == "unknown":
                    status = str(details.get("status", status))
                if total_files <= 0:
                    total_files = int(
                        stats.get("total_files", details.get("total_files", total_files))
                    )
                if processed_count <= 0:
                    processed_count = int(stats.get("processed_count", processed_count))
                if failed_count <= 0:
                    failed_count = int(stats.get("failed_count", failed_count))
                details_updated_at = details.get("updated_at")
                if updated_at is None and isinstance(details_updated_at, str):
                    try:
                        updated_at = datetime.fromisoformat(details_updated_at)
                    except ValueError:
                        if projection_error is None:
                            projection_error = "invalid_filesystem_session_timestamp"

        if updated_at is None:
            updated_at = datetime.now(timezone.utc)
            if projection_error is None and payload:
                projection_error = "missing_result_payload_timestamp"

        record = db.get(SessionRecord, session_id)
        if record is None:
            record = SessionRecord(
                session_id=session_id,
                source_directory=source_directory,
                status=status,
                total_files=total_files,
                processed_count=processed_count,
                failed_count=failed_count,
                artifact_dir=artifact_dir,
                is_archived=1 if is_archived else 0,
                archived_at=archived_at,
                projection_source=projection_origin,
                projection_error=projection_error,
                last_reconciled_at=datetime.now(timezone.utc),
                updated_at=updated_at,
            )
            db.add(record)
        else:
            record.source_directory = source_directory
            record.status = status
            record.total_files = total_files
            record.processed_count = processed_count
            record.failed_count = failed_count
            record.artifact_dir = artifact_dir
            record.is_archived = 1 if is_archived else 0
            record.archived_at = archived_at
            record.projection_source = projection_origin
            record.projection_error = projection_error
            record.last_reconciled_at = datetime.now(timezone.utc)
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
        return (JOBS_HOME / job_id).resolve()

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
                    was_running = job.status == JobStatus.RUNNING.value
                    dispatch_payload = self._load_dispatch_payload(job.dispatch_payload)
                    if dispatch_payload is None:
                        request_payload = self._load_request_payload(job.request_payload)
                        if request_payload is None:
                            recovered_failed += self._mark_recovery_failed(
                                db,
                                job,
                                "Failed to recover job after restart: invalid request payload",
                            )
                            continue
                        dispatch_payload = {"kind": "process", "request": request_payload}
                    if dispatch_payload.get("kind") == "process" and was_running:
                        request_payload = dispatch_payload.get("request", {})
                        if isinstance(request_payload, dict):
                            request_payload["resume"] = True
                            request_payload["force"] = False
                            if job.session_id:
                                request_payload["resume_session"] = job.session_id

                    now = datetime.now(timezone.utc)
                    job.status = JobStatus.QUEUED.value
                    job.dispatch_payload = json.dumps(dispatch_payload, default=str)
                    job.dispatch_state = DISPATCH_STATE_PENDING
                    job.dispatch_last_error = None
                    job.dispatch_next_attempt_at = now
                    job.started_at = None
                    job.finished_at = None
                    job.updated_at = now
                    dispatch_kind = str(dispatch_payload.get("kind", "process"))
                    if was_running and dispatch_kind == "process":
                        message = "Recovered running job after restart; requeued with resume"
                    elif was_running:
                        message = "Recovered running retry after restart; requeued"
                    else:
                        message = "Recovered queued job after restart"

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
                            dispatch_payload,
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
            self._submit_or_defer_dispatch(job_id, payload, source="startup_recovery")
            self._write_job_log(job_id, message)
            recovered_requeued += 1

        self._recovery_stats = {"requeued": recovered_requeued, "failed": recovered_failed}
        self._refresh_runtime_counters()

    def _reconcile_terminal_artifacts(self) -> None:
        """Reconcile terminal job result_payload rows against result.json artifacts."""

        def _load_terminal_job_ids() -> list[str]:
            with SessionLocal() as db:
                return list(
                    db.scalars(
                        select(Job.id)
                        .where(Job.status.in_(TERMINAL_STATUSES))
                        .order_by(
                            Job.artifact_sync_state.asc(),
                            Job.updated_at.asc(),
                        )
                    )
                )

        def _load_unsynced_terminal_job_ids() -> list[str]:
            with SessionLocal() as db:
                return list(
                    db.scalars(
                        select(Job.id)
                        .where(
                            Job.status.in_(TERMINAL_STATUSES),
                            (Job.artifact_sync_state.is_(None))
                            | (Job.artifact_sync_state != ARTIFACT_SYNC_SYNCED),
                        )
                        .order_by(Job.created_at.asc())
                    )
                )

        all_terminal_job_ids = with_sqlite_lock_retry(
            _load_terminal_job_ids,
            operation_name="startup.reconcile_terminal.list",
            serialize_writes=False,
        )
        unsynced_job_ids = with_sqlite_lock_retry(
            _load_unsynced_terminal_job_ids,
            operation_name="startup.reconcile_terminal.list_unsynced",
            serialize_writes=False,
        )
        job_ids = list(dict.fromkeys([*unsynced_job_ids, *all_terminal_job_ids]))
        stats: dict[str, Any] = {
            "scanned": 0,
            "repaired": 0,
            "failed": 0,
            "db_repairs": 0,
            "artifact_repairs": 0,
            "mismatch_repairs": 0,
            "unsynced_scanned": len(unsynced_job_ids),
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
                stats["artifact_repairs"] += 1
                stats["mismatch_repairs"] += 1
            elif outcome == "failed":
                stats["failed"] += 1
        with self._startup_stats_lock:
            self._terminal_reconciliation_stats = stats
        self._refresh_runtime_counters()

    def _reconcile_session_projections(self) -> None:
        """Rehydrate SQL session projections from canonical job rows."""

        def _rehydrate() -> None:
            with SessionLocal() as db:
                jobs = list(
                    db.scalars(
                        select(Job)
                        .where(Job.session_id.is_not(None))
                        .order_by(Job.updated_at.asc(), Job.created_at.asc())
                    )
                )
                for job in jobs:
                    if not job.session_id:
                        continue
                    payload, _error = self._load_json_object(job.result_payload)
                    self._upsert_session(
                        db,
                        str(job.session_id),
                        str(job.input_path),
                        result_payload=payload,
                        artifact_dir=job.artifact_dir,
                        is_archived=job.status in {JobStatus.PARTIAL.value, JobStatus.FAILED.value},
                        archived_at=(
                            job.finished_at
                            if job.status in {JobStatus.PARTIAL.value, JobStatus.FAILED.value}
                            else None
                        ),
                        projection_source="startup_reconcile",
                    )
                db.commit()

        with_sqlite_lock_retry(
            _rehydrate,
            operation_name="startup.reconcile_sessions.rehydrate",
            serialize_writes=True,
        )
        self._refresh_runtime_counters(refresh_session_drift=True)

    def _refresh_runtime_counters(self, refresh_session_drift: bool = False) -> None:
        def _load_counts() -> tuple[int, int]:
            with SessionLocal() as db:
                pending_dispatch = len(
                    list(
                        db.scalars(
                            select(Job.id).where(
                                Job.status == JobStatus.QUEUED.value,
                                (Job.dispatch_state.is_(None))
                                | (
                                    Job.dispatch_state.in_(
                                        [
                                            DISPATCH_STATE_PENDING,
                                            DISPATCH_STATE_PENDING_LEGACY,
                                            DISPATCH_STATE_DISPATCHING,
                                        ]
                                    )
                                ),
                            )
                        )
                    )
                )
                artifact_backlog = len(
                    list(
                        db.scalars(
                            select(Job.id).where(
                                Job.status.in_(TERMINAL_STATUSES),
                                (Job.artifact_sync_state.is_(None))
                                | (Job.artifact_sync_state != ARTIFACT_SYNC_SYNCED),
                            )
                        )
                    )
                )
                return pending_dispatch, artifact_backlog

        pending_dispatch_count, artifact_sync_backlog_count = with_sqlite_lock_retry(
            _load_counts,
            operation_name="runtime_counters.refresh_counts",
            serialize_writes=False,
        )
        session_projection_drift_count = self.session_projection_drift_count
        if refresh_session_drift:
            session_projection_drift_count = self._compute_session_projection_drift()

        with self._runtime_counters_lock:
            self._runtime_counters["pending_dispatch_count"] = int(pending_dispatch_count)
            self._runtime_counters["artifact_sync_backlog_count"] = int(artifact_sync_backlog_count)
            self._runtime_counters["session_projection_drift_count"] = int(
                session_projection_drift_count
            )

    def _compute_session_projection_drift(self) -> int:
        def _load() -> tuple[list[Job], list[SessionRecord]]:
            with SessionLocal() as db:
                jobs = list(
                    db.scalars(
                        select(Job)
                        .where(Job.session_id.is_not(None))
                        .order_by(Job.updated_at.desc(), Job.created_at.desc())
                    )
                )
                projections = list(db.scalars(select(SessionRecord)))
                return jobs, projections

        jobs, projections = with_sqlite_lock_retry(
            _load,
            operation_name="runtime_counters.session_drift.load",
            serialize_writes=False,
        )
        latest_by_session: dict[str, Job] = {}
        for job in jobs:
            session_id = str(job.session_id or "")
            if not session_id or session_id in latest_by_session:
                continue
            latest_by_session[session_id] = job

        projection_map = {record.session_id: record for record in projections}
        drift_count = 0
        for session_id, job in latest_by_session.items():
            expected = self._session_projection_from_job(job)
            projected = projection_map.get(session_id)
            if projected is None:
                drift_count += 1
                continue
            if expected["source_directory"] != projected.source_directory:
                drift_count += 1
                continue
            if expected["status"] != projected.status:
                drift_count += 1
                continue
            if expected["total_files"] != int(projected.total_files):
                drift_count += 1
                continue
            if expected["processed_count"] != int(projected.processed_count):
                drift_count += 1
                continue
            if expected["failed_count"] != int(projected.failed_count):
                drift_count += 1
                continue
        for session_id in projection_map:
            if session_id not in latest_by_session:
                drift_count += 1
        return drift_count

    def _session_projection_from_job(self, job: Job) -> dict[str, Any]:
        payload, _error = self._load_json_object(job.result_payload)
        data = payload if payload is not None else {}
        input_dir = Path(str(job.input_path)).resolve()
        source_dir = input_dir if input_dir.is_dir() else input_dir.parent
        processed_files = data.get("processed_files")
        failed_files = data.get("failed_files")
        processed_list = processed_files if isinstance(processed_files, list) else []
        failed_list = failed_files if isinstance(failed_files, list) else []
        return {
            "source_directory": str(source_dir),
            "status": str(data.get("status", job.status)),
            "total_files": int(data.get("total_files", len(processed_list) + len(failed_list))),
            "processed_count": int(data.get("processed_count", len(processed_list))),
            "failed_count": int(data.get("failed_count", len(failed_list))),
        }

    def _reconcile_terminal_artifact_for_job(self, job_id: str) -> str:
        """Reconcile a single terminal job row and artifact, returning outcome key."""

        def _load_snapshot() -> tuple[str | None, str | None, str | None, str | None] | None:
            with SessionLocal() as db:
                job = db.get(Job, job_id)
                if job is None or job.status not in TERMINAL_STATUSES:
                    return None
                return (
                    job.result_payload,
                    job.artifact_dir,
                    job.artifact_sync_state,
                    job.result_checksum,
                )

        snapshot = with_sqlite_lock_retry(
            _load_snapshot,
            operation_name="startup.reconcile_terminal.snapshot",
            serialize_writes=False,
        )
        if snapshot is None:
            return "noop"
        raw_result_payload, artifact_dir, artifact_sync_state, existing_checksum = snapshot
        db_payload, db_error = self._load_json_object(raw_result_payload)
        artifact_path = (
            self._resolve_artifact_root(job_id, artifact_dir=artifact_dir) / "result.json"
        )
        artifact_payload, artifact_error = self._read_json_object_from_path(artifact_path)

        if db_payload is None:
            self._mark_artifact_sync_failed(
                job_id,
                error=(
                    "Startup reconciliation could not load canonical result_payload "
                    f"(error={db_error})"
                ),
            )
            self._record_terminal_failure_event(
                job_id,
                message="Startup reconciliation failed: canonical result_payload is invalid",
                payload={
                    "phase": "startup_terminal_reconciliation",
                    "failure": "invalid_canonical_result_payload",
                    "result_payload_error": db_error,
                    "artifact_error": artifact_error,
                },
            )
            self._write_job_log(
                job_id,
                "Startup reconciliation failed: canonical result_payload is invalid",
            )
            return "failed"

        canonical_db_payload = self._canonical_payload(db_payload)
        artifact_matches = (
            artifact_payload is not None
            and canonical_db_payload == self._canonical_payload(artifact_payload)
        )
        expected_checksum = self._payload_checksum(db_payload)
        if existing_checksum != expected_checksum:
            self._update_job_result_checksum(job_id, expected_checksum)

        if artifact_matches and artifact_sync_state == ARTIFACT_SYNC_SYNCED:
            return "noop"

        if artifact_payload is None:
            repair_key = "repair_artifact"
            repair_name = "artifact_from_db_missing"
        elif artifact_matches:
            repair_key = "repair_artifact"
            repair_name = "artifact_sync_state_backlog"
        else:
            repair_key = "repair_mismatch"
            repair_name = "artifact_from_db_mismatch"

        synced = self._sync_artifact_from_canonical_db(
            job_id,
            db_payload,
            artifact_dir=artifact_dir,
        )
        if not synced:
            self._record_terminal_failure_event(
                job_id,
                message="Startup reconciliation failed to sync result.json from canonical payload",
                payload={
                    "phase": "startup_terminal_reconciliation",
                    "failure": "artifact_write_failed",
                    "artifact_error": artifact_error,
                },
            )
            self._write_job_log(
                job_id,
                "Startup reconciliation failed to sync result.json from canonical payload",
            )
            return "failed"

        self._record_terminal_repair_event(
            job_id,
            message="Startup reconciliation synced result.json from canonical result_payload",
            payload={
                "phase": "startup_terminal_reconciliation",
                "repair": repair_name,
                "artifact_error": artifact_error,
                "artifact_sync_state": artifact_sync_state,
            },
        )
        self._write_job_log(
            job_id,
            "Startup reconciliation synced result.json from canonical result_payload",
        )
        return repair_key

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
        return validated.model_dump()

    @staticmethod
    def _canonical_payload(payload: dict[str, Any]) -> str:
        return json.dumps(payload, default=str, sort_keys=True, separators=(",", ":"))

    @staticmethod
    def _payload_checksum(payload: dict[str, Any]) -> str:
        canonical = ApiRuntime._canonical_payload(payload)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def _update_job_result_checksum(self, job_id: str, checksum: str) -> None:
        def _persist() -> None:
            with SessionLocal() as db:
                job = db.get(Job, job_id)
                if job is None:
                    return
                job.result_checksum = checksum
                job.updated_at = datetime.now(timezone.utc)
                db.commit()

        with_sqlite_lock_retry(
            _persist,
            operation_name="startup.reconcile_terminal.update_checksum",
            serialize_writes=True,
        )

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
                    job.result_checksum = self._payload_checksum(repaired_payload)
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
        payload = {
            "job_id": job.id,
            "status": JobStatus.FAILED.value,
            "error": message,
            "recovered_at": datetime.now(timezone.utc).isoformat(),
        }
        job.status = JobStatus.FAILED.value
        job.dispatch_state = DISPATCH_STATE_DONE
        job.finished_at = datetime.now(timezone.utc)
        job.updated_at = datetime.now(timezone.utc)
        job.result_payload = json.dumps(payload)
        job.result_checksum = self._payload_checksum(payload)
        job.artifact_sync_state = ARTIFACT_SYNC_PENDING
        job.artifact_sync_error = None
        job.artifact_last_synced_at = None
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
                payload = {
                    "job_id": job_id,
                    "status": JobStatus.FAILED.value,
                    "error": message,
                    "recovered_at": datetime.now(timezone.utc).isoformat(),
                }
                job.status = JobStatus.FAILED.value
                job.dispatch_state = DISPATCH_STATE_DONE
                job.finished_at = datetime.now(timezone.utc)
                job.updated_at = datetime.now(timezone.utc)
                job.result_payload = json.dumps(payload)
                job.result_checksum = self._payload_checksum(payload)
                job.artifact_sync_state = ARTIFACT_SYNC_PENDING
                job.artifact_sync_error = None
                job.artifact_last_synced_at = None
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

        failed_count = with_sqlite_lock_retry(
            _persist,
            operation_name="startup.recover_inflight.persist_submission_failure",
            serialize_writes=True,
        )
        if failed_count:
            self._write_job_log(job_id, message)
        return failed_count

    def _capture_storage_stats(self) -> tuple[int, int, int]:
        usage = shutil.disk_usage(JOBS_HOME)
        total_bytes = int(usage.total)
        used_bytes = int(usage.used)
        free_bytes = int(usage.free)
        used_ratio = (used_bytes / total_bytes) if total_bytes > 0 else 0.0
        with self._storage_stats_lock:
            self._storage_stats["threshold"] = self._disk_pressure_threshold
            self._storage_stats["last_total_bytes"] = total_bytes
            self._storage_stats["last_free_bytes"] = free_bytes
            self._storage_stats["last_used_ratio"] = float(used_ratio)
            self._storage_stats["last_checked_at"] = datetime.now(timezone.utc).isoformat()
            self._storage_stats["last_error"] = None
        return total_bytes, used_bytes, free_bytes

    def _assert_storage_available(self) -> None:
        if self._disk_pressure_threshold <= 0:
            return
        try:
            _total_bytes, _used_bytes, free_bytes = self._capture_storage_stats()
        except OSError as exc:
            with self._storage_stats_lock:
                self._storage_stats["last_checked_at"] = datetime.now(timezone.utc).isoformat()
                self._storage_stats["last_error"] = str(exc)
                self._storage_stats["disk_pressure_rejections"] += 1
            retry_after_seconds = self._record_queue_rejection(reason="disk_pressure")
            raise QueueCapacityError(
                (
                    "Unable to verify available disk space for job admission; "
                    f"storage probe failed: {exc}"
                ),
                retry_after_seconds=retry_after_seconds,
                reason="disk_pressure",
            ) from exc

        if free_bytes >= self._disk_pressure_threshold:
            return

        with self._storage_stats_lock:
            self._storage_stats["disk_pressure_rejections"] += 1
        retry_after_seconds = self._record_queue_rejection(reason="disk_pressure")
        raise QueueCapacityError(
            (
                "Available disk space is below the admission threshold "
                f"(free={free_bytes} bytes, required>={self._disk_pressure_threshold} bytes). "
                "Cleanup artifacts and retry."
            ),
            retry_after_seconds=retry_after_seconds,
            reason="disk_pressure",
        )

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
            elif reason == "disk_pressure":
                self._overload_stats["disk_pressure_rejections"] += 1
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
    def _resolve_disk_pressure_threshold() -> int:
        raw_value = os.environ.get("DATA_EXTRACT_API_MIN_FREE_DISK_BYTES", str(64 * 1024 * 1024))
        try:
            return max(0, int(str(raw_value).strip()))
        except ValueError:
            return 64 * 1024 * 1024

    @staticmethod
    def _resolve_dispatch_poll_interval_seconds() -> float:
        raw_ms = os.environ.get("DATA_EXTRACT_API_DISPATCH_POLL_MS")
        if raw_ms is not None:
            try:
                milliseconds = float(str(raw_ms).strip())
            except ValueError:
                milliseconds = 250.0
            if milliseconds <= 0:
                milliseconds = 250.0
            return min(5.0, max(0.05, milliseconds / 1000.0))

        raw_seconds = os.environ.get("DATA_EXTRACT_API_DISPATCH_POLL_SECONDS", "0.5").strip()
        try:
            value = float(raw_seconds)
        except ValueError:
            return 0.5
        if value <= 0:
            return 0.5
        return min(5.0, max(0.1, value))

    @staticmethod
    def _resolve_dispatch_batch_size() -> int:
        raw_value = os.environ.get("DATA_EXTRACT_API_DISPATCH_BATCH_SIZE", "50").strip()
        try:
            return max(1, int(raw_value))
        except ValueError:
            return 50

    @staticmethod
    def _resolve_artifact_sync_interval_seconds() -> float:
        raw_value = os.environ.get("DATA_EXTRACT_API_ARTIFACT_SYNC_INTERVAL_SECONDS", "30").strip()
        try:
            seconds = float(raw_value)
        except ValueError:
            return 30.0
        if seconds <= 0:
            return 30.0
        return min(3600.0, max(1.0, seconds))

    @staticmethod
    def _resolve_work_dir(input_path: str) -> Path:
        """Resolve session work dir from an input path."""
        resolved = Path(input_path).resolve()
        return resolved if resolved.is_dir() else resolved.parent


runtime = ApiRuntime()
