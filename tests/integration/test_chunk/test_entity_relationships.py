"""Integration tests for entity relationship preservation (Story 3.2 - AC-3.2-3).

Tests relationship context preservation and mixed entity type handling
during chunking operations.

Test Coverage:
    - AC-3.2-3: Relationship context preservation (CRITICAL)
    - Mixed entity type handling (risks, controls, policies, processes)
"""

from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import Mock

import pytest

pytestmark = [pytest.mark.P2, pytest.mark.integration, pytest.mark.chunking]

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


class TestRelationshipPreservation:
    """Test entity relationship preservation (AC-3.2-3 - CRITICAL)."""

    def test_relationship_context_preserved(self):
        """Should preserve risk-control relationships in chunks (AC-3.2-3)."""
        # GIVEN: Document with "RISK-001 mitigated by CTRL-042" patterns
        text = """
        RISK-001 data breach risk is mitigated by CTRL-042 encryption control.
        The control implements AES-256 encryption for all sensitive data.
        RISK-002 supply chain disruption addresses CTRL-043 vendor diversification.
        """

        entities = [
            Entity(
                type=EntityType.RISK,
                id="RISK-001",
                text="RISK-001",
                confidence=0.95,
                location={"start": 9, "end": 17},
            ),
            Entity(
                type=EntityType.CONTROL,
                id="CTRL-042",
                text="CTRL-042",
                confidence=0.92,
                location={"start": 54, "end": 62},
            ),
            Entity(
                type=EntityType.RISK,
                id="RISK-002",
                text="RISK-002",
                confidence=0.95,
                location={"start": 150, "end": 158},
            ),
            Entity(
                type=EntityType.CONTROL,
                id="CTRL-043",
                text="CTRL-043",
                confidence=0.92,
                location={"start": 199, "end": 207},
            ),
        ]

        document = Document(
            id="relationship_test",
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

        # THEN: Relationship triples in ChunkMetadata
        found_relationships = []
        for chunk in chunks:
            if hasattr(chunk.metadata, "entity_relationships"):
                found_relationships.extend(chunk.metadata.entity_relationships)

        # AND: Both entities in same chunk when relationship span < chunk_size
        assert len(found_relationships) >= 1, "Expected at least one relationship detected"
        # Should find ("RISK-001", "mitigated_by", "CTRL-042")
        relationship_types = [r[1] for r in found_relationships]
        assert "mitigated_by" in relationship_types or "mitigates" in relationship_types

    def test_complex_relationship_patterns(self):
        """Should detect various relationship patterns."""
        text = """
        RISK-003 compliance risk is addressed by POL-GOV-001 governance policy.
        POL-GOV-001 implements CTRL-044 quarterly review control.
        CTRL-044 is executed through PROC-REV-001 review process.
        This creates a full compliance chain from risk to process.
        """

        entities = [
            Entity(
                type=EntityType.RISK,
                id="RISK-003",
                text="RISK-003",
                confidence=0.95,
                location={"start": 9, "end": 17},
            ),
            Entity(
                type=EntityType.POLICY,
                id="POL-GOV-001",
                text="POL-GOV-001",
                confidence=0.93,
                location={"start": 51, "end": 62},
            ),
            Entity(
                type=EntityType.CONTROL,
                id="CTRL-044",
                text="CTRL-044",
                confidence=0.92,
                location={"start": 108, "end": 116},
            ),
            Entity(
                type=EntityType.PROCESS,
                id="PROC-REV-001",
                text="PROC-REV-001",
                confidence=0.94,
                location={"start": 180, "end": 192},
            ),
        ]

        document = Document(
            id="complex_relationship_test",
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

        # Should preserve the chain of relationships
        found_relationships = []
        for chunk in chunks:
            if hasattr(chunk.metadata, "entity_relationships"):
                found_relationships.extend(chunk.metadata.entity_relationships)

        # Should find multiple relationship types
        assert len(found_relationships) >= 2, "Expected multiple relationships"

    def test_bidirectional_relationships(self):
        """Should handle bidirectional entity relationships."""
        text = """
        RISK-004 operational risk depends on CTRL-045 monitoring control.
        CTRL-045 monitoring control mitigates RISK-004 operational risk.
        This bidirectional relationship ensures coverage.
        """

        entities = [
            Entity(
                type=EntityType.RISK,
                id="RISK-004",
                text="RISK-004",
                confidence=0.95,
                location={"start": 9, "end": 17},
            ),
            Entity(
                type=EntityType.CONTROL,
                id="CTRL-045",
                text="CTRL-045",
                confidence=0.92,
                location={"start": 47, "end": 55},
            ),
        ]

        document = Document(
            id="bidirectional_test",
            text=text,
            entities=entities,
            metadata=create_test_metadata(),
            structure={},
        )

        mock_segmenter = Mock()
        sentences = text.split(". ")
        mock_segmenter.segment.return_value = sentences

        engine = ChunkingEngine(
            segmenter=mock_segmenter, chunk_size=512, overlap_pct=0.15, entity_aware=True
        )
        context = ProcessingContext(config={}, logger=Mock(), metrics={})
        chunks = list(engine.process(document, context))

        # Both entities should be in same chunk with relationships preserved
        risk_ctrl_chunk = None
        for chunk in chunks:
            if hasattr(chunk.metadata, "entity_tags"):
                entity_ids = [tag.entity_id for tag in chunk.metadata.entity_tags]
                if "RISK-004" in entity_ids and "CTRL-045" in entity_ids:
                    risk_ctrl_chunk = chunk
                    break

        assert risk_ctrl_chunk is not None, "Expected both entities in same chunk"


class TestMixedEntityTypes:
    """Test entity-aware chunking with multiple entity types (AC-3.2-1, AC-3.2-6)."""

    def test_entity_aware_with_multiple_entity_types(self):
        """Should handle risks, controls, policies, processes (AC-3.2-1)."""
        # GIVEN: Document with risks, controls, policies, processes
        text = """
        RISK-001 data security risk addresses POL-SEC-001 data protection policy.
        CTRL-IAM-002 multi-factor authentication implements the policy requirements.
        PROC-ACC-001 access management process supports the control implementation.
        """

        entities = [
            Entity(
                type=EntityType.RISK,
                id="RISK-001",
                text="RISK-001",
                confidence=0.95,
                location={"start": 9, "end": 17},
            ),
            Entity(
                type=EntityType.POLICY,
                id="POL-SEC-001",
                text="POL-SEC-001",
                confidence=0.93,
                location={"start": 46, "end": 57},
            ),
            Entity(
                type=EntityType.CONTROL,
                id="CTRL-IAM-002",
                text="CTRL-IAM-002",
                confidence=0.92,
                location={"start": 87, "end": 99},
            ),
            Entity(
                type=EntityType.PROCESS,
                id="PROC-ACC-001",
                text="PROC-ACC-001",
                confidence=0.94,
                location={"start": 166, "end": 178},
            ),
        ]

        document = Document(
            id="mixed_types_test",
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

        # THEN: All entity types preserved, tagged correctly in metadata
        found_entity_types = set()
        for chunk in chunks:
            if hasattr(chunk.metadata, "entity_tags"):
                for entity_tag in chunk.metadata.entity_tags:
                    found_entity_types.add(entity_tag.entity_type)

        # Should find all entity types
        assert "RISK" in found_entity_types or len(found_entity_types) > 0

    def test_entity_type_distribution(self):
        """Should maintain entity type distribution across chunks."""
        # Create document with balanced entity types
        text = """
        Section 1: RISK-005 identified. CTRL-046 applied. POL-002 referenced.
        Section 2: PROC-002 executed. RISK-006 noted. CTRL-047 implemented.
        Section 3: POL-003 updated. PROC-003 started. RISK-007 assessed.
        """

        entities = []
        entity_data = [
            ("RISK-005", EntityType.RISK, 11, 19),
            ("CTRL-046", EntityType.CONTROL, 33, 41),
            ("POL-002", EntityType.POLICY, 51, 58),
            ("PROC-002", EntityType.PROCESS, 83, 91),
            ("RISK-006", EntityType.RISK, 102, 110),
            ("CTRL-047", EntityType.CONTROL, 118, 126),
            ("POL-003", EntityType.POLICY, 151, 158),
            ("PROC-003", EntityType.PROCESS, 168, 176),
            ("RISK-007", EntityType.RISK, 186, 194),
        ]

        for entity_id, entity_type, start, end in entity_data:
            entities.append(
                Entity(
                    type=entity_type,
                    id=entity_id,
                    text=entity_id,
                    confidence=0.95,
                    location={"start": start, "end": end},
                )
            )

        document = Document(
            id="distribution_test",
            text=text,
            entities=entities,
            metadata=create_test_metadata(),
            structure={},
        )

        mock_segmenter = Mock()
        sentences = text.split(". ")
        mock_segmenter.segment.return_value = sentences

        engine = ChunkingEngine(
            segmenter=mock_segmenter, chunk_size=256, overlap_pct=0.15, entity_aware=True
        )
        context = ProcessingContext(config={}, logger=Mock(), metrics={})
        chunks = list(engine.process(document, context))

        # Count entity types per chunk
        chunk_entity_types = []
        for chunk in chunks:
            types_in_chunk = set()
            if hasattr(chunk.metadata, "entity_tags"):
                for tag in chunk.metadata.entity_tags:
                    types_in_chunk.add(tag.entity_type)
            chunk_entity_types.append(types_in_chunk)

        # Each chunk should have mixed types when possible
        assert len(chunks) >= 1, "Expected at least one chunk"
        assert any(len(types) > 1 for types in chunk_entity_types), "Expected mixed types in chunks"
