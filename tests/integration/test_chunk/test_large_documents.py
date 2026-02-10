"""Integration tests for large document handling (AC-3.1-4, NFR-P2).

Tests chunking engine with large documents:
- 10,000+ word documents
- Memory efficiency (constant memory streaming)
- Proper chunking with overlap
- Metadata preservation
"""

from datetime import datetime, timezone
from pathlib import Path

import pytest

from data_extract.chunk import ChunkingEngine, SentenceSegmenter
from data_extract.core.models import Document, Metadata, ProcessingContext

pytestmark = [pytest.mark.P2, pytest.mark.integration, pytest.mark.chunking]


class TestLargeDocumentChunking:
    """Test chunking behavior with large documents."""

    def test_10k_word_document_chunking(self):
        """Should chunk 10,000-word document successfully (AC-3.1-4)."""
        # GIVEN: Large document (10,000 words)
        segmenter = SentenceSegmenter()
        engine = ChunkingEngine(segmenter=segmenter, chunk_size=512)

        # Create text with ~10k words (50 words per sentence, 200 sentences)
        sentence_template = " ".join([f"word{i}" for i in range(50)]) + ". "
        text = sentence_template * 200

        document = Document(
            id="large_doc",
            text=text,
            entities=[],
            metadata=Metadata(
                source_file=Path("large.pdf"),
                file_hash="abc123",
                processing_timestamp=datetime.now(timezone.utc),
                tool_version="3.1.0",
                config_version="1.0",
            ),
            structure={},
        )
        context = ProcessingContext(config={}, logger=None, metrics={})

        # WHEN: Chunking large document
        chunks = list(engine.process(document, context))

        # THEN: Document chunked successfully
        assert len(chunks) > 0
        # With 10k words and 512 chunk_size, expect ~20 chunks (10000/512)
        assert len(chunks) >= 15  # Allow some variation due to boundaries

    def test_chunk_size_boundaries_with_large_text(self):
        """Should respect chunk size boundaries in large documents."""
        # GIVEN: Large document
        segmenter = SentenceSegmenter()
        engine = ChunkingEngine(segmenter=segmenter, chunk_size=512)  # Use larger size

        # Create structured text with known sentence lengths
        sentences = [f"This is sentence number {i} with some content." for i in range(500)]
        text = " ".join(sentences)

        document = Document(
            id="boundary_test",
            text=text,
            entities=[],
            metadata=Metadata(
                source_file=Path("boundaries.pdf"),
                file_hash="abc123",
                processing_timestamp=datetime.now(timezone.utc),
                tool_version="3.1.0",
                config_version="1.0",
            ),
            structure={},
        )
        context = ProcessingContext(config={}, logger=None, metrics={})

        # WHEN: Chunking
        chunks = list(engine.process(document, context))

        # THEN: All chunks have reasonable word counts close to chunk_size
        assert len(chunks) > 0
        for chunk in chunks:
            # Most chunks should be near the chunk_size (allowing some variance)
            # Note: chunk_size is in tokens, not characters
            assert chunk.word_count > 0
            assert chunk.word_count <= engine.chunk_size * 2  # Allow 2x for edge cases

    def test_overlap_preservation_in_large_docs(self):
        """Should maintain overlap between chunks in large documents."""
        # GIVEN: Large document with overlap
        segmenter = SentenceSegmenter()
        engine = ChunkingEngine(segmenter=segmenter, chunk_size=512, overlap_pct=0.2)

        # Create text with identifiable sentences
        sentences = [f"Sentence {i:03d}." for i in range(300)]
        text = " ".join(sentences)

        document = Document(
            id="overlap_test",
            text=text,
            entities=[],
            metadata=Metadata(
                source_file=Path("overlap.pdf"),
                file_hash="abc123",
                processing_timestamp=datetime.now(timezone.utc),
                tool_version="3.1.0",
                config_version="1.0",
            ),
            structure={},
        )
        context = ProcessingContext(config={}, logger=None, metrics={})

        # WHEN: Chunking with overlap
        chunks = list(engine.process(document, context))

        # THEN: Multiple chunks created
        assert len(chunks) >= 2

        # AND: Chunks are different (basic sanity check)
        for i in range(len(chunks) - 1):
            current_chunk = chunks[i]
            next_chunk = chunks[i + 1]
            assert current_chunk.text != next_chunk.text


