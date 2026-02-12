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


def test_status_service_detects_orphans_for_json_txt_csv(tmp_path: Path) -> None:
    source_dir = tmp_path / "source"
    output_dir = tmp_path / "output"
    source_dir.mkdir(parents=True)
    output_dir.mkdir(parents=True)

    (source_dir / "valid.txt").write_text("source", encoding="utf-8")
    (output_dir / "valid.json").write_text("{}", encoding="utf-8")
    (output_dir / "valid.txt").write_text("chunk text", encoding="utf-8")
    (output_dir / "valid.csv").write_text("id,text\n1,chunk", encoding="utf-8")

    orphan_json = output_dir / "orphan.json"
    orphan_txt = output_dir / "orphan.txt"
    orphan_csv = output_dir / "orphan.csv"
    orphan_json.write_text("{}", encoding="utf-8")
    orphan_txt.write_text("orphan", encoding="utf-8")
    orphan_csv.write_text("id,text\n9,orphan", encoding="utf-8")

    status = StatusService().get_status(source_dir=source_dir, output_dir=output_dir, cleanup=False)

    assert status["orphaned_count"] == 3
    assert status["cleaned_count"] == 0
    assert str(orphan_json) in status["orphaned_outputs"]
    assert str(orphan_txt) in status["orphaned_outputs"]
    assert str(orphan_csv) in status["orphaned_outputs"]
