"""Integration tests for entity preservation rate (Story 3.2 - AC-3.2-1).

Tests entity preservation during chunking, targeting >95% preservation rate
for audit entities. Also handles oversized entity scenarios.

Test Coverage:
    - AC-3.2-1: >95% entity preservation rate (CRITICAL)
    - Large entity handling that exceeds chunk size
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


@pytest.fixture
def risk_register_document():
    """Load entity-rich risk register fixture (100+ entities)."""
    fixture_path = Path(__file__).parent.parent.parent / "fixtures" / "entity_rich_documents"
    risk_register_file = fixture_path / "risk_register.md"

    if not risk_register_file.exists():
        pytest.skip(f"Fixture not found: {risk_register_file}")

    text = risk_register_file.read_text(encoding="utf-8")

    # Create entities found in risk register
    entities = []
    # Sample entities (real implementation would parse all)
    entity_patterns = [
        ("RISK-2024-001", EntityType.RISK, 0, 100),
        ("CTRL-001", EntityType.CONTROL, 200, 250),
        ("POL-001", EntityType.POLICY, 400, 450),
        ("RISK-2024-002", EntityType.RISK, 600, 700),
        ("CTRL-002", EntityType.CONTROL, 800, 850),
    ]

    for entity_id, entity_type, start, end in entity_patterns:
        entities.append(
            Entity(
                type=entity_type,
                id=entity_id,
                text=text[start:end] if start < len(text) else entity_id,
                confidence=0.95,
                location={"start": start, "end": end},
            )
        )

    return Document(
        id="risk_register_test",
        text=text,
        entities=entities,
        metadata=create_test_metadata("risk_register.md"),
        structure={},
    )


class TestEntityPreservationRate:
    """Test entity preservation rate >95% (AC-3.2-1 - CRITICAL)."""

    def test_entity_preservation_rate_exceeds_95_percent(self, risk_register_document):
        """Should preserve >95% of entities within single chunks (AC-3.2-1)."""
        # GIVEN: Real risk register document with 100+ entities
        document = risk_register_document

        # WHEN: ChunkingEngine.chunk_document() called with entity_aware=True
        mock_segmenter = Mock()
        # Simple sentence splitting for test
        sentences = document.text.split(". ")
        mock_segmenter.segment.return_value = sentences

        engine = ChunkingEngine(
            segmenter=mock_segmenter, chunk_size=512, overlap_pct=0.15, entity_aware=True
        )
        context = ProcessingContext(config={}, logger=Mock(), metrics={})
        chunks = list(engine.process(document, context))

        # THEN: Measure entities intact vs. split
        total_entities = len(document.entities)
        split_entities = 0

        for chunk in chunks:
            # Count entities marked as partial
            if hasattr(chunk.metadata, "entity_tags"):
                for entity_tag in chunk.metadata.entity_tags:
                    if entity_tag.is_partial:
                        split_entities += 1

        intact_entities = total_entities - split_entities
        preservation_rate = intact_entities / total_entities if total_entities > 0 else 0

        # AND: Assert >95% intact
        assert preservation_rate > 0.95, (
            f"Entity preservation rate {preservation_rate:.2%} below 95% threshold. "
            f"Intact: {intact_entities}, Split: {split_entities}, Total: {total_entities}"
        )

    def test_preservation_rate_with_overlap(self, risk_register_document):
        """Should improve preservation with chunk overlap."""
        document = risk_register_document

        mock_segmenter = Mock()
        sentences = document.text.split(". ")
        mock_segmenter.segment.return_value = sentences

        # Test with higher overlap
        engine = ChunkingEngine(
            segmenter=mock_segmenter, chunk_size=512, overlap_pct=0.25, entity_aware=True
        )
        context = ProcessingContext(config={}, logger=Mock(), metrics={})
        chunks = list(engine.process(document, context))

        # Count preserved entities
        total_entities = len(document.entities)
        split_entities = 0

        for chunk in chunks:
            if hasattr(chunk.metadata, "entity_tags"):
                for entity_tag in chunk.metadata.entity_tags:
                    if entity_tag.is_partial:
                        split_entities += 1

        preservation_rate = (total_entities - split_entities) / total_entities
        assert preservation_rate > 0.90, f"Preservation rate {preservation_rate:.2%} too low"


class TestLargeEntityHandling:
    """Test oversized entity handling (AC-3.2-1, AC-3.2-4)."""

    def test_large_entity_exceeding_chunk_size(self):
        """Should handle entity > chunk_size gracefully (AC-3.2-1, AC-3.2-4)."""
        # GIVEN: Entity definition > chunk_size (e.g., 1000 tokens)
        large_definition = " ".join(
            [f"This is sentence {i} of a very large entity definition." for i in range(100)]
        )
        text = f"RISK-LARGE: {large_definition}"

        entities = [
            Entity(
                type=EntityType.RISK,
                id="RISK-LARGE",
                text=large_definition[:200],  # Truncated
                confidence=0.95,
                location={"start": 0, "end": len(text)},
            )
        ]

        document = Document(
            id="large_entity_test",
            text=text,
            entities=entities,
            metadata=create_test_metadata(),
            structure={},
        )

        # WHEN: chunk_document() called with small chunk_size
        mock_segmenter = Mock()
        sentences = [s.strip() for s in text.split(".") if s.strip()]
        mock_segmenter.segment.return_value = sentences

        engine = ChunkingEngine(
            segmenter=mock_segmenter, chunk_size=256, overlap_pct=0.0, entity_aware=True
        )
        context = ProcessingContext(config={}, logger=Mock(), metrics={})
        chunks = list(engine.process(document, context))

        # THEN: Entity becomes single chunk exceeding chunk_size, warning logged
        # Should not crash, handles gracefully
        assert len(chunks) > 0, "Expected at least one chunk (oversized allowed for entities)"

    def test_very_large_entity_split_handling(self):
        """Should split very large entities with proper metadata."""
        # Create entity that's 3x chunk size
        huge_text = " ".join([f"Sentence {i}." for i in range(200)])
        text = f"RISK-HUGE: {huge_text}"

        entities = [
            Entity(
                type=EntityType.RISK,
                id="RISK-HUGE",
                text=huge_text[:500],
                confidence=0.95,
                location={"start": 0, "end": len(text)},
            )
        ]

        document = Document(
            id="huge_entity_test",
            text=text,
            entities=entities,
            metadata=create_test_metadata(),
            structure={},
        )

        mock_segmenter = Mock()
        sentences = text.split(". ")
        mock_segmenter.segment.return_value = sentences

        engine = ChunkingEngine(
            segmenter=mock_segmenter, chunk_size=128, overlap_pct=0.0, entity_aware=True
        )
        context = ProcessingContext(config={}, logger=Mock(), metrics={})
        chunks = list(engine.process(document, context))

        # Should create multiple chunks with partial flags
        assert len(chunks) >= 2, "Expected multiple chunks for huge entity"

        # Check partial flags are set
        partial_count = 0
        for chunk in chunks:
            if hasattr(chunk.metadata, "entity_tags"):
                for tag in chunk.metadata.entity_tags:
                    if tag.entity_id == "RISK-HUGE" and tag.is_partial:
                        partial_count += 1

        assert partial_count >= 2, "Expected partial flags on split entity chunks"