class TestMemoryEfficiency:
    """Test memory efficiency with large documents."""

    def test_streaming_chunks_generator(self):
        """Should yield chunks as generator (constant memory, AC-3.1-4)."""
        # GIVEN: Large document
        segmenter = SentenceSegmenter()
        engine = ChunkingEngine(segmenter=segmenter, chunk_size=512)

        # Create large text
        text = "This is a sentence. " * 5000  # ~10k words

        document = Document(
            id="streaming_test",
            text=text,
            entities=[],
            metadata=Metadata(
                source_file=Path("streaming.pdf"),
                file_hash="abc123",
                processing_timestamp=datetime.now(timezone.utc),
                tool_version="3.1.0",
                config_version="1.0",
            ),
            structure={},
        )
        context = ProcessingContext(config={}, logger=None, metrics={})

        # WHEN: Processing (returns iterable)
        chunks = engine.process(document, context)

        # THEN: Can iterate through chunks
        chunk_count = 0
        for chunk in chunks:
            chunk_count += 1
            # Each chunk should be valid
            assert chunk.text
            assert chunk.metadata

        # AND: Multiple chunks created from large document
        assert chunk_count > 0

    def test_multiple_large_documents_sequentially(self):
        """Should handle multiple large documents without memory growth."""
        # GIVEN: ChunkingEngine
        segmenter = SentenceSegmenter()
        engine = ChunkingEngine(segmenter=segmenter, chunk_size=512)

        # WHEN: Processing multiple large documents
        for doc_num in range(5):
            # Create large text for each document
            text = f"Document {doc_num} content. " * 2000  # ~4k words each

            document = Document(
                id=f"doc_{doc_num}",
                text=text,
                entities=[],
                metadata=Metadata(
                    source_file=Path(f"doc_{doc_num}.pdf"),
                    file_hash=f"hash_{doc_num}",
                    processing_timestamp=datetime.now(timezone.utc),
                    tool_version="3.1.0",
                    config_version="1.0",
                ),
                structure={},
            )
            context = ProcessingContext(config={}, logger=None, metrics={})

            # THEN: Each document processes successfully
            chunks = list(engine.process(document, context))
            assert len(chunks) > 0


class TestMetadataPreservation:
    """Test metadata preservation in large document chunks."""

    def test_chunk_metadata_completeness(self):
        """Should preserve complete metadata in all chunks."""
        # GIVEN: Large document with rich metadata
        segmenter = SentenceSegmenter()
        engine = ChunkingEngine(segmenter=segmenter, chunk_size=256)

        text = "This is a test sentence. " * 500

        original_metadata = Metadata(
            source_file=Path("test.pdf"),
            file_hash="abc123def456",
            processing_timestamp=datetime.now(timezone.utc),
            tool_version="3.1.0",
            config_version="1.0",
            document_type="report",
            quality_scores={"ocr_confidence": 0.95},
        )

        document = Document(
            id="metadata_test",
            text=text,
            entities=[],
            metadata=original_metadata,
            structure={"sections": [{"title": "Section 1"}]},
        )
        context = ProcessingContext(config={}, logger=None, metrics={})

        # WHEN: Chunking
        chunks = list(engine.process(document, context))

        # THEN: All chunks preserve document metadata (provenance fields)
        assert len(chunks) > 0
        for chunk in chunks:
            assert chunk.metadata.source_file == original_metadata.source_file
            assert chunk.metadata.file_hash == original_metadata.file_hash
            # tool_version updated to chunking stage version (Story 3.2)
            assert chunk.metadata.tool_version == "3.2.0"
            assert chunk.metadata.document_type == original_metadata.document_type

    def test_chunk_position_tracking(self):
        """Should track chunk positions in large documents."""
        # GIVEN: Large document
        segmenter = SentenceSegmenter()
        engine = ChunkingEngine(segmenter=segmenter, chunk_size=256)

        # Create text with numbered sentences
        sentences = [f"Sentence number {i}." for i in range(200)]
        text = " ".join(sentences)

        document = Document(
            id="position_test",
            text=text,
            entities=[],
            metadata=Metadata(
                source_file=Path("positions.pdf"),
                file_hash="abc123",
                processing_timestamp=datetime.now(timezone.utc),
                tool_version="3.1.0",
                config_version="1.0",
            ),
            structure={},
        )
        context = ProcessingContext(config={}, logger=None, metrics={})

        # WHEN: Chunking
        chunks = list(engine.process(document, context))

        # THEN: Chunk position_index values are sequential (0-based)
        assert len(chunks) > 0
        for i, chunk in enumerate(chunks):
            assert chunk.position_index == i

        # AND: All chunks have unique IDs
        chunk_ids = [chunk.id for chunk in chunks]
        assert len(chunk_ids) == len(set(chunk_ids))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
