"""Integration tests for spaCy NLP pipeline.

Tests spaCy model loading, caching, sentence segmentation accuracy,
and performance benchmarks against requirements.
"""

import json
import time
from pathlib import Path
from unittest.mock import patch

import pytest
import spacy

from src.data_extract.utils.nlp import get_sentence_boundaries

pytestmark = [pytest.mark.P1, pytest.mark.integration]


@pytest.fixture(scope="module")
def nlp_model():
    """Load spaCy model once for all tests in this module."""
    return spacy.load("en_core_web_md")


@pytest.fixture(scope="module")
def gold_standard_corpus():
    """Load gold standard corpus for accuracy validation."""
    fixture_path = Path(__file__).parent.parent / "fixtures" / "spacy_gold_standard.json"
    with open(fixture_path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.mark.integration
class TestSpacyModelLoading:
    """Test spaCy model loading and caching behavior."""

    def test_model_loads_successfully(self, nlp_model):
        """AC 2.5.2-2: Model should load without errors."""
        assert nlp_model is not None
        assert isinstance(nlp_model, spacy.language.Language)

    def test_model_has_required_components(self, nlp_model):
        """AC 2.5.2-2: Verify model has expected pipeline components."""
        expected_components = ["tok2vec", "tagger", "parser", "ner"]
        for component in expected_components:
            assert component in nlp_model.pipe_names, f"Missing component: {component}"

    def test_model_metadata(self, nlp_model):
        """AC 2.5.2-2: Model version and metadata should be accessible."""
        meta = nlp_model.meta
        assert "version" in meta
        assert meta["lang"] == "en"
        assert "name" in meta

    def test_model_caching_singleton_pattern(self):
        """AC 2.5.2-6: Model should be cached and reused (singleton pattern)."""
        import src.data_extract.utils.nlp as nlp_module

        # First call loads model
        boundaries1 = get_sentence_boundaries("First test.")
        cached_model1 = nlp_module._nlp_model

        # Second call reuses cached model
        boundaries2 = get_sentence_boundaries("Second test.")
        cached_model2 = nlp_module._nlp_model

        assert cached_model1 is cached_model2, "Model should be cached and reused"
        assert len(boundaries1) == 1
        assert len(boundaries2) == 1

    def test_error_handling_missing_model(self):
        """AC 2.5.2-6: Clear error message when model is missing."""
        import src.data_extract.utils.nlp as nlp_module

        original_cache = nlp_module._nlp_model
        nlp_module._nlp_model = None

        try:
            with patch("spacy.load", side_effect=OSError("Model 'en_core_web_md' not found")):
                with pytest.raises(
                    OSError, match="python -m spacy download en_core_web_md"
                ) as exc_info:
                    get_sentence_boundaries("Test text for error handling.")

                # Verify error message is actionable
                error_msg = str(exc_info.value)
                assert "en_core_web_md" in error_msg
                assert "python -m spacy download" in error_msg
        finally:
            nlp_module._nlp_model = original_cache


@pytest.mark.integration
class TestSentenceSegmentationAccuracy:
    """Test sentence segmentation accuracy on gold standard corpus."""

    def test_accuracy_on_gold_standard_corpus(self, nlp_model, gold_standard_corpus):
        """AC 2.5.2-3: Accuracy must be ≥95% on gold standard corpus.

        This is the critical acceptance criterion for Story 2.5.2.
        Tests all 55 test cases with 135 total sentences.
        """
        test_cases = gold_standard_corpus["test_cases"]
        total_cases = len(test_cases)
        correct_cases = 0
        failed_cases = []

        for test_case in test_cases:
            text = test_case["text"]
            expected_boundaries = test_case["expected_boundaries"]

            # Get actual boundaries from our function
            actual_boundaries = get_sentence_boundaries(text, nlp=nlp_model)

            # Compare boundaries
            if actual_boundaries == expected_boundaries:
                correct_cases += 1
            else:
                failed_cases.append(
                    {
                        "id": test_case["id"],
                        "category": test_case["category"],
                        "text": text[:50] + "..." if len(text) > 50 else text,
                        "expected": expected_boundaries,
                        "actual": actual_boundaries,
                        "notes": test_case.get("notes", ""),
                    }
                )

        # Calculate accuracy
        accuracy = (correct_cases / total_cases) * 100

        # Log results for observability (NFR-O4)
        print(f"\n{'='*70}")
        print("Sentence Segmentation Accuracy Test Results")
        print(f"{'='*70}")
        print(f"Total test cases: {total_cases}")
        print(f"Correct: {correct_cases}")
        print(f"Failed: {len(failed_cases)}")
        print(f"Accuracy: {accuracy:.2f}%")
        print("Target: ≥95%")
        print(f"{'='*70}")

        if failed_cases:
            print("\nFailed Cases (showing first 10):")
            for case in failed_cases[:10]:
                print(f"  ID {case['id']} ({case['category']}): {case['text']}")
                print(f"    Expected: {case['expected']}")
                print(f"    Actual:   {case['actual']}")
                print(f"    Notes: {case['notes']}")

        # AC 2.5.2-3: Assert accuracy ≥95%
        assert (
            accuracy >= 95.0
        ), f"Accuracy {accuracy:.2f}% is below required 95% threshold. {len(failed_cases)} cases failed."

    def test_accuracy_by_category(self, nlp_model, gold_standard_corpus):
        """Additional analysis: Accuracy breakdown by category."""
        test_cases = gold_standard_corpus["test_cases"]
        category_stats = {}

        for test_case in test_cases:
            category = test_case["category"]
            if category not in category_stats:
                category_stats[category] = {"total": 0, "correct": 0}

            text = test_case["text"]
            expected = test_case["expected_boundaries"]
            actual = get_sentence_boundaries(text, nlp=nlp_model)

            category_stats[category]["total"] += 1
            if actual == expected:
                category_stats[category]["correct"] += 1

        # Calculate per-category accuracy
        print(f"\n{'='*70}")
        print("Accuracy by Category")
        print(f"{'='*70}")

        categories_below_threshold = []
        for category, stats in sorted(category_stats.items()):
            accuracy = (stats["correct"] / stats["total"]) * 100
            print(f"{category:30s}: {accuracy:5.1f}% ({stats['correct']}/{stats['total']})")

            if accuracy < 90.0:  # Flag categories with low accuracy
                categories_below_threshold.append((category, accuracy))

        if categories_below_threshold:
            print("\nCategories below 90% accuracy:")
            for cat, acc in categories_below_threshold:
                print(f"  - {cat}: {acc:.1f}%")


@pytest.mark.integration
class TestSpacyPerformance:
    """Performance validation tests (NFR-P3, NFR-O4)."""

    def test_model_load_time_under_5_seconds(self):
        """NFR-P3: Model load time must be <5 seconds."""
        # Unload model to test fresh load time
        import src.data_extract.utils.nlp as nlp_module

        original_cache = nlp_module._nlp_model
        nlp_module._nlp_model = None

        try:
            start = time.perf_counter()
            # This should trigger model loading
            get_sentence_boundaries("Test sentence for load timing.")
            elapsed = time.perf_counter() - start

            print(f"\nModel load time: {elapsed:.3f} seconds")
            assert elapsed < 5.0, f"Model load took {elapsed:.3f}s, requirement is <5s"
        finally:
            nlp_module._nlp_model = original_cache

    def test_segmentation_speed_1000_words(self, nlp_model):
        """NFR-P3: Segmentation of 1000-word document performance benchmark.

        Note: NFR-P3 specifies individual file processing <5 seconds total.
        Segmentation is only one component. We benchmark here but allow reasonable
        performance on Windows systems. Target <250ms for 1000 words (4000+ words/sec).
        """
        # Generate ~1000 word test document
        sentence = "This is a test sentence with approximately ten words in total. "
        # 10 words per sentence, 100 sentences = 1000 words
        text = sentence * 100

        start = time.perf_counter()
        boundaries = get_sentence_boundaries(text, nlp=nlp_model)
        elapsed = time.perf_counter() - start

        word_count = len(text.split())
        print("\nSegmentation performance:")
        print(f"  Text length: {len(text)} characters")
        print(f"  Word count: {word_count} words")
        print(f"  Sentences detected: {len(boundaries)}")
        print(f"  Processing time: {elapsed*1000:.2f}ms")
        print(f"  Words/second: {word_count/elapsed:.0f}")

        # Reasonable performance threshold: <250ms for 1000 words (allows OS/hardware variance)
        assert elapsed < 0.25, f"Segmentation took {elapsed*1000:.0f}ms, requirement is <250ms"

        # Verify throughput is adequate (>4000 words/second)
        throughput = word_count / elapsed
        assert throughput > 4000, f"Throughput {throughput:.0f} words/sec below minimum 4000"

    def test_baseline_performance_metrics(self, nlp_model):
        """NFR-O4: Document baseline performance metrics."""
        test_texts = [
            "Short sentence.",
            "Medium length sentence with several words to process.",
            "Long sentence with many words that continues for quite some time "
            "to test the performance characteristics of the segmentation algorithm "
            "when processing longer text inputs that might be more typical in real documents.",
        ]

        print(f"\n{'='*70}")
        print("Baseline Performance Metrics")
        print(f"{'='*70}")

        for i, text in enumerate(test_texts, 1):
            word_count = len(text.split())
            char_count = len(text)

            start = time.perf_counter()
            boundaries = get_sentence_boundaries(text, nlp=nlp_model)
            elapsed = time.perf_counter() - start

            print(f"\nTest {i}:")
            print(f"  Characters: {char_count}")
            print(f"  Words: {word_count}")
            print(f"  Sentences: {len(boundaries)}")
            print(f"  Time: {elapsed*1000:.2f}ms")
            print(f"  Words/sec: {word_count/elapsed:.0f}")


@pytest.mark.integration
class TestSpacyWithRealDocuments:
    """Test spaCy integration with real document samples."""

    def test_segmentation_on_sample_documents(self):
        """AC 2.5.2-6: Test on real document samples from fixtures."""
        # Test with various sample texts
        sample_texts = [
            # Technical documentation
            "The system uses Python 3.12 or higher. Installation requires pip 24.0+. "
            "Follow the README.md instructions carefully.",
            # Business text
            "Q3 revenue was $1.5M. This represents a 15% increase year-over-year. "
            "The CEO announced expansion plans.",
            # Academic text
            "According to Smith et al. (2023), the results were significant. "
            "The p-value was less than 0.05. Further research is needed.",
        ]

        for i, text in enumerate(sample_texts, 1):
            boundaries = get_sentence_boundaries(text)

            # Verify boundaries are reasonable
            assert len(boundaries) > 0, f"Sample {i}: No boundaries detected"
            assert boundaries[-1] == len(text), f"Sample {i}: Last boundary should be text end"

            # Verify all boundaries are within text
            for boundary in boundaries:
                assert 0 < boundary <= len(text), f"Sample {i}: Boundary {boundary} out of range"

            print(f"\nSample {i}: {len(boundaries)} sentences detected")

    def test_empty_and_edge_cases(self):
        """AC 2.5.2-6: Test error handling for edge cases."""
        # Empty text should raise ValueError
        with pytest.raises(ValueError, match="cannot be empty"):
            get_sentence_boundaries("")

        # Whitespace only should raise ValueError
        with pytest.raises(ValueError, match="cannot be empty"):
            get_sentence_boundaries("   \n\t  ")

        # Single character should work
        boundaries = get_sentence_boundaries("A")
        assert len(boundaries) == 1


@pytest.mark.integration
class TestSpacyLogging:
    """Test logging behavior (NFR-O4)."""

    def test_model_load_logging(self, capsys):
        """NFR-O4: Verify model metadata is logged on first load.

        Note: structlog outputs to stdout by default, so we use capsys instead of caplog.
        """
        import src.data_extract.utils.nlp as nlp_module

        original_cache = nlp_module._nlp_model
        nlp_module._nlp_model = None

        try:
            get_sentence_boundaries("Test logging.")

            # Capture stdout where structlog writes
            captured = capsys.readouterr()
            output = captured.out + captured.err

            # Verify model load event was logged with required metadata
            assert (
                "spaCy model loaded" in output or "model_name=en_core_web_md" in output
            ), "Model load should be logged with metadata"

            # Verify key metadata fields are present
            if "model_name=en_core_web_md" in output:
                assert "version=" in output, "Model version should be logged"
                assert "language=" in output, "Language should be logged"
        finally:
            nlp_module._nlp_model = original_cache
