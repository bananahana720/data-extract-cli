"""Integration tests for OutputWriter formatter workflows."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from data_extract.core.models import Chunk
from data_extract.output.writer import OutputWriter

pytestmark = [pytest.mark.P1, pytest.mark.integration]


def _chunk(chunk_id: str, text: str, source_file: str) -> Chunk:
    words = text.split()
    return Chunk(
        id=chunk_id,
        text=text,
        document_id=Path(source_file).stem,
        position_index=0,
        token_count=len(words),
        word_count=len(words),
        entities=[],
        section_context="",
        quality_score=1.0,
        readability_scores={},
        metadata={"source_file": source_file, "entity_tags": []},
    )


def test_output_writer_json_includes_source_documents(tmp_path: Path) -> None:
    chunks = [
        _chunk("chunk-001", "alpha beta", "doc-a.txt"),
        _chunk("chunk-002", "gamma delta", "doc-b.txt"),
    ]
    output_file = tmp_path / "chunks.json"

    result = OutputWriter().write(chunks, output_file, format_type="json")

    assert result.chunk_count == 2

    payload = json.loads(output_file.read_text(encoding="utf-8-sig"))
    assert payload["metadata"]["chunk_count"] == 2
    assert payload["metadata"]["source_documents"] == ["doc-a.txt", "doc-b.txt"]
    assert "alpha beta" in payload["content"]


def test_output_writer_txt_per_chunk_uses_source_stems(tmp_path: Path) -> None:
    chunks = [
        _chunk("chunk-001", "first", "alpha.txt"),
        _chunk("chunk-002", "second", "alpha.txt"),
        _chunk("chunk-003", "third", "beta.txt"),
    ]
    output_dir = tmp_path / "per-chunk"

    result = OutputWriter().write(chunks, output_dir, format_type="txt", per_chunk=True)

    assert result.chunk_count == 3
    assert sorted(path.name for path in output_dir.glob("*.txt")) == [
        "alpha_chunk_001.txt",
        "alpha_chunk_002.txt",
        "beta_chunk_001.txt",
    ]


def test_output_writer_csv_writes_header_and_rows(tmp_path: Path) -> None:
    chunks = [
        _chunk("chunk-001", "alpha beta", "doc-a.txt"),
        _chunk("chunk-002", "gamma delta", "doc-b.txt"),
    ]
    output_file = tmp_path / "chunks.csv"

    result = OutputWriter().write(chunks, output_file, format_type="csv")

    assert result.chunk_count == 2

    with output_file.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.reader(handle))

    assert rows[0][0] == "chunk_id"
    assert rows[1][0] == "chunk-001"
    assert rows[2][0] == "chunk-002"
    assert len(rows) == 3
