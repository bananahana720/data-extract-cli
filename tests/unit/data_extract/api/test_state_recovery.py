from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("DATA_EXTRACT_UI_HOME", "/tmp/data-extract-ui-tests")

from data_extract.api.database import Base
from data_extract.api.models import Job, JobEvent
from data_extract.api.state import ApiRuntime
from data_extract.contracts import ProcessJobRequest


@pytest.mark.unit
def test_recover_inflight_jobs_requeues_queued_and_fails_running(
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
    assert running_job.status == "failed"
    assert submitted and submitted[0][0] == "queued-job"
    assert any(event.event_type == "error" for event in events)
    assert runtime.recovery_stats == {"requeued": 1, "failed": 1}
