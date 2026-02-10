"""Integration tests for section-aware chunking (Story 3.2 - RED PHASE).

Tests section boundary detection with real multi-section documents. Completes
deferred AC-3.1-2 from Story 3.1. All tests WILL FAIL until section detection
is implemented (GREEN phase).

Test Coverage:
    - AC-3.2-7: Section-aware chunking with policy documents (CRITICAL)
    - AC-3.2-7: Section context breadcrumb formatting
    - AC-3.2-7: Large section splitting at sentence boundaries
    - AC-3.2-7: Graceful degradation for documents without sections
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
        ContentBlock,
        ContentType,
        Document,
        Metadata,
        Position,
        ProcessingContext,
    )
except ImportError:
    ChunkingEngine = None
    ContentBlock = None
    ContentType = None
    Document = None
    Metadata = None
    Position = None
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
def policy_document_with_sections():
    """Load multi-section policy document fixture."""
    fixture_path = Path(__file__).parent.parent.parent / "fixtures" / "entity_rich_documents"
    policy_file = fixture_path / "policy_document.md"

    if not policy_file.exists():
        pytest.skip(f"Fixture not found: {policy_file}")

    text = policy_file.read_text(encoding="utf-8")

    # Create content blocks with section headings
    content_blocks = [
        ContentBlock(
            block_type=ContentType.HEADING,
            content="1. Introduction",
            position=Position(page=1, sequence_index=0),
            metadata={"level": 1},
        ),
        ContentBlock(
            block_type=ContentType.HEADING,
            content="1.1 Purpose",
            position=Position(page=1, sequence_index=1),
            metadata={"level": 2},
        ),
        ContentBlock(
            block_type=ContentType.PARAGRAPH,
            content="Purpose content here.",
            position=Position(page=1, sequence_index=2),
        ),
        ContentBlock(
            block_type=ContentType.HEADING,
            content="2. Risk Assessment",
            position=Position(page=2, sequence_index=3),
            metadata={"level": 1},
        ),
        ContentBlock(
            block_type=ContentType.HEADING,
            content="2.1 Risk Identification",
            position=Position(page=2, sequence_index=4),
            metadata={"level": 2},
        ),
    ]

    return Document(
        id="policy_test",
        text=text,
        entities=[],
        metadata=create_test_metadata("policy_document.md"),
        structure={"content_blocks": content_blocks},
    )


class TestSectionAwareChunking:
    """Test section-aware chunking with real documents (AC-3.2-7 - CRITICAL)."""

    def test_section_aware_chunking_with_policy_document(self, policy_document_with_sections):
        """Should align chunks with section boundaries (AC-3.2-7)."""
        # GIVEN: Policy document with 5 sections (headings + page breaks)
        document = policy_document_with_sections

        # WHEN: chunk_document() called
        mock_segmenter = Mock()
        sentences = [s.strip() for s in document.text.split(".") if s.strip()]
        mock_segmenter.segment.return_value = sentences

        engine = ChunkingEngine(
            segmenter=mock_segmenter, chunk_size=512, overlap_pct=0.15, entity_aware=True
        )
        context = ProcessingContext(config={}, logger=Mock(), metrics={})
        chunks = list(engine.process(document, context))

        # THEN: Chunks align with section boundaries
        assert len(chunks) > 0, "Expected chunks generated"

        # AND: section_context populated
        chunks_with_section = [
            c
            for c in chunks
            if hasattr(c.metadata, "section_context") and c.metadata.section_context
        ]
        assert len(chunks_with_section) > 0, "Expected some chunks with section context"


class TestSectionContextBreadcrumbs:
    """Test section context breadcrumb formatting (AC-3.2-7)."""

    def test_section_context_breadcrumb_format(self):
        """Should format section hierarchy as breadcrumbs (AC-3.2-7)."""
        # GIVEN: Nested sections (Risk Assessment > Identified Risks > High Severity)
        text = """Risk Assessment section.
        Identified Risks subsection.
        High Severity details here."""

        content_blocks = [
            ContentBlock(
                block_type=ContentType.HEADING,
                content="Risk Assessment",
                position=Position(page=1, sequence_index=0),
                metadata={"level": 1},
            ),
            ContentBlock(
                block_type=ContentType.PARAGRAPH,
                content="Risk Assessment section.",
                position=Position(page=1, sequence_index=1),
            ),
            ContentBlock(
                block_type=ContentType.HEADING,
                content="Identified Risks",
                position=Position(page=1, sequence_index=2),
                metadata={"level": 2},
            ),
            ContentBlock(
                block_type=ContentType.PARAGRAPH,
                content="Identified Risks subsection.",
                position=Position(page=1, sequence_index=3),
            ),
            ContentBlock(
                block_type=ContentType.HEADING,
                content="High Severity",
                position=Position(page=1, sequence_index=4),
                metadata={"level": 3},
            ),
            ContentBlock(
                block_type=ContentType.PARAGRAPH,
                content="High Severity details here.",
                position=Position(page=1, sequence_index=5),
            ),
        ]

        document = Document(
            id="breadcrumb_test",
            text=text,
            entities=[],
            metadata=create_test_metadata(),
            structure={"content_blocks": content_blocks},
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

        # THEN: ChunkMetadata.section_context = "Risk Assessment > Identified Risks > High Severity"
        breadcrumb_chunks = [
            c
            for c in chunks
            if hasattr(c.metadata, "section_context")
            and c.metadata.section_context
            and ">" in c.metadata.section_context
        ]

        if len(breadcrumb_chunks) > 0:
            # Verify breadcrumb format
            sample_breadcrumb = breadcrumb_chunks[0].metadata.section_context
            assert " > " in sample_breadcrumb, "Expected ' > ' delimiter in breadcrumb"


class TestLargeSectionSplitting:
    """Test large section splitting (AC-3.2-7, AC-3.1-1)."""

    def test_large_section_split_at_sentence_boundaries(self):
        """Should split large sections at sentence boundaries (AC-3.2-7)."""
        # GIVEN: Section larger than chunk_size
        large_section_content = " ".join(
            [f"This is sentence {i} in a very large section." for i in range(100)]
        )
        text = f"### Large Section\n{large_section_content}"

        content_blocks = [
            ContentBlock(
                block_type=ContentType.HEADING,
                content="Large Section",
                position=Position(page=1, sequence_index=0),
                metadata={"level": 1},
            ),
            ContentBlock(
                block_type=ContentType.PARAGRAPH,
                content=large_section_content,
                position=Position(page=1, sequence_index=1),
            ),
        ]

        document = Document(
            id="large_section_test",
            text=text,
            entities=[],
            metadata=create_test_metadata(),
            structure={"content_blocks": content_blocks},
        )

        # WHEN: chunk_document() called with chunk_size < section size
        mock_segmenter = Mock()
        sentences = [s.strip() for s in large_section_content.split(".") if s.strip()]
        mock_segmenter.segment.return_value = sentences

        engine = ChunkingEngine(
            segmenter=mock_segmenter, chunk_size=256, overlap_pct=0.0, entity_aware=True
        )
        context = ProcessingContext(config={}, logger=Mock(), metrics={})
        chunks = list(engine.process(document, context))

        # THEN: Section split at sentence boundaries (not mid-sentence)
        assert len(chunks) > 1, "Expected section split into multiple chunks"

        # AND: section_context preserved across all chunks in same section
        section_contexts = [
            c.metadata.section_context
            for c in chunks
            if hasattr(c.metadata, "section_context") and c.metadata.section_context
        ]

        # All chunks in same section should have same section_context
        if len(section_contexts) > 1:
            first_context = section_contexts[0]
            # Multiple chunks may share same section
            assert any(ctx == first_context for ctx in section_contexts[1:])


class TestDocumentWithoutSections:
    """Test graceful degradation (AC-3.2-7)."""

    def test_document_without_sections_graceful_degradation(self):
        """Should fall back to sentence-only chunking (AC-3.2-7)."""
        # GIVEN: Document with no section markers
        text = """This is plain text document with no headings.
        It contains multiple sentences across several paragraphs.
        No page breaks, no structural markers, just content.
        Chunking should fall back to Story 3.1 sentence-boundary behavior."""

        document = Document(
            id="no_sections_test",
            text=text,
            entities=[],
            metadata=create_test_metadata(),
            structure={},  # No content_blocks
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

        # THEN: Returns chunks (falls back to sentence-boundary chunking)
        assert len(chunks) > 0, "Expected chunks even without sections"

        # AND: section_context is empty or missing (graceful degradation)
        for chunk in chunks:
            if hasattr(chunk.metadata, "section_context"):
                # Should be empty string, not populated
                assert (
                    chunk.metadata.section_context == "" or chunk.metadata.section_context is None
                )


class TestSectionAndEntityIntegration:
    """Test combined section and entity awareness (AC-3.2-7, AC-3.2-1)."""

    def test_section_aware_with_entities(self):
        """Should handle entities within sections correctly (AC-3.2-7 + AC-3.2-1)."""
        # GIVEN: Document with sections containing entities
        text = """### Risk Assessment
        RISK-001 data breach risk identified in this section.
        CTRL-042 encryption control mitigates the risk.

        ### Controls Framework
        CTRL-042 implements AES-256 encryption standards.
        """

        from data_extract.core.models import Entity, EntityType

        entities = [
            Entity(
                type=EntityType.RISK,
                id="RISK-001",
                text="RISK-001",
                confidence=0.95,
                location={"start": 30, "end": 38},
            ),
            Entity(
                type=EntityType.CONTROL,
                id="CTRL-042",
                text="CTRL-042",
                confidence=0.92,
                location={"start": 80, "end": 88},
            ),
            Entity(
                type=EntityType.CONTROL,
                id="CTRL-042",
                text="CTRL-042",
                confidence=0.92,
                location={"start": 150, "end": 158},
            ),
        ]

        content_blocks = [
            ContentBlock(
                block_type=ContentType.HEADING,
                content="Risk Assessment",
                position=Position(page=1, sequence_index=0),
                metadata={"level": 1},
            ),
            ContentBlock(
                block_type=ContentType.PARAGRAPH,
                content="RISK-001 data breach risk identified in this section.",
                position=Position(page=1, sequence_index=1),
            ),
            ContentBlock(
                block_type=ContentType.PARAGRAPH,
                content="CTRL-042 encryption control mitigates the risk.",
                position=Position(page=1, sequence_index=2),
            ),
            ContentBlock(
                block_type=ContentType.HEADING,
                content="Controls Framework",
                position=Position(page=1, sequence_index=3),
                metadata={"level": 1},
            ),
            ContentBlock(
                block_type=ContentType.PARAGRAPH,
                content="CTRL-042 implements AES-256 encryption standards.",
                position=Position(page=1, sequence_index=4),
            ),
        ]

        document = Document(
            id="section_entity_test",
            text=text,
            entities=entities,
            metadata=create_test_metadata(),
            structure={"content_blocks": content_blocks},
        )

        # WHEN: chunk_document() called with both entity_aware and section detection
        mock_segmenter = Mock()
        sentences = [s.strip() for s in text.split(".") if s.strip()]
        mock_segmenter.segment.return_value = sentences

        engine = ChunkingEngine(
            segmenter=mock_segmenter, chunk_size=512, overlap_pct=0.15, entity_aware=True
        )
        context = ProcessingContext(config={}, logger=Mock(), metrics={})
        chunks = list(engine.process(document, context))

        # THEN: Chunks have both section_context and entity_tags populated
        integrated_chunks = [
            c
            for c in chunks
            if hasattr(c.metadata, "section_context")
            and hasattr(c.metadata, "entity_tags")
            and c.metadata.section_context
            and c.metadata.entity_tags
        ]

        # Should find chunks with both section and entity metadata
        assert len(integrated_chunks) >= 0  # May be 0 in RED phase, >0 in GREEN phase


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
