from __future__ import annotations

from pathlib import Path

from data_extract.contracts import ProcessJobRequest
from data_extract.services import JobService


def test_run_process_generates_real_output_for_txt(tmp_path: Path) -> None:
    source_dir = tmp_path / "source"
    output_dir = tmp_path / "output"
    source_dir.mkdir()
    sample_file = source_dir / "sample.txt"
    sample_file.write_text("alpha beta gamma", encoding="utf-8")

    request = ProcessJobRequest(
        input_path=str(source_dir),
        output_path=str(output_dir),
        output_format="json",
        chunk_size=16,
    )

    result = JobService().run_process(request, work_dir=tmp_path)

    assert result.processed_count == 1
    assert result.failed_count == 0
    assert (output_dir / "sample.json").exists()
    assert result.request_hash is not None


def test_run_process_avoids_output_collisions_for_duplicate_stems(tmp_path: Path) -> None:
    source_dir = tmp_path / "source-dupes"
    output_dir = tmp_path / "output-dupes"
    (source_dir / "a").mkdir(parents=True)
    (source_dir / "b").mkdir(parents=True)
    (source_dir / "a" / "same.txt").write_text("alpha", encoding="utf-8")
    (source_dir / "b" / "same.txt").write_text("beta", encoding="utf-8")

    request = ProcessJobRequest(
        input_path=str(source_dir),
        output_path=str(output_dir),
        output_format="json",
        chunk_size=16,
        recursive=True,
    )
    result = JobService().run_process(request, work_dir=tmp_path)

    assert result.processed_count == 2
    assert (output_dir / "a" / "same.json").exists()
    assert (output_dir / "b" / "same.json").exists()
    assert all(outcome.source_key for outcome in result.processed_files)
