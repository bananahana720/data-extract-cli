"""Integration checks for cross-format output consistency."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from data_extract.services.pipeline_service import PipelineService

pytestmark = [pytest.mark.P1, pytest.mark.integration, pytest.mark.cross_format]


def _write_text(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def _run_pipeline(source_file: Path, output_dir: Path, output_format: str, chunk_size: int) -> Path:
    run = PipelineService().process_files(
        files=[source_file],
        output_dir=output_dir,
        output_format=output_format,
        chunk_size=chunk_size,
        include_semantic=False,
        pipeline_profile="legacy",
        source_root=source_file.parent,
    )

    assert len(run.processed) == 1
    assert run.failed == []
    return run.processed[0].output_path


def test_chunk_counts_match_across_json_txt_and_csv(tmp_path: Path) -> None:
    source_file = _write_text(
        tmp_path / "cross-format.txt",
        "one two three four five six seven eight nine",
    )

    json_output = _run_pipeline(source_file, tmp_path / "json", "json", chunk_size=3)
    txt_output = _run_pipeline(source_file, tmp_path / "txt", "txt", chunk_size=3)
    csv_output = _run_pipeline(source_file, tmp_path / "csv", "csv", chunk_size=3)

    json_count = json.loads(json_output.read_text(encoding="utf-8"))["metadata"]["chunk_count"]
    txt_count = txt_output.read_text(encoding="utf-8-sig").count("━━━ CHUNK")
    with csv_output.open(encoding="utf-8-sig", newline="") as handle:
        csv_count = len(list(csv.reader(handle))) - 1

    assert json_count == txt_count == csv_count == 3


def test_core_text_is_present_in_all_formats(tmp_path: Path) -> None:
    phrase = "compliance evidence ledger"
    source_file = _write_text(
        tmp_path / "content.txt",
        f"{phrase} with deterministic integration coverage",
    )

    json_output = _run_pipeline(source_file, tmp_path / "json", "json", chunk_size=64)
    txt_output = _run_pipeline(source_file, tmp_path / "txt", "txt", chunk_size=64)
    csv_output = _run_pipeline(source_file, tmp_path / "csv", "csv", chunk_size=64)

    json_payload = json.loads(json_output.read_text(encoding="utf-8"))
    txt_payload = txt_output.read_text(encoding="utf-8-sig")
    with csv_output.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.reader(handle))

    assert phrase in json_payload["content"].lower()
    assert phrase in txt_payload.lower()
    assert phrase in rows[1][3].lower()
