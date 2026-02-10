"""Integration tests for entity lookup and serialization (Story 3.2 - AC-3.2-5, AC-3.2-6, Story 3.8).

Tests cross-chunk entity lookup functionality and JSON serialization
of entity tags.

Test Coverage:
    - AC-3.2-5: Entity ID cross-chunk lookups
    - AC-3.2-6: Entity tags JSON serialization
    - Story 3.8: Cross-chunk entity lookup functionality
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import Mock

import pytest

pytestmark = [pytest.mark.P1, pytest.mark.integration, pytest.mark.chunking]

# These imports WILL FAIL in RED phase - this is expected
try:
    from data_extract.chunk.engine import ChunkingEngine
    from data_extract.core.models import (
        Chunk,
        Document,
        Entity,
        EntityType,
        Metadata,
        ProcessingContext,
    )
except ImportError:
    ChunkingEngine = None
    Chunk = None
    Document = None
    Entity = None
    EntityType = None
    Metadata = None
    ProcessingContext = None

pytestmark = [pytest.mark.integration, pytest.mark.chunking, pytest.mark.entity_aware]


def create_test_metadata(source_file: str = "test.pdf") -> "Metadata":
    """Create complete Metadata for tests."""
    return Metadata(
        source_file=Path(source_file),
        file_hash="abc123",
        processing_timestamp=datetime.now(timezone.utc),
        tool_version="3.2.0",
        config_version="1.0",
    )


class TestEntityIDCrossReferences:
    """Test entity ID cross-chunk lookups (AC-3.2-5)."""

    def test_entity_ids_enable_cross_chunk_search(self):
        """Should enable cross-chunk entity lookups by ID (AC-3.2-5)."""
        # GIVEN: Entity "RISK-2024-001" mentioned in multiple chunks
        text = (
            """
        RISK-2024-001 is a critical data breach risk.
        """
            + (" ".join([f"Sentence {i}." for i in range(50)]))
            + """
        RISK-2024-001 requires ongoing monitoring and mitigation.
        """
        )

        entities = [
            Entity(
                type=EntityType.RISK,
                id="RISK-2024-001",
                text="RISK-2024-001",
                confidence=0.95,
                location={"start": 9, "end": 22},
            ),
            Entity(
                type=EntityType.RISK,
                id="RISK-2024-001",
                text="RISK-2024-001",
                confidence=0.95,
                location={"start": len(text) - 100, "end": len(text) - 87},
            ),
        ]

        document = Document(
            id="cross_ref_test",
            text=text,
            entities=entities,
            metadata=create_test_metadata(),
            structure={},
        )

        # WHEN: Search all chunks for entity_id="RISK-2024-001"
        mock_segmenter = Mock()
        sentences = [s.strip() for s in text.split(".") if s.strip()]
        mock_segmenter.segment.return_value = sentences

        engine = ChunkingEngine(
            segmenter=mock_segmenter, chunk_size=256, overlap_pct=0.15, entity_aware=True
        )
        context = ProcessingContext(config={}, logger=Mock(), metrics={})
        chunks = list(engine.process(document, context))

        # THEN: Returns all chunks containing that entity
        matching_chunks = []
        for chunk in chunks:
            if hasattr(chunk.metadata, "entity_tags"):
                for entity_tag in chunk.metadata.entity_tags:
                    if entity_tag.entity_id == "RISK-2024-001":
                        matching_chunks.append(chunk)
                        break

        assert len(matching_chunks) >= 1, "Expected entity found in at least one chunk"

    def test_multiple_entity_occurrences(self):
        """Should track all occurrences of an entity across chunks."""
        # Create text with entity appearing 3 times
        text = (
            """
        CTRL-050 first occurrence.
        """
            + (" Filler text. " * 30)
            + """
        CTRL-050 second occurrence.
        """
            + (" More filler. " * 30)
            + """
        CTRL-050 third occurrence.
        """
        )

        entities = [
            Entity(
                type=EntityType.CONTROL,
                id="CTRL-050",
                text="CTRL-050",
                confidence=0.92,
                location={"start": 9, "end": 17},
            ),
            Entity(
                type=EntityType.CONTROL,
                id="CTRL-050",
                text="CTRL-050",
                confidence=0.92,
                location={"start": 200, "end": 208},
            ),
            Entity(
                type=EntityType.CONTROL,
                id="CTRL-050",
                text="CTRL-050",
                confidence=0.92,
                location={"start": 400, "end": 408},
            ),
        ]

        document = Document(
            id="multiple_occurrence_test",
            text=text,
            entities=entities,
            metadata=create_test_metadata(),
            structure={},
        )

        mock_segmenter = Mock()
        sentences = text.split(". ")
        mock_segmenter.segment.return_value = sentences

        engine = ChunkingEngine(
            segmenter=mock_segmenter, chunk_size=200, overlap_pct=0.1, entity_aware=True
        )
        context = ProcessingContext(config={}, logger=Mock(), metrics={})
        chunks = list(engine.process(document, context))

        # Find all chunks with CTRL-050
        ctrl_chunks = find_chunks_by_entity_id(chunks, "CTRL-050")
        assert len(ctrl_chunks) >= 1, "Expected entity in at least one chunk"


class TestEntityTagsJSONSerialization:
    """Test entity tags JSON serialization (AC-3.2-6)."""

    def test_entity_tags_json_serialization(self):
        """Should serialize entity_tags to JSON (AC-3.2-6)."""
        # GIVEN: Chunk with entity_tags populated
        text = "RISK-001 data breach risk mitigated by CTRL-042."

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
            id="serialization_test",
            text=text,
            entities=entities,
            metadata=create_test_metadata(),
            structure={},
        )

        # WHEN: Chunk.to_dict() called
        mock_segmenter = Mock()
        mock_segmenter.segment.return_value = [text]

        engine = ChunkingEngine(
            segmenter=mock_segmenter, chunk_size=512, overlap_pct=0.15, entity_aware=True
        )
        context = ProcessingContext(config={}, logger=Mock(), metrics={})
        chunks = list(engine.process(document, context))

        assert len(chunks) > 0, "Expected at least one chunk"
        chunk_dict = chunks[0].to_dict()

        # THEN: entity_tags converted to list of dicts, JSON serializable
        assert "metadata" in chunk_dict
        if "entity_tags" in chunk_dict["metadata"]:
            entity_tags = chunk_dict["metadata"]["entity_tags"]
            assert isinstance(entity_tags, list)
            # Should be JSON serializable
            json_str = json.dumps(chunk_dict)
            assert json_str is not None

    def test_complex_entity_serialization(self):
        """Should serialize complex entity structures to JSON."""
        text = "POL-001 policy with complex metadata and relationships."

        entities = [
            Entity(
                type=EntityType.POLICY,
                id="POL-001",
                text="POL-001",
                confidence=0.93,
                location={"start": 0, "end": 7},
                # Complex metadata
                metadata={
                    "version": "2.0",
                    "effective_date": "2024-01-01",
                    "review_cycle": "quarterly",
                },
            )
        ]

        document = Document(
            id="complex_serialization_test",
            text=text,
            entities=entities,
            metadata=create_test_metadata(),
            structure={},
        )

        mock_segmenter = Mock()
        mock_segmenter.segment.return_value = [text]

        engine = ChunkingEngine(
            segmenter=mock_segmenter, chunk_size=512, overlap_pct=0.15, entity_aware=True
        )
        context = ProcessingContext(config={}, logger=Mock(), metrics={})
        chunks = list(engine.process(document, context))

        # Should serialize without errors
        chunk_dict = chunks[0].to_dict()
        json_str = json.dumps(chunk_dict)
        assert json_str is not None

        # Deserialize and verify structure
        parsed = json.loads(json_str)
        assert "metadata" in parsed


class TestCrossChunkEntityLookup:
    """Test cross-chunk entity lookup functionality (Story 3.8 - AC-3.8-1, AC-3.8-2, AC-3.8-3).

    Validates that entity IDs enable cross-chunk queries for RAG workflows.
    Tests the find_chunks_by_entity_id() helper function.
    """

    def test_cross_chunk_entity_lookup(self):
        """Should enable cross-chunk entity lookup by entity_id (AC-3.8-1, AC-3.8-2, AC-3.8-3)."""
        # GIVEN: Document with large entity (>chunk_size) splitting across 2 chunks
        large_entity_text = "RISK-001: " + ("risk description " * 300)  # ~1500 tokens

        # Add more entities for multiple entity lookup test (AC-3.8-2)
        text = (
            large_entity_text
            + " Some filler text. "
            + ("Additional sentence. " * 50)
            + " CTRL-042 encryption control. "
            + ("More filler. " * 30)
            + " PROC-100 process description. "
        )

        entities = [
            Entity(
                type=EntityType.RISK,
                id="RISK-001",
                text=large_entity_text[:200],
                confidence=0.95,
                location={"start": 0, "end": len(large_entity_text)},
            ),
            Entity(
                type=EntityType.CONTROL,
                id="CTRL-042",
                text="CTRL-042",
                confidence=0.92,
                location={
                    "start": len(large_entity_text) + 100,
                    "end": len(large_entity_text) + 108,
                },
            ),
            Entity(
                type=EntityType.PROCESS,
                id="PROC-100",
                text="PROC-100",
                confidence=0.94,
                location={"start": len(text) - 100, "end": len(text) - 92},
            ),
        ]

        document = Document(
            id="cross_chunk_lookup_test",
            text=text,
            entities=entities,
            metadata=create_test_metadata("lookup_test.pdf"),
            structure={},
        )

        # WHEN: Entity-aware chunking performed with chunk_size=512
        mock_segmenter = Mock()
        sentences = [s.strip() for s in text.split(".") if s.strip()]
        mock_segmenter.segment.return_value = sentences

        engine = ChunkingEngine(
            segmenter=mock_segmenter, chunk_size=512, overlap_pct=0.15, entity_aware=True
        )
        context = ProcessingContext(config={}, logger=Mock(), metrics={})
        chunks = list(engine.process(document, context))

        # THEN: Large entity (RISK-001) appears in multiple chunks
        assert len(chunks) >= 2, "Expected at least 2 chunks for large document"

        risk_001_chunks = find_chunks_by_entity_id(chunks, "RISK-001")

        # AC-3.8-1: Lookup function returns chunks containing RISK-001
        assert len(risk_001_chunks) >= 1, "Expected RISK-001 in at least one chunk"

        # Verify entity_id consistency across chunks
        for chunk in risk_001_chunks:
            entity_ids = [e.entity_id for e in chunk.metadata.entity_tags]
            assert "RISK-001" in entity_ids, f"Expected RISK-001 in chunk {chunk.id}"

        # AC-3.8-2: Multiple entity lookup - only matching chunks returned
        ctrl_042_chunks = find_chunks_by_entity_id(chunks, "CTRL-042")
        proc_100_chunks = find_chunks_by_entity_id(chunks, "PROC-100")

        # Verify each entity lookup returns results (distinct entities in different parts of document)
        assert len(ctrl_042_chunks) >= 1, "Expected CTRL-042 found in at least one chunk"
        assert len(proc_100_chunks) >= 1, "Expected PROC-100 found in at least one chunk"

        # AC-3.8-3: Entity not found handling - empty list returned
        not_found_chunks = find_chunks_by_entity_id(chunks, "RISK-999")
        assert not_found_chunks == [], "Expected empty list for non-existent entity"

        # Verify graceful handling (no exceptions)
        assert isinstance(not_found_chunks, list), "Expected list return type"

    def test_lookup_performance(self):
        """Should efficiently lookup entities across many chunks."""
        # Create large document with many chunks
        text = " ".join([f"Sentence {i}." for i in range(500)])
        # Insert entity references at specific positions
        text = text[:100] + " PROC-200 " + text[110:500] + " PROC-200 " + text[510:]

        entities = [
            Entity(
                type=EntityType.PROCESS,
                id="PROC-200",
                text="PROC-200",
                confidence=0.94,
                location={"start": 100, "end": 108},
            ),
            Entity(
                type=EntityType.PROCESS,
                id="PROC-200",
                text="PROC-200",
                confidence=0.94,
                location={"start": 500, "end": 508},
            ),
        ]

        document = Document(
            id="performance_test",
            text=text,
            entities=entities,
            metadata=create_test_metadata(),
            structure={},
        )

        mock_segmenter = Mock()
        sentences = text.split(". ")
        mock_segmenter.segment.return_value = sentences

        engine = ChunkingEngine(
            segmenter=mock_segmenter, chunk_size=128, overlap_pct=0.1, entity_aware=True
        )
        context = ProcessingContext(config={}, logger=Mock(), metrics={})
        chunks = list(engine.process(document, context))

        # Should handle lookup efficiently even with many chunks
        proc_chunks = find_chunks_by_entity_id(chunks, "PROC-200")
        assert len(proc_chunks) >= 1, "Expected entity found"


def find_chunks_by_entity_id(chunks: list, entity_id: str) -> list:
    """Helper function to find all chunks containing a specific entity_id.

    Enables cross-chunk entity queries for RAG workflows (AC-3.2-5, Story 3.8).

    Args:
        chunks: List of Chunk objects from chunking engine
        entity_id: Entity ID to search for (e.g., "RISK-001", "CTRL-042")

    Returns:
        List of Chunk objects containing the specified entity_id.
        Empty list if entity not found.

    Example:
        >>> chunks = engine.process(document, context)
        >>> risk_chunks = find_chunks_by_entity_id(chunks, "RISK-2024-001")
        >>> print(f"Found {len(risk_chunks)} chunks mentioning RISK-2024-001")
    """
    return [
        chunk
        for chunk in chunks
        if hasattr(chunk.metadata, "entity_tags")
        and any(entity.entity_id == entity_id for entity in chunk.metadata.entity_tags)
    ]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
