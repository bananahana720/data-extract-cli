from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("DATA_EXTRACT_UI_HOME", "/tmp/data-extract-ui-tests")

from data_extract.api.database import Base
from data_extract.api.models import Job, JobEvent
from data_extract.api.state import ApiRuntime
from data_extract.contracts import ProcessJobRequest, ProcessJobResult

pytestmark = [pytest.mark.P0, pytest.mark.integration]


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _wait_until(
    predicate, *, timeout_seconds: float = 8.0, poll_interval_seconds: float = 0.05, message: str
) -> None:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        if predicate():
            return
        time.sleep(poll_interval_seconds)
    raise AssertionError(message)


def _seed_recoverable_job(
    session_local,
    *,
    job_id: str,
    status: str,
    request_payload: dict[str, object],
    artifact_dir: Path,
    session_id: str | None = None,
) -> None:
    now = _utc_now()
    dispatch_state = "running" if status == "running" else "pending_dispatch"
    started_at = now if status == "running" else None

    with session_local() as db:
        db.add(
            Job(
                id=job_id,
                status=status,
                input_path=str(request_payload["input_path"]),
                output_dir=str(artifact_dir / "outputs"),
                requested_format="json",
                chunk_size=512,
                request_payload=json.dumps(request_payload, default=str),
                dispatch_payload=json.dumps({"kind": "process", "request": request_payload}),
                result_payload="{}",
                dispatch_state=dispatch_state,
                dispatch_attempts=0,
                dispatch_next_attempt_at=now,
                artifact_dir=str(artifact_dir),
                session_id=session_id,
                created_at=now,
                started_at=started_at,
                updated_at=now,
            )
        )
        db.commit()


@pytest.fixture
def isolated_runtime(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    from data_extract.api import state as state_module

    db_path = tmp_path / "runtime.db"
    jobs_home = tmp_path / "jobs-home"
    jobs_home.mkdir(parents=True, exist_ok=True)

    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
        future=True,
    )
    test_session_local = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    Base.metadata.create_all(bind=engine)

    def _init_database_for_test() -> None:
        Base.metadata.create_all(bind=engine)

    call_counts: dict[str, int] = {}
    request_flags: dict[str, dict[str, object]] = {}
    call_lock = Lock()

    class DeterministicJobService:
        def run_process(
            self,
            request: ProcessJobRequest,
            work_dir: Path | None = None,
            job_id: str | None = None,
            prior_retry_counts: dict[str, int] | None = None,
        ) -> ProcessJobResult:
            del work_dir, prior_retry_counts
            assert job_id is not None
            with call_lock:
                call_counts[job_id] = call_counts.get(job_id, 0) + 1
                request_flags[job_id] = {
                    "resume": bool(request.resume),
                    "force": bool(request.force),
                    "resume_session": request.resume_session,
                }

            artifact_dir = jobs_home / job_id
            artifact_dir.mkdir(parents=True, exist_ok=True)
            return ProcessJobResult(
                job_id=job_id,
                status="completed",
                total_files=1,
                processed_count=1,
                failed_count=0,
                output_dir=str(artifact_dir / "outputs"),
                artifact_dir=str(artifact_dir),
                processed_files=[
                    {
                        "path": str(tmp_path / f"{job_id}.txt"),
                        "output_path": f"{job_id}.json",
                        "chunk_count": 1,
                    }
                ],
                failed_files=[],
            )

    monkeypatch.setattr(state_module, "SessionLocal", test_session_local)
    monkeypatch.setattr(state_module, "JOBS_HOME", jobs_home)
    monkeypatch.setattr(state_module, "init_database", _init_database_for_test)
    monkeypatch.setattr(state_module, "JobService", DeterministicJobService)

    runtime = ApiRuntime()
    yield runtime, test_session_local, jobs_home, call_counts, request_flags
    runtime.stop()


def test_restart_recovery_requeues_running_and_queued_once_without_duplicates(
    tmp_path: Path,
    isolated_runtime,
) -> None:
    runtime, session_local, jobs_home, call_counts, request_flags = isolated_runtime

    queued_payload = ProcessJobRequest(
        input_path=str(tmp_path / "queued-input.txt"),
        output_path=str(jobs_home / "queued-job" / "outputs"),
        output_format="json",
    ).model_dump()
    running_payload = ProcessJobRequest(
        input_path=str(tmp_path / "running-input.txt"),
        output_path=str(jobs_home / "running-job" / "outputs"),
        output_format="json",
        resume=False,
        force=True,
    ).model_dump()

    _seed_recoverable_job(
        session_local,
        job_id="queued-job",
        status="queued",
        request_payload=queued_payload,
        artifact_dir=jobs_home / "queued-job",
    )
    _seed_recoverable_job(
        session_local,
        job_id="running-job",
        status="running",
        request_payload=running_payload,
        artifact_dir=jobs_home / "running-job",
        session_id="session-running-123",
    )

    runtime.start()

    def _jobs_completed() -> bool:
        with session_local() as db:
            queued = db.get(Job, "queued-job")
            running = db.get(Job, "running-job")
            if queued is None or running is None:
                return False
            return queued.status == "completed" and running.status == "completed"

    _wait_until(
        _jobs_completed,
        message="Recovered jobs did not transition to completed state.",
    )
    _wait_until(
        lambda: call_counts.get("queued-job", 0) == 1 and call_counts.get("running-job", 0) == 1,
        message="Recovered jobs were not executed exactly once.",
    )

    runtime._dispatch_pending_jobs_once(source="post_recovery_duplicate_check")
    time.sleep(0.25)

    assert call_counts == {"queued-job": 1, "running-job": 1}
    assert runtime.recovery_stats == {"requeued": 2, "failed": 0}

    queued_flags = request_flags["queued-job"]
    running_flags = request_flags["running-job"]
    assert queued_flags["resume"] is False
    assert running_flags["resume"] is True
    assert running_flags["force"] is False
    assert running_flags["resume_session"] == "session-running-123"

    with session_local() as db:
        queued_job = db.get(Job, "queued-job")
        running_job = db.get(Job, "running-job")
        queued_events = list(db.query(JobEvent).filter(JobEvent.job_id == "queued-job"))
        running_events = list(db.query(JobEvent).filter(JobEvent.job_id == "running-job"))

    assert queued_job is not None
    assert running_job is not None
    assert queued_job.dispatch_state == "done"
    assert running_job.dispatch_state == "done"
    assert len([event for event in queued_events if event.event_type == "finished"]) == 1
    assert len([event for event in running_events if event.event_type == "finished"]) == 1
