from __future__ import annotations

from pathlib import Path

import pytest

from data_extract.core.models import Chunk
from data_extract.services.semantic_orchestration_service import SemanticOrchestrationService

pytestmark = [pytest.mark.unit]


def _make_chunk(chunk_id: str) -> Chunk:
    return Chunk(
        id=chunk_id,
        text=f"text for {chunk_id}",
        document_id="doc",
        position_index=0,
        token_count=3,
        word_count=3,
        entities=[],
        section_context="",
        quality_score=0.5,
        readability_scores={},
        metadata={},
    )


def test_load_output_chunks_uses_strict_chunk_loading(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output_file = tmp_path / "chunks.json"
    output_file.write_text("{}", encoding="utf-8")

    observed: dict[str, bool] = {}

    def fake_load_chunks(path: Path, *, strict: bool = False) -> list[Chunk]:
        observed["strict"] = strict
        return [_make_chunk("chunk-001"), _make_chunk("chunk-001")]

    monkeypatch.setattr(
        "data_extract.services.semantic_orchestration_service.load_chunks",
        fake_load_chunks,
    )

    chunks = SemanticOrchestrationService._load_output_chunks([output_file])

    assert observed["strict"] is True
    assert [chunk.id for chunk in chunks] == ["chunk-001"]
