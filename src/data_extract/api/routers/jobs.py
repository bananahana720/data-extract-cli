"""Job management API routes."""

from __future__ import annotations

import json
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Body, HTTPException, Request, UploadFile
from pydantic import BaseModel
from sqlalchemy import select

from data_extract.api.database import JOBS_HOME, SessionLocal
from data_extract.api.models import Job, JobEvent, JobFile
from data_extract.api.state import runtime
from data_extract.contracts import ProcessJobRequest, RetryRequest

router = APIRouter(prefix="/api/v1/jobs", tags=["jobs"])


class EnqueueJobResponse(BaseModel):
    """Queue response payload."""

    job_id: str
    status: str


class CleanupResponse(BaseModel):
    """Cleanup response payload."""

    job_id: str
    removed: bool


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _to_int(value: Any, default: int) -> int:
    if value is None or value == "":
        return default
    return int(value)


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


async def _build_process_request_from_form(request: Request, job_id: str) -> ProcessJobRequest:
    form = await request.form()
    uploaded_files = [
        entry
        for entry in form.getlist("files")
        if isinstance(entry, UploadFile) and entry.filename
    ]

    input_path = _optional_str(form.get("input_path"))
    if not uploaded_files and not input_path:
        raise HTTPException(status_code=400, detail="Provide files upload or input_path")

    if uploaded_files:
        inputs_dir = JOBS_HOME / job_id / "inputs"
        inputs_dir.mkdir(parents=True, exist_ok=True)

        for upload in uploaded_files:
            raw_path = Path(str(upload.filename).replace("\\", "/"))
            safe_parts = [part for part in raw_path.parts if part not in {"", ".", ".."}]
            if not safe_parts:
                continue
            destination = inputs_dir.joinpath(*safe_parts)
            destination.parent.mkdir(parents=True, exist_ok=True)
            payload = await upload.read()
            destination.write_bytes(payload)

        input_path = str(inputs_dir)

    if not input_path:
        raise HTTPException(status_code=400, detail="No usable input_path provided")

    try:
        return ProcessJobRequest(
            input_path=input_path,
            output_format=str(form.get("output_format") or "json"),
            chunk_size=_to_int(form.get("chunk_size"), 512),
            recursive=_to_bool(form.get("recursive")),
            incremental=_to_bool(form.get("incremental")),
            force=_to_bool(form.get("force")),
            resume=_to_bool(form.get("resume")),
            resume_session=_optional_str(form.get("resume_session")),
            preset=_optional_str(form.get("preset")),
            idempotency_key=_optional_str(form.get("idempotency_key")),
            non_interactive=True,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid numeric input: {exc}") from exc


@router.post("/process", response_model=EnqueueJobResponse)
async def enqueue_process_job(
    request: Request,
    process_request: ProcessJobRequest | None = Body(default=None),
) -> EnqueueJobResponse:
    """Queue a new processing job from JSON payload or multipart upload."""
    content_type = request.headers.get("content-type", "")
    job_id = str(uuid.uuid4())[:12]
    if not isinstance(process_request, ProcessJobRequest):
        process_request = None

    if "multipart/form-data" in content_type:
        process_request = await _build_process_request_from_form(request, job_id)
    else:
        if process_request is None:
            try:
                payload = await request.json()
            except Exception as exc:
                raise HTTPException(status_code=400, detail=f"Invalid JSON payload: {exc}") from exc
            process_request = ProcessJobRequest(**payload)
    if process_request is None:
        raise HTTPException(status_code=400, detail="Missing process request payload")

    queued_job_id = runtime.enqueue_process(process_request, job_id=job_id)
    return EnqueueJobResponse(job_id=queued_job_id, status="queued")


@router.get("")
def list_jobs() -> list[dict[str, Any]]:
    """List jobs with basic summary fields."""
    with SessionLocal() as db:
        jobs = list(db.scalars(select(Job).order_by(Job.created_at.desc())))

    output = []
    for job in jobs:
        output.append(
            {
                "job_id": job.id,
                "status": job.status,
                "input_path": job.input_path,
                "output_dir": job.output_dir,
                "created_at": job.created_at,
                "started_at": job.started_at,
                "finished_at": job.finished_at,
                "session_id": job.session_id,
            }
        )
    return output


@router.get("/{job_id}")
def get_job(job_id: str) -> dict[str, Any]:
    """Return full job detail with files and events."""
    with SessionLocal() as db:
        job = db.get(Job, job_id)
        if not job:
            raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")

        files = list(db.scalars(select(JobFile).where(JobFile.job_id == job_id)))
        events = list(
            db.scalars(select(JobEvent).where(JobEvent.job_id == job_id).order_by(JobEvent.event_time))
        )

    return {
        "job_id": job.id,
        "status": job.status,
        "input_path": job.input_path,
        "output_dir": job.output_dir,
        "requested_format": job.requested_format,
        "chunk_size": job.chunk_size,
        "request_hash": job.request_hash,
        "artifact_dir": job.artifact_dir,
        "created_at": job.created_at,
        "started_at": job.started_at,
        "finished_at": job.finished_at,
        "updated_at": job.updated_at,
        "session_id": job.session_id,
        "request_payload": json.loads(job.request_payload or "{}"),
        "result_payload": json.loads(job.result_payload or "{}"),
        "files": [
            {
                "source_path": file.source_path,
                "output_path": file.output_path,
                "status": file.status,
                "chunk_count": file.chunk_count,
                "retry_count": file.retry_count,
                "error_type": file.error_type,
                "error_message": file.error_message,
            }
            for file in files
        ],
        "events": [
            {
                "event_type": event.event_type,
                "message": event.message,
                "payload": json.loads(event.payload or "{}"),
                "event_time": event.event_time,
            }
            for event in events
        ],
    }


@router.post("/{job_id}/retry-failures", response_model=EnqueueJobResponse)
def retry_job_failures(job_id: str) -> EnqueueJobResponse:
    """Queue retry for the failed files of a completed/partial job."""
    with SessionLocal() as db:
        job = db.get(Job, job_id)
        if not job:
            raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")

        result_payload = json.loads(job.result_payload or "{}")
        session_id = result_payload.get("session_id") or job.session_id

        if not session_id:
            raise HTTPException(status_code=400, detail="Job has no session context for retry")

        job.status = "queued"
        job.started_at = None
        job.finished_at = None
        job.updated_at = datetime.utcnow()
        db.add(
            JobEvent(
                job_id=job_id,
                event_type="queued",
                message="Retry queued",
                payload="{}",
                event_time=datetime.utcnow(),
            )
        )
        db.commit()

    retry_request = RetryRequest(session=session_id, last=False, non_interactive=True)
    runtime.enqueue_retry(job_id=job_id, request=retry_request)

    return EnqueueJobResponse(job_id=job_id, status="queued")


@router.delete("/{job_id}/artifacts", response_model=CleanupResponse)
def cleanup_job_artifacts(job_id: str) -> CleanupResponse:
    """Delete persisted filesystem artifacts for a job."""
    with SessionLocal() as db:
        job = db.get(Job, job_id)
        if not job:
            raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")

        job_dir = JOBS_HOME / job_id
        removed = False
        if job_dir.exists():
            shutil.rmtree(job_dir)
            removed = True

        db.add(
            JobEvent(
                job_id=job_id,
                event_type="cleanup",
                message="Job artifacts cleaned",
                payload=json.dumps({"removed": removed}),
                event_time=datetime.utcnow(),
            )
        )
        db.commit()

    return CleanupResponse(job_id=job_id, removed=removed)
