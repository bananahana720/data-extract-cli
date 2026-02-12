"""Unit tests for nlp utilities.

Tests for get_sentence_boundaries() function covering:
- Input validation (empty text, whitespace)
- Sentence boundary detection accuracy
- Lazy loading behavior
- Model caching
- Error handling for missing model
"""

import time
from unittest.mock import patch

import pytest
import spacy

from src.data_extract.utils.nlp import get_sentence_boundaries

pytestmark = [pytest.mark.P1, pytest.mark.unit]


def _load_test_nlp_model():
    """Load preferred spaCy model with local lightweight fallback for offline environments."""
    try:
        return spacy.load("en_core_web_md")
    except OSError:
        nlp = spacy.blank("en")
        if "sentencizer" not in nlp.pipe_names:
            nlp.add_pipe("sentencizer")
        return nlp


class TestGetSentenceBoundaries:
    """Test suite for get_sentence_boundaries() function."""

    def test_empty_text_raises_valueerror(self) -> None:
        """AC 2.5.2-5: Empty text should raise ValueError."""
        with pytest.raises(ValueError, match="Input text cannot be empty"):
            get_sentence_boundaries("")

    def test_whitespace_only_raises_valueerror(self) -> None:
        """AC 2.5.2-5: Whitespace-only text should raise ValueError."""
        with pytest.raises(ValueError, match="Input text cannot be empty"):
            get_sentence_boundaries("   \n\t  ")

    def test_single_sentence_returns_one_boundary(self) -> None:
        """AC 2.5.2-5: Single sentence should return one boundary position."""
        text = "This is a single sentence."
        boundaries = get_sentence_boundaries(text)

        assert len(boundaries) == 1
        assert boundaries[0] == len(text)

    def test_multi_sentence_returns_multiple_boundaries(self) -> None:
        """AC 2.5.2-5: Multiple sentences should return multiple boundaries."""
        text = "First sentence. Second sentence. Third sentence."
        boundaries = get_sentence_boundaries(text)

        assert len(boundaries) == 3
        assert boundaries[0] == len("First sentence.")
        assert boundaries[1] == len("First sentence. Second sentence.")
        assert boundaries[2] == len(text)

    def test_with_abbreviations(self) -> None:
        """AC 2.5.2-5: Should handle abbreviations correctly (Dr., Inc., U.S.)."""
        text = "Dr. Smith visited Inc. Ltd. in the U.S. last year. This is sentence two."
        boundaries = get_sentence_boundaries(text)

        # Should detect 2 sentences, not split on abbreviations
        assert len(boundaries) == 2
        # First boundary should be after "last year."
        assert boundaries[0] < len(text)
        assert boundaries[1] == len(text)

    def test_with_provided_nlp_model(self) -> None:
        """AC 2.5.2-5: Should work with pre-loaded nlp parameter."""
        nlp = _load_test_nlp_model()
        text = "First sentence. Second sentence."
        boundaries = get_sentence_boundaries(text, nlp=nlp)

        assert len(boundaries) == 2
        assert boundaries == [15, 32]

    def test_lazy_loading_without_nlp_parameter(self) -> None:
        """AC 2.5.2-5: Should lazy load model when nlp=None."""
        # Clear module cache to test lazy loading
        import src.data_extract.utils.nlp as nlp_module

        original_cache = nlp_module._nlp_model
        nlp_module._nlp_model = None

        try:
            text = "Test sentence."
            boundaries = get_sentence_boundaries(text)

            # Should have loaded and cached model
            assert nlp_module._nlp_model is not None
            assert len(boundaries) == 1
        finally:
            # Restore original cache
            nlp_module._nlp_model = original_cache

    def test_boundary_positions_are_character_offsets(self) -> None:
        """AC 2.5.2-5: Boundary positions should be zero-indexed character offsets."""
        text = "Hello. World."
        boundaries = get_sentence_boundaries(text)

        # Verify boundaries are character positions
        assert boundaries[0] == 6  # After "Hello."
        assert boundaries[1] == 13  # After "World."

        # Verify we can slice text using boundaries
        first_sentence = text[: boundaries[0]]
        assert first_sentence == "Hello."

    def test_complex_punctuation(self) -> None:
        """AC 2.5.2-5: Should handle complex punctuation (quotes, ellipsis, parentheses)."""
        text = 'He said, "Hello there!" She replied. Then he left...'
        boundaries = get_sentence_boundaries(text)

        # Should handle quotes and ellipsis correctly
        assert len(boundaries) >= 2

    def test_multi_paragraph_text(self) -> None:
        """AC 2.5.2-5: Should handle multi-paragraph text."""
        text = "First paragraph sentence one. Sentence two.\n\nSecond paragraph sentence."
        boundaries = get_sentence_boundaries(text)

        assert len(boundaries) == 3
        assert boundaries[-1] == len(text)

    def test_performance_under_100ms(self) -> None:
        """AC 2.5.2-5 & NFR-P1: All unit tests should execute in <100ms."""
        # Pre-load model to exclude model loading time
        nlp = _load_test_nlp_model()

        text = "This is a test sentence. " * 10  # 10 sentences
        start = time.perf_counter()
        boundaries = get_sentence_boundaries(text, nlp=nlp)
        elapsed = time.perf_counter() - start

        assert len(boundaries) == 10
        # Individual test should be much faster than 100ms
        assert elapsed < 0.1, f"Test took {elapsed:.3f}s, expected <0.1s"

    def test_missing_model_uses_fallback_sentencizer(self) -> None:
        """Missing en_core_web_md should fall back to blank+sentencizer in dev mode."""
        import src.data_extract.utils.nlp as nlp_module

        original_cache = nlp_module._nlp_model
        nlp_module._nlp_model = None

        try:
            with patch("spacy.load", side_effect=OSError("Model not found")):
                boundaries = get_sentence_boundaries("Test text.")
                assert boundaries == [10]
                assert nlp_module._nlp_model is not None
                assert "sentencizer" in nlp_module._nlp_model.pipe_names
        finally:
            nlp_module._nlp_model = original_cache

    def test_single_word_returns_one_boundary(self) -> None:
        """Edge case: Single word should return one boundary."""
        text = "Hello"
        boundaries = get_sentence_boundaries(text)

        assert len(boundaries) == 1
        assert boundaries[0] == 5

    def test_multiple_spaces_between_sentences(self) -> None:
        """Edge case: Multiple spaces between sentences should be handled."""
        text = "First sentence.   Second sentence."
        boundaries = get_sentence_boundaries(text)

        assert len(boundaries) == 2
        assert boundaries[1] == len(text)

    def test_model_caching_behavior(self) -> None:
        """Verify model is loaded once and cached for subsequent calls."""
        import src.data_extract.utils.nlp as nlp_module

        original_cache = nlp_module._nlp_model
        nlp_module._nlp_model = None

        try:
            # First call should load model
            get_sentence_boundaries("First call.")
            first_model = nlp_module._nlp_model

            # Second call should reuse cached model
            get_sentence_boundaries("Second call.")
            second_model = nlp_module._nlp_model

            assert first_model is second_model, "Model should be cached and reused"
        finally:
            nlp_module._nlp_model = original_cache


