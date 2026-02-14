from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("DATA_EXTRACT_UI_HOME", "/tmp/data-extract-ui-tests")

from data_extract.api.database import Base
from data_extract.api.models import Job, SessionRecord
from data_extract.api.state import ApiRuntime


@pytest.mark.unit
def test_upsert_session_uses_result_payload_when_session_file_missing(
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

    with test_session_local() as db:
        ApiRuntime._upsert_session(
            db,
            session_id="sess-payload",
            input_path=str(tmp_path / "input"),
            result_payload={
                "status": "completed",
                "total_files": 3,
                "processed_count": 2,
                "failed_count": 1,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            },
            projection_source="result_payload",
        )
        db.commit()

    monkeypatch.setattr(state_module, "SessionLocal", test_session_local)
    with test_session_local() as db:
        record = db.get(SessionRecord, "sess-payload")

    assert record is not None
    assert record.status == "completed"
    assert record.total_files == 3
    assert record.processed_count == 2
    assert record.failed_count == 1
    assert record.projection_source == "result_payload"


@pytest.mark.unit
def test_startup_session_reconciliation_rehydrates_session_projection(
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

    updated_at = datetime.now(timezone.utc)
    with test_session_local() as db:
        db.add(
            Job(
                id="job-session-1",
                status="completed",
                input_path=str(tmp_path / "inputs"),
                output_dir=str(tmp_path / "outputs"),
                requested_format="json",
                chunk_size=512,
                request_payload="{}",
                result_payload=json.dumps(
                    {
                        "status": "completed",
                        "total_files": 5,
                        "processed_count": 4,
                        "failed_count": 1,
                        "updated_at": updated_at.isoformat(),
                    }
                ),
                session_id="sess-rehydrate",
                created_at=updated_at,
                updated_at=updated_at,
            )
        )
        db.commit()

    monkeypatch.setattr(state_module, "SessionLocal", test_session_local)
    runtime = ApiRuntime()
    monkeypatch.setattr(runtime, "_write_job_log", lambda *args, **kwargs: None)

    runtime._reconcile_session_projections()

    with test_session_local() as db:
        record = db.get(SessionRecord, "sess-rehydrate")
        count = len(list(db.scalars(select(SessionRecord))))

    assert count == 1
    assert record is not None
    assert record.status == "completed"
    assert record.total_files == 5
    assert record.processed_count == 4
    assert record.failed_count == 1
    assert record.projection_source == "startup_reconcile"
