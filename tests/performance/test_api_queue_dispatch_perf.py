"""ApiRuntime queue dispatch performance and counter convergence tests."""

from __future__ import annotations

import os
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from threading import Event, Lock
from typing import Any, Callable

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("DATA_EXTRACT_UI_HOME", "/tmp/data-extract-ui-tests")

from data_extract.api.database import Base
from data_extract.api.models import Job, SessionRecord
from data_extract.contracts import (
    JobStatus,
    ProcessedFileOutcome,
    ProcessJobRequest,
    ProcessJobResult,
)

pytestmark = [pytest.mark.P1, pytest.mark.performance]


def _wait_until(
    predicate: Callable[[], bool],
    *,
    timeout_seconds: float,
    interval_seconds: float = 0.02,
) -> bool:
    deadline = time.monotonic() + timeout_seconds
    while True:
        if predicate():
            return True
        if time.monotonic() >= deadline:
            return False
        time.sleep(interval_seconds)


@pytest.fixture
def runtime_harness(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> tuple[Any, Any]:
    from data_extract.api import state as state_module

    monkeypatch.setenv("DATA_EXTRACT_API_WORKERS", "1")
    monkeypatch.setenv("DATA_EXTRACT_API_QUEUE_MAX_BACKLOG", "2")
    monkeypatch.setenv("DATA_EXTRACT_API_DISPATCH_BATCH_SIZE", "16")
    monkeypatch.setenv("DATA_EXTRACT_API_QUEUE_RETRY_HINT_SECONDS", "1")
    monkeypatch.setenv("DATA_EXTRACT_API_DB_LOCK_RETRIES", "8")
    monkeypatch.setenv("DATA_EXTRACT_API_DB_LOCK_BACKOFF_MS", "5")

    db_path = tmp_path / "runtime-perf.db"
    jobs_home = tmp_path / "jobs-home"
    jobs_home.mkdir(parents=True, exist_ok=True)

    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
        future=True,
    )
    test_session_local = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    Base.metadata.create_all(bind=engine)

    monkeypatch.setattr(state_module, "SessionLocal", test_session_local)
    monkeypatch.setattr(state_module, "JOBS_HOME", jobs_home)

    runtime = state_module.ApiRuntime()
    monkeypatch.setattr(runtime, "_write_job_log", lambda *args, **kwargs: None)
    monkeypatch.setattr(runtime, "_compute_request_hash", lambda _request: None)
    monkeypatch.setattr(runtime, "_raise_if_queue_throttled", lambda *args, **kwargs: None)

    runtime.queue.start()
    yield runtime, test_session_local
    runtime.queue.stop()
    engine.dispose()


def _install_fake_process_handler(
    monkeypatch: pytest.MonkeyPatch,
    state_module: Any,
    *,
    release_event: Event,
    tmp_path: Path,
) -> Event:
    started_event = Event()
    started_lock = Lock()
    started_jobs: set[str] = set()

    def fake_run_process(
        self,
        request: ProcessJobRequest,
        work_dir: Path | None = None,
        job_id: str | None = None,
        prior_retry_counts: dict[str, int] | None = None,
    ) -> ProcessJobResult:
        del self, work_dir, prior_retry_counts
        assert job_id is not None
        with started_lock:
            started_jobs.add(job_id)
        started_event.set()
        if not release_event.wait(timeout=8):
            raise TimeoutError("Timed out waiting for test-controlled release signal")

        output_dir = Path(request.output_path or tmp_path / "outputs")
        source_path = str(Path(request.input_path).resolve())
        now = datetime.now(timezone.utc)
        return ProcessJobResult(
            job_id=job_id,
            status=JobStatus.COMPLETED,
            total_files=1,
            processed_count=1,
            failed_count=0,
            skipped_count=0,
            output_dir=str(output_dir),
            session_id=f"sess-{job_id}",
            processed_files=[
                ProcessedFileOutcome(
                    path=source_path,
                    output_path=str(output_dir / f"{job_id}.json"),
                    chunk_count=1,
                )
            ],
            failed_files=[],
            started_at=now,
            finished_at=now,
            artifact_dir=str(output_dir),
            request_hash=f"hash-{job_id}",
            exit_code=0,
        )

    def fake_run_retry(
        self,
        request: Any,
        work_dir: Path | None = None,
    ) -> ProcessJobResult:
        del self, request, work_dir
        raise AssertionError("Retry path should not execute in queue dispatch performance tests")

    monkeypatch.setattr(state_module.JobService, "run_process", fake_run_process)
    monkeypatch.setattr(state_module.RetryService, "run_retry", fake_run_retry)
    return started_event


def _enqueue_concurrently(runtime: Any, *, input_root: Path, total_jobs: int) -> list[str]:
    input_root.mkdir(parents=True, exist_ok=True)
    jobs = [f"perf-job-{index:03d}" for index in range(total_jobs)]

    def _enqueue(job_id: str) -> str:
        request = ProcessJobRequest(
            input_path=str(input_root / f"{job_id}.txt"),
            output_format="json",
            non_interactive=True,
        )
        return runtime.enqueue_process(request, job_id=job_id)

    with ThreadPoolExecutor(max_workers=min(8, total_jobs)) as pool:
        return [future.result() for future in [pool.submit(_enqueue, job_id) for job_id in jobs]]


