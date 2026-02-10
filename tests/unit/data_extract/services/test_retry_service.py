from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pytest

from data_extract.cli.session import SessionManager
from data_extract.contracts import JobStatus
from data_extract.contracts import RetryRequest
from data_extract.services import RetryService


pytestmark = [pytest.mark.unit]


def test_retry_service_loads_archived_failed_session(tmp_path: Path) -> None:
    source_dir = tmp_path / "source"
    output_dir = tmp_path / "output"
    source_dir.mkdir()
    output_dir.mkdir()

    failed_file = source_dir / "needs_retry.txt"
    failed_file.write_text("retry me", encoding="utf-8")

    manager = SessionManager(work_dir=tmp_path)
    manager.start_session(
        source_dir=source_dir,
        total_files=1,
        configuration={
            "output_path": str(output_dir),
            "format": "json",
        },
    )
    assert manager.session_id is not None
    session_id = manager.session_id

    manager.record_failed_file(
        file_path=failed_file,
        error_type="RuntimeError",
        error_message="Simulated failure",
    )
    manager.save_session()
    manager.complete_session()

    result = RetryService().run_retry(
        RetryRequest(session=session_id, non_interactive=True),
        work_dir=tmp_path,
    )

    assert result.processed_count == 1
    assert result.failed_count == 0
    assert (output_dir / "needs_retry.json").exists()


def test_retry_service_uses_canonical_session_payload_when_legacy_missing(tmp_path: Path) -> None:
    os.environ["DATA_EXTRACT_UI_HOME"] = str(tmp_path / "ui-home")
    from data_extract.api.database import SessionLocal, init_database
    from data_extract.api.models import Job

    init_database()

    source_dir = tmp_path / "source-canonical"
    output_dir = tmp_path / "output-canonical"
    source_dir.mkdir()
    output_dir.mkdir()

    failed_file = source_dir / "canonical_retry.txt"
    failed_file.write_text("retry via canonical session", encoding="utf-8")

    session_id = "sess-canonical"
    result_payload = {
        "job_id": "job-canonical",
        "status": JobStatus.PARTIAL.value,
        "total_files": 1,
        "processed_count": 0,
        "failed_count": 1,
        "output_dir": str(output_dir),
        "session_id": session_id,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "failed_files": [
            {
                "path": str(failed_file),
                "error_type": "RuntimeError",
                "error_message": "Simulated failure",
                "retry_count": 0,
            }
        ],
    }
    with SessionLocal() as db:
        db.add(
            Job(
                id=str(uuid.uuid4())[:12],
                status=JobStatus.PARTIAL.value,
                input_path=str(source_dir),
                output_dir=str(output_dir),
                requested_format="json",
                chunk_size=512,
                session_id=session_id,
                request_payload="{}",
                result_payload=json.dumps(result_payload),
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
        )
        db.commit()

    result = RetryService().run_retry(RetryRequest(session=session_id, non_interactive=True))

    assert result.processed_count == 1
    assert result.failed_count == 0
    assert (output_dir / "canonical_retry.json").exists()
