"""Unit tests for sentence boundary edge cases (Story 3.1).

Tests AC-3.1-1, AC-3.1-6 edge cases.
"""

from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import Mock

import pytest

# These imports will fail until implementation exists (RED phase)
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


class TestVeryLongSentences:
    """Test handling of sentences exceeding chunk_size (AC-3.1-6)."""

    def test_very_long_sentence_becomes_single_chunk(self):
        """Should yield entire long sentence as single chunk when sentence > chunk_size."""
        # GIVEN: Mock SentenceSegmenter returning very long sentence (>512 tokens)
        mock_segmenter = Mock()
        very_long_sentence = " ".join(["word"] * 600)  # ~600 tokens, exceeds default 512
        mock_segmenter.segment.return_value = [very_long_sentence]

        # GIVEN: Document with very long sentence
        document = Document(
            id="long_sentence_doc",
            text=very_long_sentence,
            entities=[],
            metadata=create_test_metadata("test.pdf"),
            structure={},
        )

        # GIVEN: ProcessingContext with mock logger
        mock_logger = Mock()
        context = ProcessingContext(config={}, logger=mock_logger, metrics={})

        # WHEN: Chunking with default chunk_size=512
        engine = ChunkingEngine(segmenter=mock_segmenter, chunk_size=512, overlap_pct=0.0)
        chunks = engine.process(document, context)

        # THEN: Single chunk created containing entire sentence
        assert len(chunks) == 1
        assert chunks[0].text == very_long_sentence
        assert chunks[0].token_count > 512  # Exceeds chunk_size

        # THEN: Warning logged via context.logger
        mock_logger.warning.assert_called()

    def test_multiple_long_sentences_each_become_chunks(self):
        """Should handle multiple long sentences, each as separate chunk."""
        # GIVEN: Mock SentenceSegmenter with multiple long sentences
        mock_segmenter = Mock()
        long_sentence_1 = " ".join(["alpha"] * 600)
        long_sentence_2 = " ".join(["beta"] * 700)
        mock_segmenter.segment.return_value = [long_sentence_1, long_sentence_2]

        # GIVEN: Document
        document = Document(
            id="multi_long_doc",
            text=long_sentence_1 + " " + long_sentence_2,
            entities=[],
            metadata=create_test_metadata("test.pdf"),
            structure={},
        )

        # GIVEN: ProcessingContext
        context = ProcessingContext(config={}, logger=Mock(), metrics={})

        # WHEN: Chunking
        engine = ChunkingEngine(segmenter=mock_segmenter, chunk_size=512, overlap_pct=0.0)
        chunks = engine.process(document, context)

        # THEN: Two chunks created
        assert len(chunks) == 2
        assert chunks[0].text == long_sentence_1
        assert chunks[1].text == long_sentence_2


class TestMicroSentences:
    """Test handling of very short sentences (AC-3.1-6)."""

    def test_micro_sentences_combined_until_chunk_size(self):
        """Should combine micro-sentences (<10 chars) with adjacent sentences."""
        # GIVEN: Mock SentenceSegmenter with micro-sentences
        mock_segmenter = Mock()
        micro_sentences = ["Hi.", "Ok.", "Yes.", "No.", "Good."]  # Each <10 chars
        mock_segmenter.segment.return_value = micro_sentences

        # GIVEN: Document
        document = Document(
            id="micro_doc",
            text=" ".join(micro_sentences),
            entities=[],
            metadata=create_test_metadata("test.pdf"),
            structure={},
        )

        # GIVEN: ProcessingContext
        context = ProcessingContext(config={}, logger=Mock(), metrics={})

        # WHEN: Chunking with default chunk_size=512
        engine = ChunkingEngine(segmenter=mock_segmenter, chunk_size=512, overlap_pct=0.0)
        chunks = engine.process(document, context)

        # THEN: Micro-sentences combined into single chunk
        assert len(chunks) == 1
        assert all(sent in chunks[0].text for sent in micro_sentences)

    def test_mixed_micro_and_normal_sentences(self):
        """Should combine micro-sentences with adjacent normal sentences."""
        # GIVEN: Mock SentenceSegmenter with mixed sentence lengths
        mock_segmenter = Mock()
        sentences = [
            "Ok.",  # Micro
            "This is a normal length sentence with adequate content.",  # Normal
            "Yes.",  # Micro
            "Another normal sentence here with sufficient length.",  # Normal
        ]
        mock_segmenter.segment.return_value = sentences

        # GIVEN: Document
        document = Document(
            id="mixed_doc",
            text=" ".join(sentences),
            entities=[],
            metadata=create_test_metadata("test.pdf"),
            structure={},
        )

        # GIVEN: ProcessingContext
        context = ProcessingContext(config={}, logger=Mock(), metrics={})

        # WHEN: Chunking
        engine = ChunkingEngine(segmenter=mock_segmenter, chunk_size=512, overlap_pct=0.0)
        chunks = engine.process(document, context)

        # THEN: Sentences combined intelligently (micro + normal)
        assert len(chunks) >= 1
        # Exact chunking depends on implementation, but should preserve all content
        full_text = " ".join(chunk.text for chunk in chunks)
        assert all(sent in full_text for sent in sentences)


