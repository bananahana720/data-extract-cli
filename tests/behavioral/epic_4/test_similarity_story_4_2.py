"""Behavioral test for Story 4.2 similarity analysis - validates AC-4.2-3."""

import numpy as np
import pytest
from sklearn.feature_extraction.text import TfidfVectorizer

from src.data_extract.semantic.models import SemanticResult
from src.data_extract.semantic.similarity import (
    SimilarityAnalysisStage,
    SimilarityConfig,
)

pytestmark = [
    pytest.mark.P1,
    pytest.mark.behavioral,
    pytest.mark.semantic,
    pytest.mark.story_4_2,
]


def test_story_4_2_duplicate_detection_precision():
    """Test that duplicate detection achieves ≥85% precision (AC-4.2-3).

    This test validates the core requirement of Story 4.2: accurate duplicate
    detection with configurable threshold achieving at least 85% precision.
    """
    # Create corpus with known characteristics
    corpus = [
        # Exact duplicates (expect 100% similarity)
        "The quarterly financial audit report indicates strong compliance with all regulatory requirements",
        "The quarterly financial audit report indicates strong compliance with all regulatory requirements",
        # Near duplicates with minor word changes (expect ~0.85-0.95 similarity)
        "Internal risk assessment procedures have identified three critical vulnerabilities requiring immediate remediation",
        "Internal risk assessment processes have identified three critical vulnerabilities needing immediate remediation",
        # Semantically related but distinct (expect ~0.5-0.7 similarity)
        "Cybersecurity audit findings show improved security posture compared to previous quarter",
        "Security assessment results demonstrate enhanced protection measures since last review",
        # Unrelated documents (expect <0.3 similarity)
        "Python programming enables efficient data processing and analysis workflows",
        "Weather patterns indicate increased precipitation expected this weekend",
    ]

    # Create TF-IDF vectors
    vectorizer = TfidfVectorizer(max_features=500)
    tfidf_matrix = vectorizer.fit_transform(corpus)

    # Prepare input
    tfidf_result = SemanticResult(
        tfidf_matrix=tfidf_matrix, chunk_ids=[f"doc_{i}" for i in range(len(corpus))], success=True
    )

    # Configure and run similarity analysis
    stage = SimilarityAnalysisStage(
        config=SimilarityConfig(duplicate_threshold=0.95, related_threshold=0.7, use_cache=False)
    )

    result = stage.process(tfidf_result)

    # Verify processing succeeded
    assert result.success is True, f"Processing failed: {result.error}"

    # Analyze detected duplicates
    duplicates_above_threshold = []
    for id1, id2, sim in result.data["similar_pairs"]:
        if sim >= 0.95:
            duplicates_above_threshold.append((id1, id2, sim))

    # Expected: Only documents 0 and 1 are true duplicates at 0.95 threshold
    # Documents 2 and 3 are near-duplicates but below 0.95 threshold

    # Calculate precision
    # In this test corpus, only docs 0-1 should be detected as duplicates
    # Any other detection would be a false positive
    actual_duplicate_count = len(duplicates_above_threshold)
    true_positives = 0

    for id1, id2, sim in duplicates_above_threshold:
        if (id1 == "doc_0" and id2 == "doc_1") or (id1 == "doc_1" and id2 == "doc_0"):
            true_positives += 1

    precision = (
        true_positives / max(1, actual_duplicate_count) if actual_duplicate_count > 0 else 1.0
    )

    print("\n=== Story 4.2 Duplicate Detection Results ===")
    print("Threshold: 0.95")
    print(f"Detected duplicates: {duplicates_above_threshold}")
    print(f"True positives: {true_positives}")
    print(f"False positives: {actual_duplicate_count - true_positives}")
    print(f"Precision: {precision:.2%}")

    # Verify similarity matrix properties
    matrix = result.data["similarity_matrix"]
    print(f"\nSimilarity matrix shape: {matrix.shape}")
    print(f"Doc 0-1 similarity: {matrix[0, 1]:.4f}")
    print(f"Doc 2-3 similarity: {matrix[2, 3]:.4f}")
    print(f"Doc 4-5 similarity: {matrix[4, 5]:.4f}")
    print(f"Doc 6-7 similarity: {matrix[6, 7]:.4f}")

    # Assert AC-4.2-3: Duplicate detection achieves ≥85% precision
    assert precision >= 0.85, f"Precision {precision:.2%} below 85% requirement (AC-4.2-3)"

    # Verify other key properties
    # 1. Matrix is symmetric (AC-4.2-6)
    np.testing.assert_array_almost_equal(
        matrix, matrix.T, decimal=10, err_msg="Matrix not symmetric (AC-4.2-6)"
    )

    # 2. Diagonal is all 1.0 (self-similarity)
    np.testing.assert_array_almost_equal(
        np.diag(matrix), np.ones(len(corpus)), err_msg="Diagonal should be 1.0"
    )

    # 3. Statistics are present (AC-4.2-8)
    stats = result.data["similarity_statistics"]
    assert "mean" in stats
    assert "std" in stats
    assert "max" in stats
    assert stats["n_samples"] == len(corpus)

    print(f"\n=== Test PASSED: Precision {precision:.2%} >= 85% ===")


def test_story_4_2_performance_requirements():
    """Test performance meets NFR requirements for Story 4.2 (AC-4.2-7).

    Performance requirements:
    - <200ms for 100x100 matrix
    - <5s for 1000x1000 matrix (not tested here due to time)
    - <500MB memory usage
    """
    import time

    # Create 100 document corpus
    corpus = []
    for i in range(100):
        # Create varied documents to avoid all being identical
        base_text = f"Document number {i} contains important business information"
        if i % 10 == 0:
            text = base_text + " about financial audits and compliance"
        elif i % 10 == 1:
            text = base_text + " regarding cybersecurity and risk management"
        else:
            text = base_text + f" with unique identifier {i * 17}"
        corpus.append(text)

    # Create TF-IDF vectors
    vectorizer = TfidfVectorizer(max_features=500)
    tfidf_matrix = vectorizer.fit_transform(corpus)

    tfidf_result = SemanticResult(
        tfidf_matrix=tfidf_matrix, chunk_ids=[f"doc_{i}" for i in range(100)], success=True
    )

    # Process with timing
    stage = SimilarityAnalysisStage(config=SimilarityConfig(use_cache=False))

    start_time = time.time()
    result = stage.process(tfidf_result)
    elapsed_ms = (time.time() - start_time) * 1000

    print("\n=== Story 4.2 Performance Test ===")
    print("Matrix size: 100x100")
    print(f"Processing time: {elapsed_ms:.1f}ms")
    print("Requirement: <200ms")

    # Verify success and performance
    assert result.success is True
    assert elapsed_ms < 200, f"Performance {elapsed_ms:.1f}ms exceeds 200ms limit (AC-4.2-7)"

    # Verify matrix dimensions
    matrix = result.data["similarity_matrix"]
    assert matrix.shape == (100, 100), f"Matrix shape {matrix.shape} != (100, 100)"

    print(f"=== Test PASSED: {elapsed_ms:.1f}ms < 200ms ===")


if __name__ == "__main__":
    # Run tests directly
    test_story_4_2_duplicate_detection_precision()
    test_story_4_2_performance_requirements()
    print("\n=== All Story 4.2 tests PASSED ===")
