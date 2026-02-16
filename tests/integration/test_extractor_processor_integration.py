"""Integration tests for extract -> normalize -> chunk behavior."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from data_extract.services.pipeline_service import PipelineService

pytestmark = [pytest.mark.P1, pytest.mark.integration]


def _write_text(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_normalize_collapses_whitespace_before_chunking(tmp_path: Path) -> None:
    source_file = _write_text(
        tmp_path / "messy.txt",
        "alpha    beta\r\n\r\n\r\ngamma\t\tdelta",
    )

    run = PipelineService().process_files(
        files=[source_file],
        output_dir=tmp_path / "output",
        output_format="json",
        chunk_size=10,
        pipeline_profile="legacy",
        include_semantic=False,
        source_root=tmp_path,
    )

    assert len(run.processed) == 1
    output_payload = _load_json(tmp_path / "output" / "messy.json")

    combined_text = " ".join(chunk["text"] for chunk in output_payload["chunks"])
    assert "  " not in combined_text
    assert "\r" not in combined_text
    assert output_payload["chunks"][0]["text"].startswith("alpha beta")


def test_chunk_size_controls_chunk_count(tmp_path: Path) -> None:
    source_file = _write_text(
        tmp_path / "words.txt",
        "one two three four five six seven eight nine ten",
    )

    run = PipelineService().process_files(
        files=[source_file],
        output_dir=tmp_path / "output",
        output_format="json",
        chunk_size=3,
        pipeline_profile="legacy",
        include_semantic=False,
        source_root=tmp_path,
    )

    payload = _load_json(tmp_path / "output" / "words.json")

    assert len(run.processed) == 1
    assert run.processed[0].chunk_count == 4
    assert len(payload["chunks"]) == 4
    assert payload["chunks"][-1]["word_count"] == 1


def test_empty_input_emits_placeholder_chunk(tmp_path: Path) -> None:
    source_file = _write_text(tmp_path / "empty.txt", "")

    run = PipelineService().process_files(
        files=[source_file],
        output_dir=tmp_path / "output",
        output_format="json",
        chunk_size=8,
        pipeline_profile="legacy",
        include_semantic=False,
        source_root=tmp_path,
    )

    payload = _load_json(tmp_path / "output" / "empty.json")

    assert len(run.processed) == 1
    assert run.processed[0].chunk_count == 1
    assert payload["chunks"][0]["text"] == ""
    assert payload["chunks"][0]["token_count"] == 0
