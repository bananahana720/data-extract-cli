from __future__ import annotations

from pathlib import Path

from data_extract.services import StatusService


def test_status_service_detects_and_cleans_orphaned_outputs(tmp_path: Path) -> None:
    source_dir = tmp_path / "source"
    output_dir = tmp_path / "output"
    source_dir.mkdir()
    output_dir.mkdir()

    (source_dir / "valid.txt").write_text("ok", encoding="utf-8")
    orphan = output_dir / "orphan.json"
    orphan.write_text("{}", encoding="utf-8")

    service = StatusService()
    status = service.get_status(source_dir=source_dir, output_dir=output_dir, cleanup=False)

    assert status["orphaned_count"] == 1
    assert str(orphan) in status["orphaned_outputs"]

    cleaned = service.get_status(source_dir=source_dir, output_dir=output_dir, cleanup=True)
    assert cleaned["cleaned_count"] == 1
    assert not orphan.exists()
