from __future__ import annotations

import json
from pathlib import Path

from data_extract.core.models import Chunk
from data_extract.services.chunk_io import chunk_to_dict, load_chunks


def test_load_chunks_reads_utf8_sig_and_upcasts_schema(tmp_path: Path) -> None:
    payload = {
        "chunks": [
            {
                "id": "doc-1_001",
                "text": "alpha beta gamma",
                "metadata": {"source_file": "source/a.txt"},
            }
        ]
    }
    file_path = tmp_path / "chunks.json"
    file_path.write_text(json.dumps(payload), encoding="utf-8-sig")

    chunks = load_chunks(file_path)

    assert len(chunks) == 1
    chunk = chunks[0]
    assert chunk.id == "doc-1_001"
    assert chunk.text == "alpha beta gamma"
    assert chunk.word_count == 3
    assert chunk.token_count == 3
    assert chunk.document_id == ""


def test_chunk_to_dict_emits_enriched_schema() -> None:
    chunk = Chunk(
        id="x_001",
        text="hello world",
        document_id="x",
        position_index=0,
        token_count=2,
        word_count=2,
        entities=[],
        section_context="",
        quality_score=0.9,
        readability_scores={"flesch": 65.0},
        metadata={"source_file": "doc.txt"},
    )

    payload = chunk_to_dict(chunk)

    assert payload["id"] == "x_001"
    assert payload["document_id"] == "x"
    assert payload["token_count"] == 2
    assert payload["word_count"] == 2
    assert payload["quality_score"] == 0.9
    assert payload["metadata"]["source_file"] == "doc.txt"
