from __future__ import annotations

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("DATA_EXTRACT_UI_HOME", "/tmp/data-extract-ui-tests")

from data_extract.api.database import Base
from data_extract.api.models import Job, JobEvent
from data_extract.api.routers import jobs as jobs_router_module
from data_extract.api.routers.jobs import (
    _build_process_request_from_form,
    download_job_artifact,
    enqueue_process_job,
    list_job_artifacts,
    retry_job_failures,
)
from data_extract.contracts import ProcessJobRequest


class JsonRequestStub:
    def __init__(self, payload: dict[str, Any]) -> None:
        self._payload = payload
        self.headers = {"content-type": "application/json"}

    async def json(self) -> dict[str, Any]:
        return self._payload


class DummyUpload:
    def __init__(self, filename: str, payload: bytes) -> None:
        self.filename = filename
        self._payload = payload

    async def read(self) -> bytes:
        return self._payload


class FormDataStub:
    def __init__(self, values: dict[str, Any], files: list[DummyUpload]) -> None:
        self._values = values
        self._files = files

    def get(self, key: str, default: Any = None) -> Any:
        return self._values.get(key, default)

    def getlist(self, key: str) -> list[Any]:
        if key == "files":
            return list(self._files)
        return []


class MultipartRequestStub:
    def __init__(self, values: dict[str, Any], files: list[DummyUpload]) -> None:
        self._form = FormDataStub(values, files)
        self.headers = {"content-type": "multipart/form-data; boundary=test"}

    async def form(self) -> FormDataStub:
        return self._form


@pytest.mark.unit
def test_enqueue_process_job_json(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def fake_enqueue(request: ProcessJobRequest, job_id: str | None = None) -> str:
        captured["request"] = request
        captured["job_id"] = job_id
        return job_id or "fallback"

    monkeypatch.setattr(jobs_router_module.runtime, "enqueue_process", fake_enqueue)

    request = JsonRequestStub(
        {
            "input_path": "/tmp/source",
            "output_format": "json",
            "chunk_size": 128,
        }
    )
    response = asyncio.run(enqueue_process_job(request))  # type: ignore[arg-type]

    assert response.status == "queued"
    assert response.job_id
    assert isinstance(captured["request"], ProcessJobRequest)


@pytest.mark.unit
def test_enqueue_process_job_multipart_upload(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(jobs_router_module, "JOBS_HOME", tmp_path)
    monkeypatch.setattr(jobs_router_module, "UploadFile", DummyUpload)

    files = [
        DummyUpload(filename="nested/upload.txt", payload=b"hello world"),
    ]
    request = MultipartRequestStub(
        values={"chunk_size": "64", "output_format": "json"},
        files=files,
    )
    process_request = asyncio.run(
        _build_process_request_from_form(request, "job-123")  # type: ignore[arg-type]
    )

    assert isinstance(process_request, ProcessJobRequest)
    assert process_request.input_path.startswith(str(tmp_path))
    assert any(tmp_path.rglob("upload.txt"))


@pytest.mark.unit
def test_build_process_request_from_form_supports_semantic_fields(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(jobs_router_module, "JOBS_HOME", tmp_path)
    monkeypatch.setattr(jobs_router_module, "UploadFile", DummyUpload)

    request = MultipartRequestStub(
        values={
            "input_path": "/tmp/source",
            "semantic": "true",
            "semantic_report": "true",
            "semantic_export_graph": "true",
            "semantic_graph_format": "dot",
            "semantic_duplicate_threshold": "0.9",
        },
        files=[],
    )
    process_request = asyncio.run(
        _build_process_request_from_form(request, "job-124")  # type: ignore[arg-type]
    )

    assert process_request.include_semantic is True
    assert process_request.semantic_report is True
    assert process_request.semantic_export_graph is True
    assert process_request.semantic_graph_format == "dot"
    assert process_request.semantic_duplicate_threshold == 0.9


@pytest.mark.unit
def test_retry_job_failures_persists_queued_state_before_enqueue(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    db_path = tmp_path / "jobs.db"
    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
        future=True,
    )
    test_session_local = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    Base.metadata.create_all(bind=engine)

    job_id = "retry-job-001"
    session_id = "sess-001"
    with test_session_local() as db:
        db.add(
            Job(
                id=job_id,
                status="partial",
                input_path=str(tmp_path / "input"),
                output_dir=str(tmp_path / "output"),
                requested_format="json",
                chunk_size=512,
                request_payload="{}",
                result_payload=json.dumps({"session_id": session_id}),
                session_id=session_id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
        )
        db.commit()

    observed: dict[str, Any] = {}

    def fake_enqueue_retry(*, job_id: str, request: Any) -> None:
        with test_session_local() as db:
            job = db.get(Job, job_id)
            events = list(
                db.scalars(
                    select(JobEvent)
                    .where(JobEvent.job_id == job_id)
                    .order_by(JobEvent.event_time.asc())
                )
            )
        observed["job_id"] = job_id
        observed["request"] = request
        observed["status"] = job.status if job else None
        observed["started_at"] = job.started_at if job else "missing"
        observed["finished_at"] = job.finished_at if job else "missing"
        observed["queued_events"] = [event.event_type for event in events if event.event_type == "queued"]
        observed["queued_messages"] = [event.message for event in events if event.event_type == "queued"]

    monkeypatch.setattr(jobs_router_module, "SessionLocal", test_session_local)
    monkeypatch.setattr(jobs_router_module.runtime, "enqueue_retry", fake_enqueue_retry)

    response = retry_job_failures(job_id)

    assert response.job_id == job_id
    assert response.status == "queued"
    assert observed["job_id"] == job_id
    assert observed["request"].session == session_id
    assert observed["status"] == "queued"
    assert observed["started_at"] is None
    assert observed["finished_at"] is None
    assert observed["queued_events"] == ["queued"]
    assert observed["queued_messages"] == ["Retry queued"]


@pytest.mark.unit
def test_job_artifact_list_and_download(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    db_path = tmp_path / "jobs.db"
    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
        future=True,
    )
    test_session_local = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    Base.metadata.create_all(bind=engine)

    job_id = "artifacts-job-001"
    with test_session_local() as db:
        db.add(
            Job(
                id=job_id,
                status="completed",
                input_path=str(tmp_path / "input"),
                output_dir=str(tmp_path / "output"),
                requested_format="json",
                chunk_size=512,
                request_payload="{}",
                result_payload="{}",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
        )
        db.commit()

    job_dir = tmp_path / job_id
    artifact_path = job_dir / "semantic" / "semantic_summary.json"
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_text("{}", encoding="utf-8")

    monkeypatch.setattr(jobs_router_module, "SessionLocal", test_session_local)
    monkeypatch.setattr(jobs_router_module, "JOBS_HOME", tmp_path)

    listing = list_job_artifacts(job_id)
    assert listing.job_id == job_id
    assert any(entry.path == "semantic/semantic_summary.json" for entry in listing.artifacts)

    response = download_job_artifact(job_id, "semantic/semantic_summary.json")
    assert "semantic_summary.json" in str(response.path)
