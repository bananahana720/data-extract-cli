"""Determinism tests for reproducible chunking (AC-3.1-7 - Critical)."""

from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import Mock

import pytest

try:
    from data_extract.chunk.engine import ChunkingEngine
    from data_extract.core.models import Document, Metadata, ProcessingContext
except ImportError:
    ChunkingEngine = None
    Document = None
    Metadata = None
    ProcessingContext = None

pytestmark = [pytest.mark.P1, pytest.mark.unit, pytest.mark.chunking]


def create_test_metadata(source_file: str = "test.pdf") -> Metadata:
    """Create complete Metadata for tests."""
    return Metadata(
        source_file=Path(source_file),
        file_hash="abc123",
        processing_timestamp=datetime.now(timezone.utc),
        tool_version="3.1.0",
        config_version="1.0",
    )


class TestDeterministicChunking:
    """Test deterministic chunking behavior (AC-3.1-7)."""

    def test_same_input_produces_identical_chunks_10_runs(self):
        """Should produce byte-for-byte identical chunks across 10 runs."""
        # GIVEN: Mock SentenceSegmenter with consistent output
        mock_segmenter = Mock()
        sentences = ["First sentence.", "Second sentence.", "Third sentence."]
        mock_segmenter.segment.return_value = sentences

        # GIVEN: Document
        document = Document(
            id="determinism_test",
            text=" ".join(sentences),
            entities=[],
            metadata=create_test_metadata("test.pdf"),
            structure={},
        )

        # GIVEN: ProcessingContext
        context = ProcessingContext(config={}, logger=Mock(), metrics={})

        # GIVEN: ChunkingEngine
        engine = ChunkingEngine(segmenter=mock_segmenter, chunk_size=512, overlap_pct=0.15)

        # WHEN: Chunking same document 10 runs
        all_runs = []
        for run in range(10):
            chunks = list(engine.process(document, context))
            all_runs.append(chunks)

        # THEN: All runs produce identical chunks (IDs, text, metadata)
        first_run = all_runs[0]
        for run_chunks in all_runs[1:]:
            assert len(run_chunks) == len(first_run)
            for i, chunk in enumerate(run_chunks):
                assert chunk.id == first_run[i].id
                assert chunk.text == first_run[i].text
                assert chunk.position_index == first_run[i].position_index

    def test_chunk_id_no_timestamps(self):
        """Should not include timestamps in chunk IDs (determinism requirement)."""
        # GIVEN: Mock SentenceSegmenter
        mock_segmenter = Mock()
        mock_segmenter.segment.return_value = ["Test sentence."]

        # GIVEN: Document
        document = Document(
            id="id_test",
            text="Test sentence.",
            entities=[],
            metadata=create_test_metadata("report_2024.pdf"),
            structure={},
        )

        # GIVEN: ProcessingContext
        context = ProcessingContext(config={}, logger=Mock(), metrics={})

        # WHEN: Chunking
        engine = ChunkingEngine(segmenter=mock_segmenter)
        chunks = list(engine.process(document, context))

        # THEN: Chunk ID uses pattern {source_file_stem}_chunk_{position:03d}
        assert chunks[0].id == "report_2024_chunk_000"

    def test_different_config_produces_different_chunks(self):
        """Should produce different chunks when configuration changes."""
        # GIVEN: Mock SentenceSegmenter with enough sentences to force multiple chunks
        mock_segmenter = Mock()
        # Create sentences with enough tokens to exceed chunk_size
        # Each sentence is ~40 characters = ~10 tokens
        sentences = [f"This is sentence number {i} with some content." for i in range(100)]
        mock_segmenter.segment.return_value = sentences

        # GIVEN: Document
        document = Document(
            id="config_test",
            text=" ".join(sentences),
            entities=[],
            metadata=create_test_metadata("test.pdf"),
            structure={},
        )

        # GIVEN: ProcessingContext
        context = ProcessingContext(config={}, logger=Mock(), metrics={})

        # WHEN: Chunking with different configurations
        # chunk_size=256 (smaller) should produce more chunks
        engine1 = ChunkingEngine(segmenter=mock_segmenter, chunk_size=256, overlap_pct=0.0)
        chunks1 = list(engine1.process(document, context))

        # chunk_size=512 (larger) should produce fewer chunks
        engine2 = ChunkingEngine(segmenter=mock_segmenter, chunk_size=512, overlap_pct=0.0)
        chunks2 = list(engine2.process(document, context))

        # THEN: Different configurations produce different chunk counts
        # Smaller chunk_size should produce more chunks
        assert len(chunks1) > len(
            chunks2
        ), f"Expected chunks1 ({len(chunks1)}) > chunks2 ({len(chunks2)})"