class TestNoPunctuation:
    """Test handling of text without punctuation (AC-3.1-6)."""

    def test_no_punctuation_uses_spacy_statistical_model(self):
        """Should handle text without punctuation via spaCy statistical model."""
        # GIVEN: Mock SentenceSegmenter (spaCy uses statistical model for no punctuation)
        mock_segmenter = Mock()
        # Simulate spaCy splitting text statistically
        mock_segmenter.segment.return_value = [
            "this is text without any punctuation marks",
            "it should still be split by spacy statistical model",
        ]

        # GIVEN: Document without punctuation
        document = Document(
            id="no_punct_doc",
            text="this is text without any punctuation marks it should still be split",
            entities=[],
            metadata=create_test_metadata("test.pdf"),
            structure={},
        )

        # GIVEN: ProcessingContext
        context = ProcessingContext(config={}, logger=Mock(), metrics={})

        # WHEN: Chunking
        engine = ChunkingEngine(segmenter=mock_segmenter, chunk_size=512, overlap_pct=0.0)
        chunks = engine.process(document, context)

        # THEN: Chunks created using spaCy segmentation
        assert len(chunks) >= 1
        assert mock_segmenter.segment.called


class TestEmptyDocuments:
    """Test handling of empty or minimal documents (AC-3.1-6)."""

    def test_empty_document_returns_no_chunks(self):
        """Should return empty iterator for empty normalized document."""
        # GIVEN: Mock SentenceSegmenter returning empty list
        mock_segmenter = Mock()
        mock_segmenter.segment.return_value = []

        # GIVEN: Empty document
        document = Document(
            id="empty_doc",
            text="",
            entities=[],
            metadata=create_test_metadata("empty.pdf"),
            structure={},
        )

        # GIVEN: ProcessingContext with mock logger
        mock_logger = Mock()
        context = ProcessingContext(config={}, logger=mock_logger, metrics={})

        # WHEN: Chunking empty document
        engine = ChunkingEngine(segmenter=mock_segmenter, chunk_size=512, overlap_pct=0.0)
        chunks = engine.process(document, context)

        # THEN: No chunks produced
        assert len(chunks) == 0

        # THEN: Info logged (not error)
        mock_logger.info.assert_called()

    def test_whitespace_only_document(self):
        """Should handle document with only whitespace."""
        # GIVEN: Mock SentenceSegmenter
        mock_segmenter = Mock()
        mock_segmenter.segment.return_value = []

        # GIVEN: Whitespace-only document
        document = Document(
            id="whitespace_doc",
            text="   \n\n\t   ",
            entities=[],
            metadata=create_test_metadata("whitespace.pdf"),
            structure={},
        )

        # GIVEN: ProcessingContext
        context = ProcessingContext(config={}, logger=Mock(), metrics={})

        # WHEN: Chunking
        engine = ChunkingEngine(segmenter=mock_segmenter, chunk_size=512, overlap_pct=0.0)
        chunks = engine.process(document, context)

        # THEN: No chunks produced
        assert len(chunks) == 0


class TestShortSections:
    """Test handling of sections shorter than chunk_size (AC-3.1-6)."""

    def test_short_section_becomes_single_chunk(self):
        """Should not artificially split sections shorter than chunk_size."""
        # GIVEN: Mock SentenceSegmenter with short section
        mock_segmenter = Mock()
        sentences = ["Section heading.", "Brief content here."]
        mock_segmenter.segment.return_value = sentences

        # GIVEN: Document with short section
        document = Document(
            id="short_section_doc",
            text=" ".join(sentences),
            entities=[],
            metadata=create_test_metadata("policy.pdf"),
            structure={"sections": [{"title": "Section heading", "length": 50}]},
        )

        # GIVEN: ProcessingContext
        context = ProcessingContext(config={}, logger=Mock(), metrics={})

        # WHEN: Chunking with large chunk_size
        engine = ChunkingEngine(segmenter=mock_segmenter, chunk_size=512, overlap_pct=0.0)
        chunks = engine.process(document, context)

        # THEN: Single chunk containing entire section
        assert len(chunks) == 1
        assert all(sent in chunks[0].text for sent in sentences)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
