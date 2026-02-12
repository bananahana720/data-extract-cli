"""Session read helpers for CLI/API."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, cast

from data_extract.contracts import SessionSummary


def _session_dir(work_dir: Path) -> Path:
    return work_dir / ".data-extract-session"


def _session_files(work_dir: Path) -> list[Path]:
    session_dir = _session_dir(work_dir)
    if not session_dir.exists():
        return []

    active = list(session_dir.glob("session-*.json"))
    archived_dir = session_dir / "archive"
    archived = list(archived_dir.glob("session-*.json")) if archived_dir.exists() else []
    return [path for path in active + archived if path.suffix == ".json"]


def list_session_summaries(work_dir: Path) -> list[SessionSummary]:
    """List session summaries from filesystem session store."""
    summaries = []
    for session_file in _session_files(work_dir):
        try:
            state = json.loads(session_file.read_text())
            stats = state.get("statistics", {})
            updated_at = state.get("updated_at")
            if not updated_at:
                continue
            summaries.append(
                SessionSummary(
                    session_id=state.get("session_id", "unknown"),
                    status=state.get("status", "unknown"),
                    source_directory=state.get("source_directory", ""),
                    total_files=stats.get("total_files", state.get("total_files", 0)),
                    processed_count=stats.get("processed_count", 0),
                    failed_count=stats.get("failed_count", 0),
                    updated_at=datetime.fromisoformat(updated_at),
                )
            )
        except Exception:
            continue

    return sorted(summaries, key=lambda s: s.updated_at, reverse=True)


def load_session_details(work_dir: Path, session_id: str) -> Optional[dict[str, Any]]:
    """Load raw session payload by id."""
    candidates = [
        _session_dir(work_dir) / f"session-{session_id}.json",
        _session_dir(work_dir) / "archive" / f"session-{session_id}.json",
    ]
    for session_file in candidates:
        if not session_file.exists():
            continue
        try:
            payload = json.loads(session_file.read_text())
            return cast(dict[str, Any], payload)
        except json.JSONDecodeError:
            continue
    return None
