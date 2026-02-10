from __future__ import annotations

from pathlib import Path

from data_extract.cli.session import SessionManager
from data_extract.contracts import RetryRequest
from data_extract.services import RetryService


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