def _drain_to_convergence(
    runtime: Any, test_session_local: Any, *, total_jobs: int
) -> tuple[int, int]:
    max_pending_seen = 0
    max_artifact_backlog_seen = 0

    def _converged() -> bool:
        nonlocal max_pending_seen, max_artifact_backlog_seen
        runtime._dispatch_pending_jobs_once(source="perf_dispatch")
        runtime._refresh_runtime_counters(refresh_session_drift=True)
        max_pending_seen = max(max_pending_seen, runtime.pending_dispatch_count)
        max_artifact_backlog_seen = max(
            max_artifact_backlog_seen,
            runtime.artifact_sync_backlog_count,
        )
        runtime._sync_pending_artifacts_once(source="perf_artifact_sync", limit=total_jobs)
        runtime._refresh_runtime_counters(refresh_session_drift=True)
        max_pending_seen = max(max_pending_seen, runtime.pending_dispatch_count)
        max_artifact_backlog_seen = max(
            max_artifact_backlog_seen,
            runtime.artifact_sync_backlog_count,
        )
        with test_session_local() as db:
            completed_count = int(
                db.scalar(
                    select(func.count())
                    .select_from(Job)
                    .where(Job.status == JobStatus.COMPLETED.value)
                )
                or 0
            )
        return (
            completed_count == total_jobs
            and runtime.pending_dispatch_count == 0
            and runtime.artifact_sync_backlog_count == 0
        )

    assert _wait_until(_converged, timeout_seconds=12), "Runtime did not converge within 12 seconds"
    return max_pending_seen, max_artifact_backlog_seen


def test_pending_dispatch_and_artifact_backlog_counters_converge_under_enqueue_pressure(
    monkeypatch: pytest.MonkeyPatch,
    runtime_harness: tuple[Any, Any],
    tmp_path: Path,
) -> None:
    runtime, test_session_local = runtime_harness
    from data_extract.api import state as state_module

    release_event = Event()
    started_event = _install_fake_process_handler(
        monkeypatch,
        state_module,
        release_event=release_event,
        tmp_path=tmp_path,
    )

    original_write = runtime._write_job_artifact
    failed_once: set[str] = set()
    fail_limit = 4

    def flaky_write(job_id: str, payload: dict[str, Any], artifact_dir: str | None = None) -> None:
        if len(failed_once) < fail_limit and job_id not in failed_once:
            failed_once.add(job_id)
            raise OSError("intentional artifact sync failure for convergence test")
        original_write(job_id, payload, artifact_dir=artifact_dir)

    monkeypatch.setattr(runtime, "_write_job_artifact", flaky_write)

    total_jobs = 24
    enqueue_started_at = time.perf_counter()
    enqueued_job_ids = _enqueue_concurrently(
        runtime,
        input_root=tmp_path / "inputs",
        total_jobs=total_jobs,
    )
    enqueue_elapsed = time.perf_counter() - enqueue_started_at

    assert len(set(enqueued_job_ids)) == total_jobs
    assert _wait_until(started_event.is_set, timeout_seconds=2), "No worker began processing"

    def _pending_dispatch_seen() -> bool:
        runtime._refresh_runtime_counters()
        return runtime.pending_dispatch_count > 0

    assert _wait_until(
        _pending_dispatch_seen, timeout_seconds=3
    ), "pending_dispatch_count never rose above zero under queue pressure"

    release_event.set()
    max_pending_seen, max_artifact_backlog_seen = _drain_to_convergence(
        runtime,
        test_session_local,
        total_jobs=total_jobs,
    )

    assert enqueue_elapsed < 6.0
    assert max_pending_seen > 0
    assert max_artifact_backlog_seen > 0
    runtime._refresh_runtime_counters(refresh_session_drift=True)
    assert runtime.pending_dispatch_count == 0
    assert runtime.artifact_sync_backlog_count == 0


def test_session_projection_drift_counter_converges_after_reconciliation(
    monkeypatch: pytest.MonkeyPatch,
    runtime_harness: tuple[Any, Any],
    tmp_path: Path,
) -> None:
    runtime, test_session_local = runtime_harness
    from data_extract.api import state as state_module

    release_event = Event()
    _install_fake_process_handler(
        monkeypatch,
        state_module,
        release_event=release_event,
        tmp_path=tmp_path,
    )

    total_jobs = 12
    enqueued_job_ids = _enqueue_concurrently(
        runtime,
        input_root=tmp_path / "inputs-drift",
        total_jobs=total_jobs,
    )
    assert len(set(enqueued_job_ids)) == total_jobs

    release_event.set()
    _drain_to_convergence(runtime, test_session_local, total_jobs=total_jobs)

    with test_session_local() as db:
        records = list(
            db.scalars(select(SessionRecord).order_by(SessionRecord.session_id.asc()).limit(3))
        )
        assert len(records) == 3
        for record in records:
            record.processed_count = 0
            record.status = "running"
        db.commit()

    runtime._refresh_runtime_counters(refresh_session_drift=True)
    assert runtime.session_projection_drift_count >= 3

    runtime._reconcile_session_projections()
    runtime._refresh_runtime_counters(refresh_session_drift=True)
    assert runtime.session_projection_drift_count == 0