@pytest.mark.unit
class TestSentenceBoundaryEdgeCases:
    """Additional edge case tests for sentence boundary detection."""

    def test_numbers_and_periods(self) -> None:
        """Numbers with periods should not cause incorrect splits."""
        text = "The value is 3.14159. This is the next sentence."
        boundaries = get_sentence_boundaries(text)

        assert len(boundaries) == 2

    def test_urls_in_text(self) -> None:
        """URLs with periods should not cause incorrect splits."""
        text = "Visit example.com for details. Then see other sites."
        boundaries = get_sentence_boundaries(text)

        # Should detect 2 sentences, not split on domain periods
        assert len(boundaries) == 2

    def test_acronyms_all_caps(self) -> None:
        """All-caps acronyms should be handled correctly."""
        text = "NASA launched the rocket. The U.S.A. celebrated."
        boundaries = get_sentence_boundaries(text)

        assert len(boundaries) == 2

    def test_exclamation_and_question_marks(self) -> None:
        """Should handle ! and ? as sentence boundaries."""
        text = "Really? Yes! Maybe not."
        boundaries = get_sentence_boundaries(text)

        assert len(boundaries) == 3

    def test_acronym_sentence_end_splits_correctly(self) -> None:
        """Acronym-ending sentence should split when next sentence starts uppercase."""
        text = "Dr. Smith works at XYZ Corp. in the U.S. He is an expert."
        boundaries = get_sentence_boundaries(text)

        assert len(boundaries) == 2
