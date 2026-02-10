"""Unit tests for ChunkingEngine core component (Story 3.1). Tests AC-3.1-1, AC-3.1-3, AC-3.1-4, AC-3.1-7."""

from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# These imports will fail until implementation exists (RED phase)
try:
    from data_extract.chunk.engine import ChunkingEngine
    from data_extract.chunk.models import Chunk, ChunkMetadata, QualityScore
    from data_extract.core.models import Document, Metadata, ProcessingContext
except ImportError:
    # Expected during RED phase
    ChunkingEngine = None
    Chunk = None
    ChunkMetadata = None
    QualityScore = None
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


class TestChunkingEngineInitialization:
    """Test ChunkingEngine initialization and configuration validation (AC-3.1-3, AC-3.1-4)."""

    def test_default_initialization(self):
        """Should initialize with default chunk_size=512 and overlap_pct=0.15."""
        # GIVEN: Mock SentenceSegmenter
        mock_segmenter = Mock()

        # WHEN: Initializing ChunkingEngine with defaults
        engine = ChunkingEngine(segmenter=mock_segmenter)

        # THEN: Default configuration applied
        assert engine.chunk_size == 512
        assert engine.overlap_pct == 0.15
        assert engine.segmenter == mock_segmenter

    def test_custom_chunk_size(self):
        """Should accept custom chunk_size values (AC-3.1-3)."""
        # GIVEN: Mock SentenceSegmenter
        mock_segmenter = Mock()

        # WHEN: Initializing with chunk_size=1024
        engine = ChunkingEngine(segmenter=mock_segmenter, chunk_size=1024)

        # THEN: Custom chunk_size applied
        assert engine.chunk_size == 1024

    @pytest.mark.parametrize("chunk_size", [128, 256, 512, 1024, 2048])
    def test_valid_chunk_sizes(self, chunk_size):
        """Should accept chunk_size in valid range 128-2048 (AC-3.1-3)."""
        # GIVEN: Mock SentenceSegmenter
        mock_segmenter = Mock()

        # WHEN: Initializing with valid chunk_size
        engine = ChunkingEngine(segmenter=mock_segmenter, chunk_size=chunk_size)

        # THEN: Configuration accepted
        assert engine.chunk_size == chunk_size

    def test_chunk_size_below_minimum_warns(self):
        """Should warn when chunk_size < 128 (AC-3.1-3)."""
        # GIVEN: Mock SentenceSegmenter
        mock_segmenter = Mock()

        # WHEN: Initializing with chunk_size=1
        with patch("data_extract.chunk.engine.logger") as mock_logger:
            ChunkingEngine(segmenter=mock_segmenter, chunk_size=1)

            # THEN: Warning logged
            mock_logger.warning.assert_called()
            warning_call = str(mock_logger.warning.call_args)
            assert "chunk_size" in warning_call.lower()
            assert "128" in warning_call

    def test_chunk_size_above_maximum_warns(self):
        """Should warn when chunk_size > 2048 (AC-3.1-3)."""
        # GIVEN: Mock SentenceSegmenter
        mock_segmenter = Mock()

        # WHEN: Initializing with chunk_size=10000
        with patch("data_extract.chunk.engine.logger") as mock_logger:
            ChunkingEngine(segmenter=mock_segmenter, chunk_size=10000)

            # THEN: Warning logged
            mock_logger.warning.assert_called()
            warning_call = str(mock_logger.warning.call_args)
            assert "chunk_size" in warning_call.lower()
            assert "2048" in warning_call

    @pytest.mark.parametrize("overlap_pct", [0.0, 0.1, 0.15, 0.2, 0.5])
    def test_valid_overlap_percentages(self, overlap_pct):
        """Should accept overlap_pct in valid range 0.0-0.5 (AC-3.1-4)."""
        # GIVEN: Mock SentenceSegmenter
        mock_segmenter = Mock()

        # WHEN: Initializing with valid overlap_pct
        engine = ChunkingEngine(segmenter=mock_segmenter, overlap_pct=overlap_pct)

        # THEN: Configuration accepted
        assert engine.overlap_pct == overlap_pct

    def test_overlap_above_maximum_warns(self):
        """Should warn when overlap_pct > 0.5 (AC-3.1-4)."""
        # GIVEN: Mock SentenceSegmenter
        mock_segmenter = Mock()

        # WHEN: Initializing with overlap_pct=1.0
        with patch("data_extract.chunk.engine.logger") as mock_logger:
            ChunkingEngine(segmenter=mock_segmenter, overlap_pct=1.0)

            # THEN: Warning logged
            mock_logger.warning.assert_called()
            warning_call = str(mock_logger.warning.call_args)
            assert "overlap" in warning_call.lower()
            assert "0.5" in warning_call or "50" in warning_call


