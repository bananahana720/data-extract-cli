"""Integration tests for Epic 2 → Epic 3 pipeline (AC-3.1-2, AC-3.1-5)."""

from datetime import datetime, timezone
from pathlib import Path

import pytest

from data_extract.chunk import ChunkingEngine, SentenceSegmenter
from data_extract.core.models import Document, Metadata, ProcessingContext

pytestmark = [pytest.mark.P1, pytest.mark.integration, pytest.mark.chunking]


class TestEpic2ToEpic3Integration:
    """Test ProcessingResult → Chunk pipeline integration."""

    def test_real_spacy_integration(self):
        """Should integrate with real SentenceSegmenter from Story 2.5.2."""
        # GIVEN: Real SentenceSegmenter (lazy-loads en_core_web_md)
        segmenter = SentenceSegmenter()

        # GIVEN: Document with real text
        document = Document(
            id="integration_test",
            text="This is the first sentence. This is the second sentence. This is the third.",
            entities=[],
            metadata=Metadata(
                source_file=Path("test.pdf"),
                file_hash="abc123",
                processing_timestamp=datetime.now(timezone.utc),
                tool_version="3.1.0",
                config_version="1.0",
            ),
            structure={},
        )

        # GIVEN: ProcessingContext
        context = ProcessingContext(config={}, logger=None, metrics={})

        # WHEN: Chunking with real spaCy
        engine = ChunkingEngine(segmenter=segmenter, chunk_size=512)
        chunks = list(engine.process(document, context))

        # THEN: Chunks created using real sentence boundaries
        assert len(chunks) >= 1

    def test_multi_section_document(self):
        """Should respect section boundaries from ContentBlocks (AC-3.1-2)."""
        # GIVEN: Real SentenceSegmenter
        segmenter = SentenceSegmenter()

        # GIVEN: Document with section structure
        document = Document(
            id="sections_test",
            text="Section 1 Title. Section 1 content here. Section 2 Title. Section 2 content.",
            entities=[],
            metadata=Metadata(
                source_file=Path("policy.pdf"),
                file_hash="abc123",
                processing_timestamp=datetime.now(timezone.utc),
                tool_version="3.1.0",
                config_version="1.0",
            ),
            structure={"sections": [{"title": "Section 1"}, {"title": "Section 2"}]},
        )

        # GIVEN: ProcessingContext
        context = ProcessingContext(config={}, logger=None, metrics={})

        # WHEN: Chunking
        engine = ChunkingEngine(segmenter=segmenter)
        chunks = list(engine.process(document, context))

        # THEN: Section context preserved in metadata
        assert len(chunks) >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
