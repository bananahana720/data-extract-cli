"""Session API routes."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from data_extract.api.database import SessionLocal
from data_extract.api.models import SessionRecord
from data_extract.contracts import SessionSummary
from data_extract.services.session_service import list_session_summaries, load_session_details

router = APIRouter(prefix="/api/v1/sessions", tags=["sessions"])


@router.get("", response_model=list[SessionSummary])
def list_sessions() -> list[SessionSummary]:
    """List known session summaries."""
    with SessionLocal() as db:
        records = list(db.scalars(select(SessionRecord).order_by(SessionRecord.updated_at.desc())))

    if records:
        return [
            SessionSummary(
                session_id=record.session_id,
                status=record.status,
                source_directory=record.source_directory,
                total_files=record.total_files,
                processed_count=record.processed_count,
                failed_count=record.failed_count,
                updated_at=record.updated_at,
            )
            for record in records
        ]

    return list_session_summaries(Path.cwd())


@router.get("/{session_id}")
def get_session(session_id: str) -> dict[str, Any]:
    """Return detailed session payload."""
    details = None
    with SessionLocal() as db:
        record = db.get(SessionRecord, session_id)
        if record:
            details = load_session_details(Path(record.source_directory), session_id)

    if details is None:
        details = load_session_details(Path.cwd(), session_id)
    if details is None:
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")
    return details
