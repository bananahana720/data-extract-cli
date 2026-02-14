from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("DATA_EXTRACT_UI_HOME", "/tmp/data-extract-ui-tests")

from data_extract.api.database import Base
from data_extract.api.models import Job, JobEvent
from data_extract.api.state import ApiRuntime, QueueCapacityError
from data_extract.contracts import ProcessJobRequest, RetryRequest
from data_extract.runtime.queue import QueueFullError


@pytest.mark.unit
def test_recover_inflight_jobs_requeues_queued_and_running(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from data_extract.api import state as state_module

    db_path = tmp_path / "jobs.db"
    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
        future=True,
    )
    test_session_local = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    Base.metadata.create_all(bind=engine)

    request_payload = ProcessJobRequest(
        input_path=str(tmp_path / "input"),
        output_path=str(tmp_path / "output"),
        output_format="json",
    ).model_dump()

    with test_session_local() as db:
        db.add(
            Job(
                id="queued-job",
                status="queued",
                input_path=str(tmp_path / "input"),
                output_dir=str(tmp_path / "output"),
                requested_format="json",
                chunk_size=512,
                request_payload=json.dumps(request_payload),
                result_payload="{}",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
        )
        db.add(
            Job(
                id="running-job",
                status="running",
                input_path=str(tmp_path / "input"),
                output_dir=str(tmp_path / "output"),
                requested_format="json",
                chunk_size=512,
                request_payload=json.dumps(request_payload),
                result_payload="{}",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                started_at=datetime.now(timezone.utc),
            )
        )
        db.commit()

    monkeypatch.setattr(state_module, "SessionLocal", test_session_local)
    runtime = ApiRuntime()
    submitted: list[tuple[str, dict[str, object]]] = []
    monkeypatch.setattr(runtime, "_write_job_log", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        runtime.queue,
        "submit",
        lambda job_id, payload: submitted.append((job_id, payload)),
    )

    runtime._recover_inflight_jobs()

    with test_session_local() as db:
        queued_job = db.get(Job, "queued-job")
        running_job = db.get(Job, "running-job")
        events = list(db.query(JobEvent).filter(JobEvent.job_id == "running-job"))

    assert queued_job is not None
    assert queued_job.status == "queued"
    assert running_job is not None
    assert running_job.status == "queued"
    assert len(submitted) == 2
    assert submitted[0][0] == "queued-job"
    assert submitted[1][0] == "running-job"
    running_payload = submitted[1][1]
    assert running_payload["kind"] == "process"
    assert running_payload["request"]["resume"] is True
    assert running_payload["request"]["force"] is False
    assert any(event.event_type == "queued" for event in events)
    assert runtime.recovery_stats == {"requeued": 2, "failed": 0}


@pytest.mark.unit
def test_enqueue_process_queue_full_discards_unaccepted_idempotent_job(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from data_extract.api import state as state_module

    db_path = tmp_path / "jobs.db"
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
    runtime = ApiRuntime()
    monkeypatch.setattr(runtime, "_write_job_log", lambda *args, **kwargs: None)
    monkeypatch.setattr(runtime, "_compute_request_hash", lambda _request: "hash-1")

    first_request = ProcessJobRequest(
        input_path=str(tmp_path / "input"),
        output_format="json",
        idempotency_key="idem-123",
    )
    second_request = ProcessJobRequest(
        input_path=str(tmp_path / "input"),
        output_format="json",
        idempotency_key="idem-123",
    )

    def reject_submit(_job_id: str, _payload: dict[str, object]) -> None:
        raise QueueFullError("Queue backlog is at capacity (1000); try again later.")

    monkeypatch.setattr(runtime.queue, "submit", reject_submit)
    with pytest.raises(QueueCapacityError):
        runtime.enqueue_process(first_request, job_id="job-full-1")

    with test_session_local() as db:
        assert db.get(Job, "job-full-1") is None
        stale_events = list(db.query(JobEvent).filter(JobEvent.job_id == "job-full-1"))
    assert stale_events == []
    assert not (jobs_home / "job-full-1").exists()

    submitted: list[str] = []

    def accept_submit(job_id: str, _payload: dict[str, object]) -> None:
        submitted.append(job_id)

    monkeypatch.setattr(runtime.queue, "submit", accept_submit)
    queued_job_id = runtime.enqueue_process(second_request, job_id="job-full-2")

    assert queued_job_id == "job-full-2"
    assert submitted == ["job-full-2"]
    with test_session_local() as db:
        persisted_job = db.get(Job, "job-full-2")
    assert persisted_job is not None
    assert persisted_job.status == "queued"


@pytest.mark.unit
def test_enqueue_retry_queue_full_preserves_existing_result_payload(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from data_extract.api import state as state_module

    db_path = tmp_path / "jobs.db"
    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
        future=True,
    )
    test_session_local = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    Base.metadata.create_all(bind=engine)

    original_payload = {"session_id": "sess-keep", "failed_files": [{"path": "a.txt"}]}
    with test_session_local() as db:
        db.add(
            Job(
                id="retry-keep",
                status="partial",
                input_path=str(tmp_path / "input"),
                output_dir=str(tmp_path / "output"),
                requested_format="json",
                chunk_size=512,
                request_payload="{}",
                result_payload=json.dumps(original_payload),
                session_id="sess-keep",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
        )
        db.commit()

    monkeypatch.setattr(state_module, "SessionLocal", test_session_local)
    runtime = ApiRuntime()
    monkeypatch.setattr(runtime, "_write_job_log", lambda *args, **kwargs: None)

    def reject_submit(_job_id: str, _payload: dict[str, object]) -> None:
        raise QueueFullError("Queue backlog is at capacity (1000); try again later.")

    monkeypatch.setattr(runtime.queue, "submit", reject_submit)

    with pytest.raises(QueueCapacityError):
        runtime.enqueue_retry(
            "retry-keep",
            RetryRequest(session="sess-keep", non_interactive=True, last=False),
        )

    with test_session_local() as db:
        job = db.get(Job, "retry-keep")

    assert job is not None
    assert job.status == "partial"
    assert json.loads(job.result_payload or "{}") == original_payload


@pytest.mark.unit
def test_recover_inflight_jobs_submits_once_when_db_lock_retry_occurs(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from data_extract.api import state as state_module

    db_path = tmp_path / "jobs.db"
    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
        future=True,
    )
    base_session_local = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    Base.metadata.create_all(bind=engine)

    request_payload = ProcessJobRequest(
        input_path=str(tmp_path / "input"),
        output_path=str(tmp_path / "output"),
        output_format="json",
    ).model_dump()
    with base_session_local() as db:
        db.add(
            Job(
                id="queued-job",
                status="queued",
                input_path=str(tmp_path / "input"),
                output_dir=str(tmp_path / "output"),
                requested_format="json",
                chunk_size=512,
                request_payload=json.dumps(request_payload),
                result_payload="{}",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
        )
        db.commit()

    failures_remaining = {"count": 1}

    def flaky_session_local():
        session = base_session_local()
        real_commit = session.commit

        def flaky_commit() -> None:
            if failures_remaining["count"] > 0:
                failures_remaining["count"] -= 1
                raise OperationalError("database is locked", params=None, orig=Exception("lock"))
            real_commit()

        session.commit = flaky_commit  # type: ignore[method-assign]
        return session

    monkeypatch.setattr(state_module, "SessionLocal", flaky_session_local)
    runtime = ApiRuntime()
    monkeypatch.setattr(runtime, "_write_job_log", lambda *args, **kwargs: None)

    submitted: list[str] = []
    monkeypatch.setattr(
        runtime.queue,
        "submit",
        lambda job_id, payload: submitted.append(f"{job_id}:{payload.get('kind')}"),
    )

    runtime._recover_inflight_jobs()

    assert submitted == ["queued-job:process"]
    assert runtime.recovery_stats == {"requeued": 1, "failed": 0}


@pytest.mark.unit
@pytest.mark.parametrize("existing_status", ["running", "completed"])
def test_enqueue_process_idempotent_replay_returns_existing_job_when_throttled(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    existing_status: str,
) -> None:
    monkeypatch.setenv("DATA_EXTRACT_API_QUEUE_MAX_BACKLOG", "2")
    monkeypatch.setenv("DATA_EXTRACT_API_QUEUE_HIGH_WATERMARK", "0.5")

    runtime = ApiRuntime()
    runtime.queue.submit("seed-job", {"kind": "process"})
    monkeypatch.setattr(runtime, "_compute_request_hash", lambda _request: "hash-replay")
    monkeypatch.setattr(
        runtime.persistence,
        "find_idempotent_job",
        lambda _idempotency_key, _request_hash: ("existing-job", existing_status, {}),
    )
    monkeypatch.setattr(
        runtime.queue,
        "submit",
        lambda *_args, **_kwargs: pytest.fail(
            "queue.submit must not be called for idempotent replay"
        ),
    )

    replay_request = ProcessJobRequest(
        input_path=str(tmp_path / "input"),
        output_format="json",
        idempotency_key="idem-replay",
    )
    resolved_job_id = runtime.enqueue_process(replay_request, job_id="new-job-id")

    assert resolved_job_id == "existing-job"
    overload = runtime.overload_stats
    assert overload["throttle_rejections"] == 0
    assert overload["last_reason"] is None


@pytest.mark.unit
def test_enqueue_process_new_work_still_throttles_at_high_watermark(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("DATA_EXTRACT_API_QUEUE_MAX_BACKLOG", "2")
    monkeypatch.setenv("DATA_EXTRACT_API_QUEUE_HIGH_WATERMARK", "0.5")
    monkeypatch.setenv("DATA_EXTRACT_API_QUEUE_RETRY_HINT_SECONDS", "4")

    runtime = ApiRuntime()
    runtime.queue.submit("seed-job", {"kind": "process"})
    monkeypatch.setattr(runtime, "_compute_request_hash", lambda _request: "hash-new")
    monkeypatch.setattr(
        runtime.persistence,
        "find_idempotent_job",
        lambda _idempotency_key, _request_hash: None,
    )
    monkeypatch.setattr(
        runtime.queue,
        "submit",
        lambda *_args, **_kwargs: pytest.fail(
            "queue.submit should not be called when process enqueue is throttled"
        ),
    )

    new_request = ProcessJobRequest(
        input_path=str(tmp_path / "input"),
        output_format="json",
        idempotency_key="idem-new-work",
    )
    with pytest.raises(QueueCapacityError) as exc_info:
        runtime.enqueue_process(new_request, job_id="new-work-job")

    assert exc_info.value.reason == "process"
    assert "above throttle watermark" in str(exc_info.value)
    assert exc_info.value.retry_after_seconds == 4
    overload = runtime.overload_stats
    assert overload["throttle_rejections"] >= 1
    assert overload["last_reason"] == "high_watermark"
    assert overload["last_retry_after_seconds"] == 4


@pytest.mark.unit
def test_enqueue_retry_throttles_at_high_watermark_and_records_overload_stats(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DATA_EXTRACT_API_QUEUE_MAX_BACKLOG", "2")
    monkeypatch.setenv("DATA_EXTRACT_API_QUEUE_HIGH_WATERMARK", "0.5")
    monkeypatch.setenv("DATA_EXTRACT_API_QUEUE_RETRY_HINT_SECONDS", "3")

    runtime = ApiRuntime()
    runtime.queue.submit("seed-job", {"kind": "process"})

    with pytest.raises(QueueCapacityError) as exc_info:
        runtime.enqueue_retry(
            "retry-throttle",
            RetryRequest(session="sess-throttle", non_interactive=True, last=False),
        )

    assert "Retry after ~3s" in str(exc_info.value)
    assert exc_info.value.retry_after_seconds == 3

    overload = runtime.overload_stats
    assert overload["throttle_rejections"] >= 1
    assert overload["last_reason"] == "high_watermark"
    assert overload["last_retry_after_seconds"] == 3


@pytest.mark.unit
def test_reconcile_terminal_artifacts_repairs_and_records_failures(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from data_extract.api import state as state_module

    db_path = tmp_path / "jobs.db"
    jobs_home = tmp_path / "jobs-home"
    jobs_home.mkdir(parents=True, exist_ok=True)
    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
        future=True,
    )
    test_session_local = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    Base.metadata.create_all(bind=engine)

    artifact_payload = {"status": "completed", "session_id": "sess-artifact"}
    db_payload = {"status": "failed", "error": "boom"}

    artifact_source_dir = jobs_home / "job-db-repair"
    artifact_source_dir.mkdir(parents=True, exist_ok=True)
    (artifact_source_dir / "result.json").write_text(json.dumps(artifact_payload), encoding="utf-8")

    with test_session_local() as db:
        db.add(
            Job(
                id="job-db-repair",
                status="completed",
                input_path=str(tmp_path / "input"),
                output_dir=str(tmp_path / "output"),
                requested_format="json",
                chunk_size=512,
                request_payload="{}",
                result_payload="{bad-json",
                artifact_dir=str(artifact_source_dir),
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
        )
        db.add(
            Job(
                id="job-artifact-repair",
                status="failed",
                input_path=str(tmp_path / "input"),
                output_dir=str(tmp_path / "output"),
                requested_format="json",
                chunk_size=512,
                request_payload="{}",
                result_payload=json.dumps(db_payload),
                artifact_dir=str(jobs_home / "job-artifact-repair"),
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
        )
        db.add(
            Job(
                id="job-repair-failure",
                status="partial",
                input_path=str(tmp_path / "input"),
                output_dir=str(tmp_path / "output"),
                requested_format="json",
                chunk_size=512,
                request_payload="{}",
                result_payload="{still-bad-json",
                artifact_dir=str(jobs_home / "job-repair-failure"),
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
        )
        db.commit()

    monkeypatch.setattr(state_module, "SessionLocal", test_session_local)
    monkeypatch.setattr(state_module, "JOBS_HOME", jobs_home)
    runtime = ApiRuntime()
    monkeypatch.setattr(runtime, "_write_job_log", lambda *args, **kwargs: None)

    runtime._reconcile_terminal_artifacts()

    stats = runtime.terminal_reconciliation_stats
    assert stats["scanned"] == 3
    assert stats["repaired"] == 2
    assert stats["failed"] == 1
    assert stats["db_repairs"] == 1
    assert stats["artifact_repairs"] == 1

    repaired_artifact_path = jobs_home / "job-artifact-repair" / "result.json"
    assert repaired_artifact_path.exists()
    assert json.loads(repaired_artifact_path.read_text(encoding="utf-8")) == db_payload

    with test_session_local() as db:
        repaired_db_job = db.get(Job, "job-db-repair")
        assert repaired_db_job is not None
        assert json.loads(repaired_db_job.result_payload or "{}") == artifact_payload

        db_repair_events = list(db.query(JobEvent).filter(JobEvent.job_id == "job-db-repair"))
        artifact_repair_events = list(
            db.query(JobEvent).filter(JobEvent.job_id == "job-artifact-repair")
        )
        failure_events = list(db.query(JobEvent).filter(JobEvent.job_id == "job-repair-failure"))

    assert any(event.event_type == "repair" for event in db_repair_events)
    assert any(event.event_type == "repair" for event in artifact_repair_events)
    assert any(event.event_type == "error" for event in failure_events)
