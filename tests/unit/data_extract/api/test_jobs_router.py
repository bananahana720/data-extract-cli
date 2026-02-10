from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import Any

import pytest

os.environ.setdefault("DATA_EXTRACT_UI_HOME", "/tmp/data-extract-ui-tests")

from data_extract.api.routers import jobs as jobs_router_module
from data_extract.api.routers.jobs import _build_process_request_from_form, enqueue_process_job
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