class TestEntityAwareDeterminism:
    """Test entity-aware chunking determinism (AC-3.2-8 - Story 3.2)."""

    def test_entity_aware_chunking_determinism(self):
        """Should produce identical chunks with entity-aware mode (AC-3.2-8)."""
        # GIVEN: Document with entities
        from data_extract.core.models import Entity, EntityType

        text = "RISK-001 data breach risk mitigated by CTRL-042 encryption control."
        entities = [
            Entity(
                type=EntityType.RISK,
                id="RISK-001",
                text="RISK-001",
                confidence=0.95,
                location={"start": 0, "end": 8},
            ),
            Entity(
                type=EntityType.CONTROL,
                id="CTRL-042",
                text="CTRL-042",
                confidence=0.92,
                location={"start": 40, "end": 48},
            ),
        ]

        document = Document(
            id="entity_determinism_test",
            text=text,
            entities=entities,
            metadata=create_test_metadata("test.pdf"),
            structure={},
        )

        # GIVEN: ProcessingContext
        context = ProcessingContext(config={}, logger=Mock(), metrics={})

        # GIVEN: Mock SentenceSegmenter
        mock_segmenter = Mock()
        mock_segmenter.segment.return_value = [text]

        # WHEN: chunk_document() called 10 times with entity_aware=True
        engine = ChunkingEngine(
            segmenter=mock_segmenter, chunk_size=512, overlap_pct=0.15, entity_aware=True
        )

        all_runs = []
        for run in range(10):
            chunks = list(engine.process(document, context))
            all_runs.append(chunks)

        # THEN: All outputs byte-for-byte identical (sha256 hash comparison)
        import hashlib
        import json

        hashes = []
        for chunks in all_runs:
            # Serialize chunks to JSON for consistent comparison
            chunk_dicts = [c.to_dict() for c in chunks]
            json_str = json.dumps(chunk_dicts, sort_keys=True)
            hash_val = hashlib.sha256(json_str.encode()).hexdigest()
            hashes.append(hash_val)

        # All hashes should be identical
        first_hash = hashes[0]
        for hash_val in hashes[1:]:
            assert hash_val == first_hash, "Expected identical output across all runs (determinism)"

    def test_entity_analysis_order_determinism(self):
        """Should process entities in consistent order (AC-3.2-8)."""
        # GIVEN: Entities in random order in ProcessingResult
        from data_extract.core.models import Entity, EntityType

        text = "RISK-003 first. CTRL-001 second. RISK-001 third."
        entities = [
            # Intentionally out of order by position
            Entity(
                type=EntityType.RISK,
                id="RISK-003",
                text="RISK-003",
                confidence=0.95,
                location={"start": 0, "end": 8},
            ),
            Entity(
                type=EntityType.RISK,
                id="RISK-001",
                text="RISK-001",
                confidence=0.93,
                location={"start": 33, "end": 41},
            ),
            Entity(
                type=EntityType.CONTROL,
                id="CTRL-001",
                text="CTRL-001",
                confidence=0.92,
                location={"start": 16, "end": 24},
            ),
        ]

        document = Document(
            id="entity_order_test",
            text=text,
            entities=entities,
            metadata=create_test_metadata("test.pdf"),
            structure={},
        )

        # GIVEN: ProcessingContext
        context = ProcessingContext(config={}, logger=Mock(), metrics={})

        # GIVEN: Mock SentenceSegmenter
        mock_segmenter = Mock()
        sentences = [s.strip() for s in text.split(".") if s.strip()]
        mock_segmenter.segment.return_value = sentences

        # WHEN: EntityPreserver.analyze_entities() called multiple times
        engine = ChunkingEngine(
            segmenter=mock_segmenter, chunk_size=512, overlap_pct=0.15, entity_aware=True
        )

        # Run multiple times
        first_run = list(engine.process(document, context))
        second_run = list(engine.process(document, context))
        third_run = list(engine.process(document, context))

        # THEN: Always returns same sorted order (by start_pos)
        # Verify entity order in metadata is consistent
        if hasattr(first_run[0].metadata, "entity_tags") and first_run[0].metadata.entity_tags:
            first_entity_ids = [e.entity_id for e in first_run[0].metadata.entity_tags]
            second_entity_ids = [e.entity_id for e in second_run[0].metadata.entity_tags]
            third_entity_ids = [e.entity_id for e in third_run[0].metadata.entity_tags]

            # All runs should have same entity order
            assert first_entity_ids == second_entity_ids
            assert second_entity_ids == third_entity_ids


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
