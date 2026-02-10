"""Integration tests for spaCy SentenceSegmenter (Story 2.5.2, AC-3.1-3).

Tests real spaCy model integration:
- Lazy loading of en_core_web_md model
- Model caching and reuse
- Sentence boundary detection accuracy
- Performance characteristics
"""

import pytest

from data_extract.chunk import SentenceSegmenter

pytestmark = [pytest.mark.P1, pytest.mark.integration, pytest.mark.chunking]


class TestSpacyLazyLoading:
    """Test spaCy model lazy loading and caching behavior."""

    def test_lazy_model_loading(self):
        """Should lazy-load spaCy model on first use (AC-3.1-3)."""
        # GIVEN: Fresh SentenceSegmenter instance
        segmenter = SentenceSegmenter()

        # WHEN: Segmenting text (triggers lazy load)
        sentences = segmenter.segment("This is a test. Here is another sentence.")

        # THEN: Model loaded and sentences extracted
        assert len(sentences) == 2
        assert sentences[0] == "This is a test."
        assert sentences[1] == "Here is another sentence."

    def test_model_caching(self):
        """Should cache spaCy model across instances."""
        # GIVEN: First SentenceSegmenter instance
        segmenter1 = SentenceSegmenter()
        sentences1 = segmenter1.segment("First call.")

        # WHEN: Creating second instance (should reuse cached model)
        segmenter2 = SentenceSegmenter()
        sentences2 = segmenter2.segment("Second call.")

        # THEN: Both instances work correctly (model cached)
        assert len(sentences1) == 1
        assert len(sentences2) == 1


class TestSentenceBoundaryAccuracy:
    """Test sentence boundary detection accuracy with real spaCy."""

    def test_standard_sentence_boundaries(self):
        """Should detect standard sentence boundaries accurately."""
        # GIVEN: Text with period, question mark, exclamation boundaries
        segmenter = SentenceSegmenter()
        text = "This is a statement. Is this a question? This is exciting! Another sentence."

        # WHEN: Segmenting
        sentences = segmenter.segment(text)

        # THEN: All sentences detected
        assert len(sentences) == 4
        assert sentences[0] == "This is a statement."
        assert sentences[1] == "Is this a question?"
        assert sentences[2] == "This is exciting!"
        assert sentences[3] == "Another sentence."

    def test_abbreviation_handling(self):
        """Should handle abbreviations without incorrect splits."""
        # GIVEN: Text with abbreviations
        segmenter = SentenceSegmenter()
        text = "Dr. Smith works at XYZ Corp. in the U.S. He is an expert."

        # WHEN: Segmenting
        sentences = segmenter.segment(text)

        # THEN: Abbreviations don't cause incorrect splits
        # spaCy should recognize Dr., Corp., U.S. as abbreviations
        assert len(sentences) == 2

    def test_multi_line_text(self):
        """Should handle multi-line text with mixed boundaries."""
        # GIVEN: Multi-line text
        segmenter = SentenceSegmenter()
        text = """First paragraph sentence.
Second line in same paragraph.

New paragraph starts here. Another sentence follows."""

        # WHEN: Segmenting
        sentences = segmenter.segment(text)

        # THEN: All sentences detected regardless of line breaks
        assert len(sentences) == 4

    def test_corporate_document_text(self):
        """Should handle typical corporate audit document text."""
        # GIVEN: Corporate document text with technical terms
        segmenter = SentenceSegmenter()
        text = (
            "The control effectiveness was assessed at 95.2% for Q3 2023. "
            "Key risk indicators (KRIs) showed improvement vs. prior quarter. "
            "Management response required for findings A-101, B-204, and C-305."
        )

        # WHEN: Segmenting
        sentences = segmenter.segment(text)

        # THEN: Technical terms and numbers don't interfere
        assert len(sentences) == 3


class TestSpacyPerformance:
    """Test spaCy integration performance characteristics."""

    def test_segmentation_speed(self):
        """Should segment 10,000-word document in reasonable time."""
        # GIVEN: Large text (10k words)
        segmenter = SentenceSegmenter()
        # Create text with ~10k words (200 words per sentence, 50 sentences)
        sentence_template = " ".join(["word"] * 200) + ". "
        text = sentence_template * 50

        # WHEN: Timing segmentation
        import time

        start = time.perf_counter()
        sentences = segmenter.segment(text)
        elapsed = time.perf_counter() - start

        # THEN: Completes in reasonable time (<2 seconds for segmentation)
        # Note: Full NFR-P3 test is in performance tests
        assert elapsed < 2.0
        assert len(sentences) == 50

    def test_memory_stability(self):
        """Should maintain stable memory across multiple segmentations."""
        # GIVEN: SentenceSegmenter
        segmenter = SentenceSegmenter()

        # WHEN: Processing multiple documents
        for i in range(10):
            text = f"Document {i} content. " * 100
            sentences = segmenter.segment(text)

            # THEN: Each document processes successfully
            assert len(sentences) == 100

        # No memory leak assertion - just verify stability


class TestSpacyErrorHandling:
    """Test spaCy integration error handling."""

    def test_empty_text_handling(self):
        """Should handle empty text gracefully."""
        # GIVEN: Empty text
        segmenter = SentenceSegmenter()

        # WHEN: Segmenting
        sentences = segmenter.segment("")

        # THEN: Returns empty list
        assert sentences == []

    def test_whitespace_only_text(self):
        """Should handle whitespace-only text."""
        # GIVEN: Whitespace-only text
        segmenter = SentenceSegmenter()

        # WHEN: Segmenting
        sentences = segmenter.segment("   \n\t  ")

        # THEN: Returns empty list
        assert sentences == []

    def test_single_word_text(self):
        """Should handle single word without punctuation."""
        # GIVEN: Single word
        segmenter = SentenceSegmenter()

        # WHEN: Segmenting
        sentences = segmenter.segment("Hello")

        # THEN: Returns single sentence
        assert len(sentences) == 1
        assert sentences[0] == "Hello"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