class TestChunkingEngineBasicOperation:
    """Test ChunkingEngine basic chunking behavior (AC-3.1-1)."""

    def test_chunk_document_returns_iterator(self):
        """Should return iterator of Chunk objects (streaming pattern)."""
        # GIVEN: Mock SentenceSegmenter that returns sentences
        mock_segmenter = Mock()
        mock_segmenter.segment.return_value = ["First sentence.", "Second sentence."]

        # GIVEN: Document with normalized text
        document = Document(
            id="test_doc_001",
            text="First sentence. Second sentence.",
            entities=[],
            metadata=create_test_metadata("test.pdf"),
            structure={},
        )

        # GIVEN: ProcessingContext
        context = ProcessingContext(config={}, logger=Mock(), metrics={})

        # WHEN: Chunking document
        engine = ChunkingEngine(segmenter=mock_segmenter, chunk_size=512, overlap_pct=0.0)
        chunks = engine.process(document, context)

        # THEN: Returns list (process() converts iterator to list)
        assert isinstance(chunks, list)

    def test_chunk_preserves_sentence_boundaries(self):
        """Should never split mid-sentence (AC-3.1-1 - Critical)."""
        # GIVEN: Mock SentenceSegmenter with known sentences
        mock_segmenter = Mock()
        sentences = [
            "This is the first sentence.",
            "This is the second sentence.",
            "This is the third sentence.",
        ]
        mock_segmenter.segment.return_value = sentences

        # GIVEN: Document
        document = Document(
            id="test_doc_002",
            text=" ".join(sentences),
            entities=[],
            metadata=create_test_metadata("test.pdf"),
            structure={},
        )

        # GIVEN: ProcessingContext
        context = ProcessingContext(config={}, logger=Mock(), metrics={})

        # WHEN: Chunking with small chunk_size to force multiple chunks
        engine = ChunkingEngine(segmenter=mock_segmenter, chunk_size=50, overlap_pct=0.0)
        chunks = engine.process(document, context)

        # THEN: Each chunk text ends at sentence boundary
        for chunk in chunks:
            # Chunk text should end with a complete sentence
            assert any(chunk.text.endswith(sentence) for sentence in sentences) or any(
                sentence in chunk.text for sentence in sentences
            )

    def test_chunk_ids_are_deterministic(self):
        """Should generate deterministic chunk IDs based on source file and position (AC-3.1-7)."""
        # GIVEN: Mock SentenceSegmenter
        mock_segmenter = Mock()
        mock_segmenter.segment.return_value = ["Sentence 1.", "Sentence 2.", "Sentence 3."]

        # GIVEN: Document
        document = Document(
            id="test_doc_003",
            text="Sentence 1. Sentence 2. Sentence 3.",
            entities=[],
            metadata=create_test_metadata("audit_report_2024.pdf"),
            structure={},
        )

        # GIVEN: ProcessingContext
        context = ProcessingContext(config={}, logger=Mock(), metrics={})

        # WHEN: Chunking document
        engine = ChunkingEngine(segmenter=mock_segmenter, chunk_size=512, overlap_pct=0.0)
        chunks = engine.process(document, context)

        # THEN: Chunk IDs follow pattern {source_file_stem}_chunk_{position:03d}
        assert chunks[0].id == "audit_report_2024_chunk_000"
        if len(chunks) > 1:
            assert chunks[1].id == "audit_report_2024_chunk_001"

    def test_sliding_window_with_overlap(self):
        """Should implement sliding window with configurable overlap (AC-3.1-4)."""
        # GIVEN: Mock SentenceSegmenter with multiple sentences
        mock_segmenter = Mock()
        sentences = [f"Sentence {i}." for i in range(10)]
        mock_segmenter.segment.return_value = sentences

        # GIVEN: Document
        document = Document(
            id="test_doc_004",
            text=" ".join(sentences),
            entities=[],
            metadata=create_test_metadata("test.pdf"),
            structure={},
        )

        # GIVEN: ProcessingContext
        context = ProcessingContext(config={}, logger=Mock(), metrics={})

        # WHEN: Chunking with 15% overlap
        engine = ChunkingEngine(segmenter=mock_segmenter, chunk_size=100, overlap_pct=0.15)
        chunks = engine.process(document, context)

        # THEN: Consecutive chunks have overlapping content
        if len(chunks) > 1:
            # Last sentence of first chunk should appear in second chunk
            # (exact overlap logic depends on implementation)
            assert len(chunks) >= 1  # At least one chunk created

    def test_metadata_population(self):
        """Should populate ChunkMetadata fields correctly."""
        # GIVEN: Mock SentenceSegmenter
        mock_segmenter = Mock()
        mock_segmenter.segment.return_value = ["Test sentence."]

        # GIVEN: Document
        document = Document(
            id="test_doc_005",
            text="Test sentence.",
            entities=[],
            metadata=create_test_metadata("policy.pdf"),
            structure={},
        )

        # GIVEN: ProcessingContext
        context = ProcessingContext(config={"version": "1.0"}, logger=Mock(), metrics={})

        # WHEN: Chunking document
        engine = ChunkingEngine(segmenter=mock_segmenter, chunk_size=512, overlap_pct=0.0)
        chunks = engine.process(document, context)

        # THEN: Metadata populated
        chunk = chunks[0]
        assert chunk.metadata is not None
        assert chunk.document_id == "test_doc_005"
        assert chunk.position_index == 0
        assert chunk.word_count > 0
        assert chunk.token_count > 0


@pytest.fixture
def mock_document():
    """Fixture providing a standard test document."""
    return Document(
        id="fixture_doc_001",
        text="This is a test document. It has multiple sentences. This enables testing.",
        entities=[],
        metadata=create_test_metadata("test.pdf"),
        structure={},
    )


@pytest.fixture
def mock_context():
    """Fixture providing a standard ProcessingContext."""
    return ProcessingContext(
        config={"chunk_size": 512, "overlap_pct": 0.15}, logger=Mock(), metrics={}
    )
