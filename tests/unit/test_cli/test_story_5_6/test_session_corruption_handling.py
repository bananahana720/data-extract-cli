"""Targeted corruption-handling tests for SessionManager.load_session."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from data_extract.cli.session import SessionCorruptedError, SessionManager

pytestmark = [pytest.mark.unit, pytest.mark.story_5_6]


def test_load_session_raises_corruption_error_for_missing_required_keys(tmp_path: Path) -> None:
    work_dir = tmp_path
    session_dir = work_dir / SessionManager.SESSION_DIR
    session_dir.mkdir(parents=True)
    session_id = "missing-required"
    session_file = session_dir / f"session-{session_id}.json"
    session_file.write_text(
        json.dumps(
            {
                "status": "in_progress",
                "source_directory": "/docs",
                "started_at": "2026-01-01T00:00:00",
                "updated_at": "2026-01-01T00:00:00",
            }
        ),
        encoding="utf-8",
    )

    manager = SessionManager(work_dir=work_dir)

    with pytest.raises(SessionCorruptedError, match="missing required keys"):
        manager.load_session(session_id)


def test_load_session_raises_corruption_error_for_invalid_timestamp(tmp_path: Path) -> None:
    work_dir = tmp_path
    session_dir = work_dir / SessionManager.SESSION_DIR
    session_dir.mkdir(parents=True)
    session_id = "invalid-time"
    session_file = session_dir / f"session-{session_id}.json"
    session_file.write_text(
        json.dumps(
            {
                "session_id": session_id,
                "status": "in_progress",
                "source_directory": "/docs",
                "started_at": "not-a-datetime",
                "updated_at": "2026-01-01T00:00:00",
                "statistics": {"total_files": 1, "processed_count": 0, "failed_count": 0},
            }
        ),
        encoding="utf-8",
    )

    manager = SessionManager(work_dir=work_dir)

    with pytest.raises(SessionCorruptedError, match="invalid ISO datetime"):
        manager.load_session(session_id)
