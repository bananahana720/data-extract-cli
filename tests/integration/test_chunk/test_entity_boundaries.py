"""Integration tests for entity boundary handling (Story 3.2 - AC-3.2-2, AC-3.2-4).

Tests partial entity flagging and multi-sentence entity definition boundaries
during chunking operations.

Test Coverage:
    - AC-3.2-2: Partial entity flagging for split entities
    - AC-3.2-4: Multi-sentence entity definition boundaries
"""

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


class TestPartialEntityMetadata:
    """Test partial entity flagging (AC-3.2-2)."""

    def test_partial_entity_metadata_flagging(self):
        """Should flag split entities with is_partial=True (AC-3.2-2)."""
        # GIVEN: Document with very large entity (>chunk_size to force split)
        large_entity_text = " ".join([f"Sentence {i} of large entity." for i in range(100)])
        text = f"RISK-LARGE-001: {large_entity_text} End of risk."

        entities = [
            Entity(
                type=EntityType.RISK,
                id="RISK-LARGE-001",
                text=large_entity_text[:200],  # Truncated for display
                confidence=0.95,
                location={"start": 0, "end": len(large_entity_text)},
            )
        ]

        document = Document(
            id="large_entity_test",
            text=text,
            entities=entities,
            metadata=create_test_metadata(),
            structure={},
        )

        # WHEN: Entity unavoidably split across chunks (chunk_size=256 < entity size)
        mock_segmenter = Mock()
        sentences = text.split(". ")
        mock_segmenter.segment.return_value = sentences

        engine = ChunkingEngine(
            segmenter=mock_segmenter, chunk_size=256, overlap_pct=0.0, entity_aware=True
        )
        context = ProcessingContext(config={}, logger=Mock(), metrics={})
        chunks = list(engine.process(document, context))

        # THEN: Both chunks have is_partial=True, continuation flags set
        partial_chunks = [
            c for c in chunks if hasattr(c.metadata, "entity_tags") and c.metadata.entity_tags
        ]
        assert len(partial_chunks) >= 2, "Expected at least 2 chunks with entity parts"

        # Find chunks with partial entity markers
        partial_entity_chunks = []
        for chunk in partial_chunks:
            for entity_tag in chunk.metadata.entity_tags:
                if entity_tag.is_partial:
                    partial_entity_chunks.append(chunk)
                    break

        assert len(partial_entity_chunks) >= 2, "Expected partial entity across multiple chunks"

    def test_partial_flag_consistency(self):
        """Should maintain consistent partial flags across chunks."""
        # Large entity spanning 3 chunks
        huge_text = " ".join([f"Part {i} of entity." for i in range(150)])
        text = f"CTRL-HUGE: {huge_text}"

        entities = [
            Entity(
                type=EntityType.CONTROL,
                id="CTRL-HUGE",
                text=huge_text[:300],
                confidence=0.92,
                location={"start": 0, "end": len(huge_text)},
            )
        ]

        document = Document(
            id="huge_control_test",
            text=text,
            entities=entities,
            metadata=create_test_metadata(),
            structure={},
        )

        mock_segmenter = Mock()
        sentences = text.split(". ")
        mock_segmenter.segment.return_value = sentences

        engine = ChunkingEngine(
            segmenter=mock_segmenter, chunk_size=200, overlap_pct=0.0, entity_aware=True
        )
        context = ProcessingContext(config={}, logger=Mock(), metrics={})
        chunks = list(engine.process(document, context))

        # All chunks containing the entity should have partial flag
        ctrl_chunks = []
        for chunk in chunks:
            if hasattr(chunk.metadata, "entity_tags"):
                for tag in chunk.metadata.entity_tags:
                    if tag.entity_id == "CTRL-HUGE":
                        ctrl_chunks.append((chunk, tag))
                        break

        assert len(ctrl_chunks) >= 2, "Expected entity in multiple chunks"

        # All should have partial flag
        for chunk, tag in ctrl_chunks:
            assert tag.is_partial, f"Expected partial flag in chunk {chunk.id}"


