from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("DATA_EXTRACT_UI_HOME", "/tmp/data-extract-ui-tests")

from data_extract.api.database import Base
from data_extract.api.models import Job
from data_extract.api.routers import health as health_router_module
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


def _seed_process_job(
    session_local,
    *,
    job_id: str,
    status: str,
    request_payload: dict[str, object],
    artifact_dir: Path,
) -> None:
    now = _utc_now()
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
                dispatch_state="pending_dispatch",
                dispatch_attempts=0,
                dispatch_next_attempt_at=now,
                artifact_dir=str(artifact_dir),
                created_at=now,
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

    monkeypatch.setattr(state_module, "SessionLocal", test_session_local)
    monkeypatch.setattr(state_module, "JOBS_HOME", jobs_home)
    monkeypatch.setattr(state_module, "init_database", _init_database_for_test)

    runtime = ApiRuntime()
    monkeypatch.setattr(health_router_module, "runtime", runtime)
    yield runtime, test_session_local, jobs_home
    runtime.stop()


@pytest.mark.filterwarnings("ignore::pytest.PytestUnhandledThreadExceptionWarning")
def test_health_telemetry_transitions_when_worker_crashes_and_watchdog_recovers(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    isolated_runtime,
) -> None:
    from data_extract.api import state as state_module

    runtime, session_local, jobs_home = isolated_runtime
    crash_once = {"triggered": False}

    class ChaosJobService:
        def run_process(
            self,
            request: ProcessJobRequest,
            work_dir: Path | None = None,
            job_id: str | None = None,
            prior_retry_counts: dict[str, int] | None = None,
        ) -> ProcessJobResult:
            del request, work_dir, job_id, prior_retry_counts
            if not crash_once["triggered"]:
                crash_once["triggered"] = True
                raise SystemExit("chaos-worker-crash")
            return ProcessJobResult(
                job_id="unused",
                status="completed",
                total_files=1,
                processed_count=1,
                failed_count=0,
                output_dir=str(tmp_path / "output"),
            )

    monkeypatch.setattr(state_module, "JobService", ChaosJobService)

    runtime.start()
    runtime.set_readiness_report({"status": "ok", "ready": True, "errors": [], "warnings": []})
    baseline = health_router_module.health(detailed=True)
    assert baseline["worker_restarts"] == 0
    assert baseline["dead_workers"] == 0

    request_payload = ProcessJobRequest(
        input_path=str(tmp_path / "chaos-input.txt"),
        output_path=str(jobs_home / "chaos-job" / "outputs"),
        output_format="json",
    ).model_dump()
    _seed_process_job(
        session_local,
        job_id="chaos-job",
        status="queued",
        request_payload=request_payload,
        artifact_dir=jobs_home / "chaos-job",
    )
    runtime.queue.submit("chaos-job", {"kind": "process", "request": request_payload})

    _wait_until(
        lambda: runtime.worker_restarts >= 1 and runtime.dead_workers == 0,
        message="Expected watchdog to restart crashed worker and recover dead worker count.",
    )

    payload = health_router_module.health(detailed=True)
    assert payload["worker_restarts"] >= 1
    assert payload["dead_workers"] == 0
    assert payload["alive_workers"] == payload["workers"]

    with session_local() as db:
        job = db.get(Job, "chaos-job")
    assert job is not None
    assert job.status == "running"


def test_artifact_sync_failure_recovers_and_health_backlog_clears(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    isolated_runtime,
) -> None:
    runtime, session_local, jobs_home = isolated_runtime
    runtime.start()
    runtime.set_readiness_report({"status": "ok", "ready": True, "errors": [], "warnings": []})

    job_id = "artifact-recovery-job"
    artifact_dir = jobs_home / job_id
    request_payload = ProcessJobRequest(
        input_path=str(tmp_path / "artifact-input.txt"),
        output_path=str(artifact_dir / "outputs"),
        output_format="json",
    ).model_dump()
    _seed_process_job(
        session_local,
        job_id=job_id,
        status="queued",
        request_payload=request_payload,
        artifact_dir=artifact_dir,
    )

    original_writer = runtime._write_job_artifact

    def _fail_write(*args, **kwargs) -> None:
        del args, kwargs
        raise OSError("disk full")

    monkeypatch.setattr(runtime, "_write_job_artifact", _fail_write)

    result_payload = {
        "job_id": job_id,
        "status": "completed",
        "total_files": 1,
        "processed_count": 1,
        "failed_count": 0,
        "output_dir": str(artifact_dir / "outputs"),
        "artifact_dir": str(artifact_dir),
        "processed_files": [
            {
                "path": str(tmp_path / "artifact-input.txt"),
                "output_path": "artifact-output.json",
                "chunk_count": 1,
            }
        ],
        "failed_files": [],
    }

    runtime._persist_result(job_id, result_payload)

    with session_local() as db:
        failed_job = db.get(Job, job_id)
    assert failed_job is not None
    assert failed_job.status == "completed"
    assert failed_job.artifact_sync_state == "failed"
    assert "disk full" in str(failed_job.artifact_sync_error or "")

    failed_health = health_router_module.health(detailed=True)
    assert failed_health["artifact_sync_backlog"] == 1

    monkeypatch.setattr(runtime, "_write_job_artifact", original_writer)
    repaired = runtime._sync_pending_artifacts_once(source="test_artifact_repair")
    assert repaired == 1

    repaired_health = health_router_module.health(detailed=True)
    assert repaired_health["artifact_sync_backlog"] == 0

    artifact_path = artifact_dir / "result.json"
    assert artifact_path.exists()
    assert json.loads(artifact_path.read_text(encoding="utf-8")) == result_payload

    with session_local() as db:
        repaired_job = db.get(Job, job_id)
    assert repaired_job is not None
    assert repaired_job.artifact_sync_state == "synced"
    assert repaired_job.artifact_sync_error is None
    assert int(repaired_job.artifact_sync_attempts or 0) >= 2
