from __future__ import annotations

import asyncio
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("DATA_EXTRACT_UI_HOME", "/tmp/data-extract-ui-tests")

from data_extract.api.database import Base
from data_extract.api.models import AppSetting, Job, JobEvent
from data_extract.api.routers import jobs as jobs_router_module
from data_extract.api.routers.jobs import (
    _build_process_request_from_form,
    download_job_artifact,
    enqueue_process_job,
    get_job,
    list_job_artifacts,
    list_jobs,
    retry_job_failures,
)
from data_extract.api.state import QueueCapacityError
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
        self._offset = 0

    async def read(self, size: int = -1) -> bytes:
        if size is None or size < 0:
            size = len(self._payload) - self._offset
        if self._offset >= len(self._payload):
            return b""
        chunk = self._payload[self._offset : self._offset + size]
        self._offset += len(chunk)
        return chunk


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
            "input_path": str(jobs_router_module.JOBS_HOME / "source"),
            "output_format": "json",
            "chunk_size": 128,
        }
    )
    response = asyncio.run(enqueue_process_job(request))  # type: ignore[arg-type]

    assert response.status == "queued"
    assert response.job_id
    assert isinstance(captured["request"], ProcessJobRequest)


@pytest.mark.unit
def test_enqueue_process_job_uses_current_preset_when_missing(
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

    with test_session_local() as db:
        db.add(
            AppSetting(key="last_preset", value="quality", updated_at=datetime.now(timezone.utc))
        )
        db.commit()

    captured: dict[str, object] = {}

    def fake_enqueue(request: ProcessJobRequest, job_id: str | None = None) -> str:
        captured["request"] = request
        captured["job_id"] = job_id
        return job_id or "fallback"

    monkeypatch.setattr(jobs_router_module, "SessionLocal", test_session_local)
    monkeypatch.setattr(jobs_router_module.runtime, "enqueue_process", fake_enqueue)

    request = JsonRequestStub(
        {
            "input_path": str(jobs_router_module.JOBS_HOME / "source"),
            "output_format": "json",
            "chunk_size": 128,
        }
    )
    response = asyncio.run(enqueue_process_job(request))  # type: ignore[arg-type]

    assert response.status == "queued"
    assert isinstance(captured["request"], ProcessJobRequest)
    assert captured["request"].preset == "quality"


@pytest.mark.unit
def test_enqueue_process_job_explicit_preset_overrides_persisted_default(
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

    with test_session_local() as db:
        db.add(
            AppSetting(key="last_preset", value="quality", updated_at=datetime.now(timezone.utc))
        )
        db.commit()

    captured: dict[str, object] = {}

    def fake_enqueue(request: ProcessJobRequest, job_id: str | None = None) -> str:
        captured["request"] = request
        captured["job_id"] = job_id
        return job_id or "fallback"

    monkeypatch.setattr(jobs_router_module, "SessionLocal", test_session_local)
    monkeypatch.setattr(jobs_router_module.runtime, "enqueue_process", fake_enqueue)

    request = JsonRequestStub(
        {
            "input_path": str(jobs_router_module.JOBS_HOME / "source"),
            "output_format": "json",
            "chunk_size": 128,
            "preset": "speed",
        }
    )
    response = asyncio.run(enqueue_process_job(request))  # type: ignore[arg-type]

    assert response.status == "queued"
    assert isinstance(captured["request"], ProcessJobRequest)
    assert captured["request"].preset == "speed"


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
def test_build_process_request_from_form_sanitizes_absolute_upload_filename(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(jobs_router_module, "JOBS_HOME", tmp_path)
    monkeypatch.setattr(jobs_router_module, "UploadFile", DummyUpload)

    request = MultipartRequestStub(
        values={},
        files=[DummyUpload(filename="/etc/passwd", payload=b"x")],
    )
    process_request = asyncio.run(
        _build_process_request_from_form(request, "job-abs")  # type: ignore[arg-type]
    )

    inputs_dir = (tmp_path / "job-abs" / "inputs").resolve()
    assert process_request.input_path == str(inputs_dir)
    assert (inputs_dir / "etc" / "passwd").exists()


@pytest.mark.unit
def test_build_process_request_from_form_sanitizes_traversal_upload_filename(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(jobs_router_module, "JOBS_HOME", tmp_path)
    monkeypatch.setattr(jobs_router_module, "UploadFile", DummyUpload)

    request = MultipartRequestStub(
        values={},
        files=[DummyUpload(filename="../../traversal/../safe.txt", payload=b"x")],
    )
    process_request = asyncio.run(
        _build_process_request_from_form(request, "job-traversal")  # type: ignore[arg-type]
    )

    inputs_dir = (tmp_path / "job-traversal" / "inputs").resolve()
    assert process_request.input_path == str(inputs_dir)
    assert (inputs_dir / "traversal" / "safe.txt").exists()


@pytest.mark.unit
def test_build_process_request_from_form_enforces_upload_limits(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(jobs_router_module, "JOBS_HOME", tmp_path)
    monkeypatch.setattr(jobs_router_module, "UploadFile", DummyUpload)
    monkeypatch.setenv("DATA_EXTRACT_API_MAX_UPLOAD_FILE_BYTES", "5")

    files = [DummyUpload(filename="nested/large.txt", payload=b"hello-world")]
    request = MultipartRequestStub(
        values={"chunk_size": "64", "output_format": "json"}, files=files
    )

    with pytest.raises(Exception) as exc_info:
        asyncio.run(_build_process_request_from_form(request, "job-125"))  # type: ignore[arg-type]
    assert getattr(exc_info.value, "status_code", None) == 413


@pytest.mark.unit
def test_enqueue_process_job_returns_503_when_queue_is_full(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_enqueue(_request: ProcessJobRequest, job_id: str | None = None) -> str:
        raise QueueCapacityError(
            "Queue backlog is at capacity (1000); try again later.",
            retry_after_seconds=6,
            reason="queue_full",
        )

    monkeypatch.setattr(jobs_router_module.runtime, "enqueue_process", fake_enqueue)
    request = JsonRequestStub(
        {
            "input_path": str(jobs_router_module.JOBS_HOME / "source"),
            "output_format": "json",
            "chunk_size": 128,
        }
    )

    with pytest.raises(Exception) as exc_info:
        asyncio.run(enqueue_process_job(request))  # type: ignore[arg-type]
    assert getattr(exc_info.value, "status_code", None) == 503
    assert getattr(exc_info.value, "headers", {}).get("Retry-After") == "6"
    assert "Retry after ~6s" in str(getattr(exc_info.value, "detail", ""))


@pytest.mark.unit
def test_build_process_request_from_form_supports_semantic_fields(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(jobs_router_module, "JOBS_HOME", tmp_path)
    monkeypatch.setattr(jobs_router_module, "UploadFile", DummyUpload)

    request = MultipartRequestStub(
        values={
            "input_path": str(tmp_path / "source"),
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
def test_enqueue_process_job_rejects_disallowed_input_path(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    monkeypatch.chdir(workspace)
    monkeypatch.delenv("DATA_EXTRACT_API_ALLOWED_INPUT_ROOTS", raising=False)

    disallowed_input_path = tmp_path / "outside" / "data"
    request = JsonRequestStub(
        {
            "input_path": str(disallowed_input_path),
            "output_format": "json",
            "chunk_size": 128,
        }
    )

    with pytest.raises(Exception) as exc_info:
        asyncio.run(enqueue_process_job(request))  # type: ignore[arg-type]

    assert getattr(exc_info.value, "status_code", None) == 400
    assert "not allowed" in str(getattr(exc_info.value, "detail", ""))


@pytest.mark.unit
def test_enqueue_process_job_accepts_input_path_under_default_cwd_root(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    monkeypatch.chdir(workspace)
    monkeypatch.delenv("DATA_EXTRACT_API_ALLOWED_INPUT_ROOTS", raising=False)

    captured: dict[str, object] = {}

    def fake_enqueue(request: ProcessJobRequest, job_id: str | None = None) -> str:
        captured["request"] = request
        return job_id or "fallback"

    monkeypatch.setattr(jobs_router_module.runtime, "enqueue_process", fake_enqueue)
    request = JsonRequestStub(
        {
            "input_path": "inputs/data",
            "output_format": "json",
            "chunk_size": 128,
        }
    )
    response = asyncio.run(enqueue_process_job(request))  # type: ignore[arg-type]

    assert response.status == "queued"
    assert isinstance(captured["request"], ProcessJobRequest)
    assert captured["request"].input_path == str((workspace / "inputs" / "data").resolve())


@pytest.mark.unit
def test_build_process_request_from_form_accepts_input_path_under_explicit_allow_root(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    workspace = tmp_path / "workspace"
    allowed_root = tmp_path / "allowed-root"
    workspace.mkdir(parents=True, exist_ok=True)
    allowed_root.mkdir(parents=True, exist_ok=True)

    monkeypatch.chdir(workspace)
    monkeypatch.setenv("DATA_EXTRACT_API_ALLOWED_INPUT_ROOTS", str(allowed_root))

    request = MultipartRequestStub(
        values={"input_path": str(allowed_root / "incoming" / "payload.json")},
        files=[],
    )
    process_request = asyncio.run(
        _build_process_request_from_form(request, "job-allow-root")  # type: ignore[arg-type]
    )

    assert process_request.input_path == str((allowed_root / "incoming" / "payload.json").resolve())


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
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
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
        observed["queued_events"] = [
            event.event_type for event in events if event.event_type == "queued"
        ]
        observed["queued_messages"] = [
            event.message for event in events if event.event_type == "queued"
        ]

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
def test_retry_job_failures_returns_503_when_queue_is_full(
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

    job_id = "retry-job-503"
    session_id = "sess-503"
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
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
        )
        db.commit()

    def fake_enqueue_retry(*, job_id: str, request: Any) -> None:
        raise QueueCapacityError(
            "Queue backlog is at capacity (1000); try again later.",
            retry_after_seconds=4,
            reason="queue_full",
        )

    monkeypatch.setattr(jobs_router_module, "SessionLocal", test_session_local)
    monkeypatch.setattr(jobs_router_module.runtime, "enqueue_retry", fake_enqueue_retry)

    with pytest.raises(Exception) as exc_info:
        retry_job_failures(job_id)
    assert getattr(exc_info.value, "status_code", None) == 503
    assert getattr(exc_info.value, "headers", {}).get("Retry-After") == "4"
    assert "Retry after ~4s" in str(getattr(exc_info.value, "detail", ""))
    with test_session_local() as db:
        job = db.get(Job, job_id)
        events = list(
            db.scalars(
                select(JobEvent)
                .where(JobEvent.job_id == job_id)
                .order_by(JobEvent.event_time.asc())
            )
        )
    assert job is not None
    assert job.status == "partial"
    assert json.loads(job.result_payload or "{}") == {"session_id": session_id}
    assert [event.event_type for event in events if event.event_type == "queued"] == []


@pytest.mark.unit
def test_job_artifact_list_and_download(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
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
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
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


@pytest.mark.unit
def test_list_jobs_supports_pagination(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    db_path = tmp_path / "jobs.db"
    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
        future=True,
    )
    test_session_local = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    Base.metadata.create_all(bind=engine)

    with test_session_local() as db:
        for index in range(5):
            db.add(
                Job(
                    id=f"job-{index}",
                    status="completed",
                    input_path=str(tmp_path / "input"),
                    output_dir=str(tmp_path / "output"),
                    requested_format="json",
                    chunk_size=512,
                    request_payload="{}",
                    result_payload="{}",
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                )
            )
        db.commit()

    monkeypatch.setattr(jobs_router_module, "SessionLocal", test_session_local)

    jobs_page = list_jobs(limit=2, offset=1)
    assert len(jobs_page) == 2


@pytest.mark.unit
def test_get_job_exposes_dispatch_and_artifact_sync_fields(
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

    with test_session_local() as db:
        db.add(
            Job(
                id="job-detail-1",
                status="queued",
                input_path=str(tmp_path / "input"),
                output_dir=str(tmp_path / "output"),
                requested_format="json",
                chunk_size=512,
                request_payload="{}",
                result_payload="{}",
                dispatch_state="pending_dispatch",
                dispatch_attempts=2,
                artifact_sync_state="failed",
                artifact_sync_attempts=3,
                artifact_sync_error="disk full",
                result_checksum="abc123",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
        )
        db.commit()

    monkeypatch.setattr(jobs_router_module, "SessionLocal", test_session_local)
    payload = get_job("job-detail-1", file_limit=1000, event_limit=1000)

    assert payload["dispatch_state"] == "pending_dispatch"
    assert payload["dispatch_attempts"] == 2
    assert payload["artifact_sync_state"] == "failed"
    assert payload["artifact_sync_attempts"] == 3
    assert payload["artifact_sync_error"] == "disk full"
    assert payload["result_checksum"] == "abc123"