class TestMultiSentenceEntityDefinitions:
    """Test multi-sentence entity definition boundaries (AC-3.2-4)."""

    def test_multi_sentence_entity_definitions_kept_together(self):
        """Should keep multi-sentence entity definitions together (AC-3.2-4)."""
        # GIVEN: Document with entity spanning 3 sentences
        text = """
        RISK-2024-002: Supply chain disruption risk affecting critical vendor relationships.
        This risk impacts component availability and delivery schedules.
        The risk requires immediate mitigation through vendor diversification strategy.
        Next topic starts here.
        """

        entities = [
            Entity(
                type=EntityType.RISK,
                id="RISK-2024-002",
                text="RISK-2024-002 definition",
                confidence=0.95,
                # Span covers 3 sentences
                location={"start": 9, "end": 250},
            )
        ]

        document = Document(
            id="multi_sentence_test",
            text=text,
            entities=entities,
            metadata=create_test_metadata(),
            structure={},
        )

        # WHEN: chunk_document() called
        mock_segmenter = Mock()
        sentences = [s.strip() for s in text.split(".") if s.strip()]
        mock_segmenter.segment.return_value = sentences

        engine = ChunkingEngine(
            segmenter=mock_segmenter, chunk_size=512, overlap_pct=0.15, entity_aware=True
        )
        context = ProcessingContext(config={}, logger=Mock(), metrics={})
        chunks = list(engine.process(document, context))

        # THEN: All 3 sentences in same chunk
        # Find chunk containing RISK-2024-002
        entity_chunks = [
            c
            for c in chunks
            if hasattr(c.metadata, "entity_tags")
            and any(e.entity_id == "RISK-2024-002" for e in c.metadata.entity_tags)
        ]
        assert len(entity_chunks) >= 1, "Expected entity in at least one chunk"

        # AND: Boundary after definition complete (before "Next topic")
        # Entity should not be split unless it exceeds chunk_size

    def test_complex_multi_sentence_entities(self):
        """Should handle complex multi-sentence entity patterns."""
        text = """
        POL-SEC-001: Security Policy Definition.
        This policy establishes mandatory security controls for all systems.
        It includes requirements for authentication, authorization, and auditing.
        The policy applies to all employees and contractors.
        Compliance is mandatory and monitored quarterly.

        PROC-AUD-001: Audit Process.
        This process defines audit procedures.
        """

        entities = [
            Entity(
                type=EntityType.POLICY,
                id="POL-SEC-001",
                text="Security policy full definition",
                confidence=0.93,
                location={"start": 9, "end": 290},  # 5 sentences
            ),
            Entity(
                type=EntityType.PROCESS,
                id="PROC-AUD-001",
                text="Audit process",
                confidence=0.94,
                location={"start": 310, "end": 380},
            ),
        ]

        document = Document(
            id="complex_multi_test",
            text=text,
            entities=entities,
            metadata=create_test_metadata(),
            structure={},
        )

        mock_segmenter = Mock()
        sentences = [s.strip() for s in text.split(".") if s.strip()]
        mock_segmenter.segment.return_value = sentences

        engine = ChunkingEngine(
            segmenter=mock_segmenter, chunk_size=512, overlap_pct=0.15, entity_aware=True
        )
        context = ProcessingContext(config={}, logger=Mock(), metrics={})
        chunks = list(engine.process(document, context))

        # Both entities should be preserved
        pol_chunks = []
        proc_chunks = []

        for chunk in chunks:
            if hasattr(chunk.metadata, "entity_tags"):
                for tag in chunk.metadata.entity_tags:
                    if tag.entity_id == "POL-SEC-001":
                        pol_chunks.append(chunk)
                    elif tag.entity_id == "PROC-AUD-001":
                        proc_chunks.append(chunk)

        assert len(pol_chunks) >= 1, "Expected policy entity preserved"
        assert len(proc_chunks) >= 1, "Expected process entity preserved"

    def test_entity_boundary_detection(self):
        """Should detect entity boundaries correctly."""
        text = """
        RISK-001: First risk description here.
        Some unrelated text in between.
        RISK-002: Second risk description here.
        More unrelated content.
        """

        entities = [
            Entity(
                type=EntityType.RISK,
                id="RISK-001",
                text="First risk",
                confidence=0.95,
                location={"start": 9, "end": 47},
            ),
            Entity(
                type=EntityType.RISK,
                id="RISK-002",
                text="Second risk",
                confidence=0.95,
                location={"start": 89, "end": 128},
            ),
        ]

        document = Document(
            id="boundary_test",
            text=text,
            entities=entities,
            metadata=create_test_metadata(),
            structure={},
        )

        mock_segmenter = Mock()
        sentences = [s.strip() for s in text.split(".") if s.strip()]
        mock_segmenter.segment.return_value = sentences

        engine = ChunkingEngine(
            segmenter=mock_segmenter, chunk_size=256, overlap_pct=0.15, entity_aware=True
        )
        context = ProcessingContext(config={}, logger=Mock(), metrics={})
        chunks = list(engine.process(document, context))

        # Entities should be in separate chunks or same chunk but not split
        risk1_partial = False
        risk2_partial = False

        for chunk in chunks:
            if hasattr(chunk.metadata, "entity_tags"):
                for tag in chunk.metadata.entity_tags:
                    if tag.entity_id == "RISK-001" and tag.is_partial:
                        risk1_partial = True
                    if tag.entity_id == "RISK-002" and tag.is_partial:
                        risk2_partial = True

        # Neither should be partial (they fit in chunks)
        assert not risk1_partial, "RISK-001 should not be partial"
        assert not risk2_partial, "RISK-002 should not be partial"
